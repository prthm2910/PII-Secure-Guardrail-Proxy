from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict

class Message(BaseModel):
    role: str
    content: str

class SanitizeRequest(BaseModel):
    content: str

class SanitizeResponse(BaseModel):
    sanitized_content: str
    request_id: str
    masked_entities: Dict[str, str]

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[dict] = None
    
    model_config = ConfigDict(extra="allow")

class Choice(BaseModel):
    message: Message
    finish_reason: Optional[str] = None
    index: int

class ChatCompletionResponse(BaseModel):
    id: str
    choices: List[Choice]
    redacted_choices: Optional[List[Choice]] = None
    proxy_request_id: str
    
    model_config = ConfigDict(extra="allow")
