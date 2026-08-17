
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage  # type: ignore
from langgraph.graph.message import add_messages  # type: ignore


class ChatState(TypedDict):
    message: str
    messages: Annotated[list[BaseMessage], add_messages]
    response: str