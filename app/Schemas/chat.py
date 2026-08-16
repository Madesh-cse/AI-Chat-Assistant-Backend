from pydantic import BaseModel  # type: ignore
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    conversation_id : Optional[int] = None
    stack_overflow_enabled: bool = False
    
class ChatResponse(BaseModel):
    response: str