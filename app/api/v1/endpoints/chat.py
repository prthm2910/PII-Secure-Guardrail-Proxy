import time
import uuid
import httpx
import copy
from datetime import datetime
from groq import AsyncGroq
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse, SanitizeRequest, SanitizeResponse
from app.services.sanitization_service import sanitization_service
from app.services.audit_service import audit_service
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

# Initialize AsyncGroq client
groq_client = AsyncGroq(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_API_BASE_URL,
)

@router.post("/sanitize", response_model=SanitizeResponse)
async def sanitize_content(payload: SanitizeRequest):
    """
    Eagerly sanitize content and store tokens in Redis.
    Used for Block 2 (Sanitized Raw Input) in the Quad UI.
    """
    request_id = str(uuid.uuid4())
    logger.info(f"Req: {request_id} | Eager sanitization request")
    
    sanitized_text, _, _, _, masked_entities = sanitization_service.sanitize(
        payload.content, 
        request_id=request_id
    )
    
    return SanitizeResponse(
        sanitized_content=sanitized_text,
        request_id=request_id,
        masked_entities=masked_entities
    )

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def proxy_chat_completions(
    payload: ChatCompletionRequest, 
    background_tasks: BackgroundTasks,
    request: Request
):
    # 0. Initial Request Context
    request_id = payload.request_id or str(uuid.uuid4())
    skip_pii = request.headers.get("X-PII-Skip", "false").lower() == "true"
    start_time = time.time()
    
    timeline = []
    def add_event(msg: str):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        timeline.append(f"{ts}: {msg}")

    add_event(f"Received proxy request. Protection Active: {not skip_pii}")
    if payload.request_id:
        add_event(f"Reusing existing session: {payload.request_id}")
    
    logger.info(f"Req: {request_id} | Incoming chat request (Provider: {settings.LLM_PROVIDER}). Skip PII: {skip_pii}")
    
    # 1. Extract and Sanitize User Content
    all_entity_summaries = {}
    all_masked_entities = {}
    
    sanitized_messages = []
    for i, msg in enumerate(payload.messages):
        msg_dict = msg.model_dump()
        if msg.role == "user" and not skip_pii:
            add_event(f"Analyzing user message {i} for PII...")
            logger.debug(f"Req: {request_id} | Sanitizing user message at index {i}")
            sanitized_content, _, _, entity_summary, masked_entities = sanitization_service.sanitize(msg.content, request_id=request_id)
            
            if entity_summary:
                count = sum(entity_summary.values())
                add_event(f"Detected {count} PII entities. Generating synthetic tokens...")
                add_event(f"Tokens stored in Redis with 1h TTL.")
            else:
                add_event("No PII detected in this message.")

            msg_dict["content"] = sanitized_content
            for k, v in entity_summary.items():
                all_entity_summaries[k] = all_entity_summaries.get(k, 0) + v
            all_masked_entities.update(masked_entities)
            
            if entity_summary:
                logger.info(f"Req: {request_id} | Detected {sum(entity_summary.values())} PII entities in message {i}")
        sanitized_messages.append(msg_dict)

    # 2. Forward to LLM via Groq SDK
    try:
        msg_summary = [{"role": m["role"], "len": len(m["content"])} for m in sanitized_messages]
        logger.info(f"Req: {request_id} | Forwarding to Groq | Payload: {msg_summary}")
        add_event(f"Forwarding sanitized payload to {settings.LLM_MODEL}...")
        
        # Prepare parameters for the Groq call
        params = payload.model_dump(exclude_none=True)
        params.pop("request_id", None) # Remove custom field before SDK call
        params["messages"] = sanitized_messages
        
        # Ensure model is set
        if not params.get("model"):
            params["model"] = settings.LLM_MODEL

        # Call Groq
        chat_completion = await groq_client.chat.completions.create(**params)
        add_event(f"Upstream response received.")
        
        # Convert to dict for response processing
        llm_response = chat_completion.model_dump()
        logger.debug(f"Req: {request_id} | Received response from Groq")
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Req: {request_id} | Upstream failure: {str(e)}")
        add_event(f"CRITICAL: Upstream LLM failed: {str(e)}")
        
        # Log failure metadata
        background_tasks.add_task(
            audit_service.log_request,
            request_id=request_id,
            entity_summary=all_entity_summaries,
            masked_entities=all_masked_entities,
            sanitized_messages=sanitized_messages,
            technical_timeline=timeline,
            latency_ms=latency_ms,
            status=f"UPSTREAM_ERROR"
        )
        raise HTTPException(status_code=500, detail="Upstream LLM provider error")

    # 3. Desanitize the LLM Response (only if not skipped)
    # We create a deep copy of choices for the redacted view
    redacted_choices = copy.deepcopy(llm_response.get("choices", []))
    
    if not skip_pii:
        logger.debug(f"Req: {request_id} | Desanitizing LLM response choices")
        add_event("Scanning response for tokens...")
        found_tokens = False
        for choice in llm_response.get("choices", []):
            message = choice.get("message", {})
            if message.get("role") == "assistant" and "content" in message:
                if message["content"]:
                    original_content = message["content"]
                    message["content"] = sanitization_service.desanitize(message["content"], request_id)
                    if original_content != message["content"]:
                        found_tokens = True

        if found_tokens:
            add_event("Found tokens in response. Rehydrating from Redis cache...")
        else:
            add_event("No tokens found in response. No rehydration needed.")

    # 4. Final Audit and Response
    latency_ms = (time.time() - start_time) * 1000
    status = "BYPASSED" if skip_pii else "SUCCESS"
    add_event(f"Request complete. Total Latency: {latency_ms:.2f}ms")
    logger.info(f"Req: {request_id} | Request complete. Status: {status} | Latency: {latency_ms:.2f}ms")
    
    background_tasks.add_task(
        audit_service.log_request,
        request_id=request_id,
        entity_summary=all_entity_summaries,
        masked_entities=all_masked_entities,
        sanitized_messages=sanitized_messages,
        technical_timeline=timeline,
        latency_ms=latency_ms,
        status=status
    )

    # Prepare response
    final_response = {
        "id": llm_response.get("id", f"proxy-{request_id}"),
        "choices": llm_response.get("choices", []),
        "redacted_choices": redacted_choices,
        "proxy_request_id": request_id
    }

    return final_response
