from datetime import datetime

from pydantic import BaseModel, ConfigDict # type: ignore


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )