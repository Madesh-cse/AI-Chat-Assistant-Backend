from app.services.llm import llm_with_tools

from langchain_core.messages import (HumanMessage) # type: ignore

from .state import ChatState


def llm_node(state: ChatState) -> dict:

    print("\n==============================")
    print("LLM NODE")
    print("==============================")

    message = state.get("message", "")

    print("USER:", message)

    # GET EXISTING MESSAGES

    messages = state.get("messages", [])

    # FIRST LLM CALL

    if not messages:

        messages = [
            HumanMessage(
                content=message
            )
        ]

    # CALL LLM

    response = llm_with_tools.invoke(
        messages
    )

    print("\nAI RESPONSE:")
    print(response.content)

    print("\nTOOL CALLS:")
    print(response.tool_calls)

    # RETURN UPDATED STATE

    return {

        "message": message,
        "response": response.content,
        "messages": [
            *messages,
            response,
        ],
    }