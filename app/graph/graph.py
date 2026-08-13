from langgraph.graph import StateGraph, START, END  # type: ignore

from .state import ChatState
from .nodes import llm_node
from .tool_node import tool_node
from .router import should_continue


builder = StateGraph(ChatState)

# NODES

builder.add_node("llm", llm_node)
builder.add_node("tools", tool_node)

# START
builder.add_edge(START, "llm")

# CONDITIONAL ROUTING
builder.add_conditional_edges("llm", should_continue,{
    "tools": "tools",
    "end": END,
})

# TOOL → LLM
builder.add_edge(
    "tools",
    "llm"
)

chat_graph = builder.compile()