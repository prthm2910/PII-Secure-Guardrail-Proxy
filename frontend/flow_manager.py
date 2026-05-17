import httpx
from enum import Enum
from typing import Optional, Dict, Any
import os
import streamlit as st

class FlowStatus(Enum):
    IDLE = "idle"
    SANITIZING = "sanitizing"
    SANITIZED = "sanitized"
    CHATTING = "chatting"
    COMPLETED = "completed"
    ERROR = "error"

@st.cache_resource
def get_client():
    return httpx.Client(timeout=70.0)

class FlowManager:
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000/proxy/v1")
        self.llm_model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.client = get_client()
        
        if "current_query" not in st.session_state:
            self.reset_state()

    def reset_state(self):
        st.session_state.current_query = {
            "raw": "",
            "sanitized": "",
            "redacted": "",
            "desanitized": "",
            "request_id": None,
            "status": FlowStatus.IDLE.value,
            "error_message": None
        }

    def run_sanitize(self, text: str):
        """Step 1: Eagerly sanitize the input."""
        st.session_state.current_query["raw"] = text
        st.session_state.current_query["status"] = FlowStatus.SANITIZING.value
        
        try:
            response = self.client.post(f"{self.base_url}/sanitize", json={"content": text})
            if response.status_code == 200:
                data = response.json()
                st.session_state.current_query["sanitized"] = data["sanitized_content"]
                st.session_state.current_query["request_id"] = data["request_id"]
                st.session_state.current_query["status"] = FlowStatus.SANITIZED.value
            else:
                self._handle_error(f"Sanitize failed: {response.text}")
        except Exception as e:
            self._handle_error(f"Sanitize connection error: {e}")

    def run_chat(self):
        """Step 2: Get LLM completion using the existing request_id."""
        query = st.session_state.current_query
        if not query["request_id"]:
            return

        st.session_state.current_query["status"] = FlowStatus.CHATTING.value
        
        payload = {
            "messages": [{"role": "user", "content": query["raw"]}],
            "request_id": query["request_id"],
            "model": self.llm_model
        }
        
        try:
            response = self.client.post(f"{self.base_url}/chat/completions", json=payload)
            if response.status_code == 200:
                data = response.json()
                st.session_state.current_query["redacted"] = data["redacted_choices"][0]["message"]["content"]
                st.session_state.current_query["desanitized"] = data["choices"][0]["message"]["content"]
                st.session_state.current_query["status"] = FlowStatus.COMPLETED.value
            else:
                self._handle_error(f"LLM failed: {response.text}")
        except Exception as e:
            self._handle_error(f"LLM connection error: {e}")

    def _handle_error(self, message: str):
        st.session_state.current_query["status"] = FlowStatus.ERROR.value
        st.session_state.current_query["error_message"] = message
