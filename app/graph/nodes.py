from app.services.llm import llm_with_tools

from .state import ChatState


def llm_node(state: ChatState) -> dict:

    print("\n==============================")
    print("LLM NODE")
    print("==============================")

    message = state["message"]

    print("USER:", message)

    messages = state["messages"]

    response = llm_with_tools.invoke(messages)

    print("\nAI RESPONSE:")
    print(response.content)

    print("\nTOOL CALLS:")
    print(response.tool_calls)

    return {
        "messages": [response],
        "response": response.content,
    }