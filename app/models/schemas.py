from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")
