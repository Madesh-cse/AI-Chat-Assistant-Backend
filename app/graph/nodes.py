import time

from app.services.llm import llm_with_tools

from .state import ChatState


def llm_node(state: ChatState) -> dict:

    node_start = time.perf_counter()

    print("\n==============================")
    print("LLM NODE")
    print("==============================")

    messages = state.get("messages", [])

    print("\nMESSAGE COUNT:", len(messages))

    # PRINT INPUT MESSAGES

    for index, message in enumerate(messages, start=1):

        print(
            f"{index}. "
            f"{message.__class__.__name__}: "
            f"{message.content}"
        )
    # LLM INVOKE

    print("\n==============================")
    print("CALLING OLLAMA")
    print("==============================")

    llm_start = time.perf_counter()

    response = llm_with_tools.invoke(
        messages
    )

    llm_time = (
        time.perf_counter()
        - llm_start
    )

    print(
        f"\n⏱️ LLM INVOKE TIME: "
        f"{llm_time:.2f}s"
    )
    # RESPONSE

    print("\n==============================")
    print("AI RESPONSE")
    print("==============================")

    print(response.content)
    # TOOL CALLS

    print("\n==============================")
    print("TOOL CALLS")
    print("==============================")

    print(response.tool_calls)

    # TOTAL NODE TIME

    total_time = (
        time.perf_counter()
        - node_start
    )

    print(
        f"\n⏱️ TOTAL LLM NODE TIME: "
        f"{total_time:.2f}s"
    )

    # UPDATE STATE

    return {
        "response": response.content,

        "messages": [
            *messages,
            response,
        ],
    }