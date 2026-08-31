from pydantic import BaseModel  # type: ignore
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    conversation_id : Optional[int] = None
    stack_overflow_enabled: bool = False
    notion_enabled: bool = False
    language: str = "English"
    
class ChatResponse(BaseModel):
    response: str