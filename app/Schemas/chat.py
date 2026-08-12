from pydantic import BaseModel  # type: ignore
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    conversation_id : Optional[int] = None
    
class ChatResponse(BaseModel):
    response: str