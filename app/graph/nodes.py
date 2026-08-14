from app.services.llm import llm_with_tools

from .state import ChatState


def llm_node(state: ChatState) -> dict:

    print("\n==============================")
    print("LLM NODE")
    print("==============================")

    messages = state.get("messages", [])

    print("\nMESSAGE COUNT:", len(messages))

    # CALL LLM

    response = llm_with_tools.invoke(
        messages
    )

    print("\nAI RESPONSE:")
    print(response.content)
    print("\nTOOL CALLS:")
    print(response.tool_calls)

    # UPDATE MESSAGE HISTORY

    return {
        "response": response.content,
        "messages": [
            *messages,
            response,
        ],
    }