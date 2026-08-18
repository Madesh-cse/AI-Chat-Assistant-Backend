from pydantic import BaseModel # type: ignore


class AppConnectionResponse(BaseModel):
    id: int
    app_id: str
    connected: bool

    class Config:
        from_attributes = True