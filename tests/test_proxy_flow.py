import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app
import json

client = TestClient(app)

@pytest.fixture
def mock_redis():
    # Patch the reference inside the sanitization_service module
    with patch("app.services.sanitization_service.redis_service") as mock:
        # Simulate in-memory storage for the test
        storage = {}
        def store(req_id, tokens): 
            storage[req_id] = tokens
        def get(req_id): 
            return storage.get(req_id)
        
        mock.store_tokens.side_effect = store
        mock.get_tokens.side_effect = get
        yield mock

@pytest.fixture
def mock_groq_response():
    with patch("app.api.v1.endpoints.chat.groq_client.chat.completions.create", new_callable=AsyncMock) as mock:
        # Create a mock response object
        mock_completion = MagicMock()
        
        # Define the structure for model_dump()
        mock_completion.model_dump.return_value = {
            "id": "groq-123",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "I see you provided a PAN. Your token is [IN_PAN_1]. Processing your request..."
                    },
                    "finish_reason": "stop"
                }
            ]
        }
        
        mock.return_value = mock_completion
        yield mock

def test_quad_block_flow(mock_redis, mock_groq_response):
    """
    Test the full Quad Block lifecycle:
    1. Call /sanitize (Eager step).
    2. Use the request_id from (1) to call /chat/completions.
    3. Verify redacted_choices and choices in the response.
    """
    original_pii = "BKXPS1234Z"
    
    # Step 1: Eager Sanitize
    san_response = client.post("/proxy/v1/sanitize", json={"content": f"My PAN is {original_pii}"})
    assert san_response.status_code == 200
    san_data = san_response.json()
    request_id = san_data["request_id"]
    assert "[IN_PAN_1]" in san_data["sanitized_content"]
    
    # Step 2: Chat Completion with request_id
    payload = {
        "messages": [
            {"role": "user", "content": f"My PAN is {original_pii}"}
        ],
        "request_id": request_id,
        "model": "llama-3.3-70b-versatile"
    }
    
    chat_response = client.post("/proxy/v1/chat/completions", json=payload)
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    
    # Verify both versions exist
    assert chat_data["proxy_request_id"] == request_id
    # Final version should be desanitized
    assert original_pii in chat_data["choices"][0]["message"]["content"]
    # Redacted version should have the token
    assert "[IN_PAN_1]" in chat_data["redacted_choices"][0]["message"]["content"]
    assert original_pii not in chat_data["redacted_choices"][0]["message"]["content"]
