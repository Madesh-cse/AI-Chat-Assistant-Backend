from typing import TypedDict
from langchain_core.messages import BaseMessage # type: ignore


class ChatState(TypedDict):
    message: str
    messages: list[BaseMessage]
    response: str