import time
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from app.core.config import settings
from app.services.sanitization_service import sanitization_service
from app.services.audit_service import audit_service
from app.models.schemas import ChatCompletionRequest
import httpx

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    description="A centralized Data Loss Prevention API Gateway for LLM sanitization."
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "0.1.0"
    }

@app.post("/proxy/v1/chat/completions")
async def proxy_chat_completions(payload: ChatCompletionRequest, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    # 1. Extract and Sanitize User Content
    request_id = None
    all_entity_summaries = {}
    all_masked_entities = {}
    
    for msg in payload.messages:
        if msg.role == "user":
            original_content = msg.content
            sanitized_content, req_id, _, entity_summary, masked_entities = sanitization_service.sanitize(original_content)
            msg.content = sanitized_content
            request_id = request_id or req_id
            for k, v in entity_summary.items():
                all_entity_summaries[k] = all_entity_summaries.get(k, 0) + v
            all_masked_entities.update(masked_entities)

    # 2. Forward to LLM (Simulated)
    llm_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": f"I received your request. The PII you mentioned has been tokenized. One of the tokens is {list(all_masked_entities.keys())[0] if all_masked_entities else 'NONE'}."
                }
            }
        ]
    }
    
    # 3. Desanitize the LLM Response
    for choice in llm_response.get("choices", []):
        msg = choice.get("message", {})
        if msg.get("role") == "assistant":
            msg["content"] = sanitization_service.desanitize(msg["content"], request_id)

    # 4. Async Audit Logging
    latency_ms = (time.time() - start_time) * 1000
    background_tasks.add_task(
        audit_service.log_request,
        request_id=request_id,
        entity_summary=all_entity_summaries,
        masked_entities=all_masked_entities,
        latency_ms=latency_ms,
        status="SUCCESS"
    )

    return llm_response
