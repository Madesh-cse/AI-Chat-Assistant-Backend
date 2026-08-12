from datetime import datetime

from pydantic import BaseModel, Field  # type: ignore


# CREATE

class ConversationCreate(BaseModel):

    title: str = "New Chat"


# MESSAGE RESPONSE

class MessageResponse(BaseModel):

    id: int

    role: str

    content: str

    created_at: datetime

    class Config:
        from_attributes = True


# CONVERSATION RESPONSE

class ConversationResponse(BaseModel):

    id: int

    title: str

    user_id: int

    created_at: datetime

    updated_at: datetime

    messages: list[MessageResponse] = Field(
        default_factory=list
    )

    class Config:
        from_attributes = True