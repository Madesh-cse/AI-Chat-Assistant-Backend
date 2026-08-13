from .state import ChatState


def should_continue(state: ChatState):

    messages = state["messages"]

    last_message = messages[-1]

    if last_message.tool_calls:
        return "tools"

    return "end"