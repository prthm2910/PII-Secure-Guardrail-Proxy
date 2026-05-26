import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_sanitize_endpoint():
    """Verify that /sanitize returns tokens and a request_id."""
    # Use the verified valid PAN BKXPS1234Z
    payload = {
        "content": "My PAN is BKXPS1234Z"
    }
    
    # Mock redis to avoid dependency
    with patch("app.services.sanitization_service.redis_service.store_tokens") as mock_store:
        response = client.post("/proxy/v1/sanitize", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "[IN_PAN_1]" in data["sanitized_content"]
        assert "request_id" in data
        assert "[IN_PAN_1]" in data["masked_entities"]
        assert mock_store.called

def test_sanitize_no_pii():
    """Verify behavior when no PII is present."""
    payload = {
        "content": "Hello world"
    }
    
    response = client.post("/proxy/v1/sanitize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sanitized_content"] == "Hello world"
    assert data["masked_entities"] == {}
