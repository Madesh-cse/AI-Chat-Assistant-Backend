import time

from langchain_core.messages import ToolMessage  # type: ignore

from app.tools.weather import get_weather
from app.tools.city_image import get_city_image
from app.tools.news import get_news
from app.tools.wikipedia import search_wikipedia
from app.tools.web_search import web_search
from app.tools.movie import get_movie

from .state import ChatState


# AVAILABLE TOOLS

TOOLS = {
    "get_weather": get_weather,
    "get_city_image": get_city_image,
    "get_news": get_news,
    "search_wikipedia": search_wikipedia,
    "web_search": web_search,
    "get_movie": get_movie,
}

# TOOL NODE

def tool_node(state: ChatState) -> dict:

    print("\n==============================")
    print("TOOL NODE")
    print("==============================")

    messages = state["messages"]

    # GET LAST AI MESSAGE

    last_message = messages[-1]

    tool_calls = last_message.tool_calls

    print(
        f"Number of tool calls: {len(tool_calls)}"
    )

    tool_messages = []

    # EXECUTE EACH TOOL
    for tool_call in tool_calls:

        tool_name = tool_call["name"]

        tool_args = tool_call.get(
            "args",
            {},
        )

        tool_call_id = tool_call["id"]

        print("\n------------------------------")
        print("TOOL EXECUTION")
        print("------------------------------")

        print("Tool:", tool_name)
        print("Arguments:", tool_args)
        print("Tool Call ID:", tool_call_id)

        # FIND TOOL

        tool = TOOLS.get(tool_name)

        if not tool:

            print(
                f"❌ Tool '{tool_name}' not found"
            )

            result = (
                f"Tool '{tool_name}' "
                "is not available."
            )

            tool_messages.append(
                ToolMessage(
                    content=result,
                    tool_call_id=tool_call_id,
                )
            )

            continue

        # EXECUTE TOOL
        start_time = time.perf_counter()

        try:

            result = tool.invoke(
                tool_args
            )

            execution_time = (
                time.perf_counter()
                - start_time
            )

            print("\nTOOL RESULT:")
            print(result)

            print(
                f"\n⏱️ TOOL TIME: "
                f"{execution_time:.2f}s"
            )

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id,
                )
            )

        except Exception as e:

            execution_time = (
                time.perf_counter()
                - start_time
            )

            print("\n❌ TOOL ERROR:")
            print(str(e))

            print(
                f"\n⏱️ FAILED TOOL TIME: "
                f"{execution_time:.2f}s"
            )

            error_message = (
                f"Tool '{tool_name}' "
                f"failed: {str(e)}"
            )

            tool_messages.append(
                ToolMessage(
                    content=error_message,
                    tool_call_id=tool_call_id,
                )
            )

    # RETURN TOOL MESSAGES

    print("\n==============================")
    print("TOOL NODE COMPLETE")
    print("==============================")

    print(
        f"Generated {len(tool_messages)} "
        f"tool message(s)"
    )

    return {
        "messages": tool_messages,
    }