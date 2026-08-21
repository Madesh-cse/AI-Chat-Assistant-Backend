import json

from langchain_core.messages import ( # type: ignore
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)

from app.core.redis import get_redis


HISTORY_CACHE_TTL = 60 * 60  # 1 hour


# ==================================================
# CREATE HISTORY CACHE KEY
# ==================================================

def create_history_cache_key(
    conversation_id: int,
) -> str:

    return f"chat:history:{conversation_id}"


# ==================================================
# SERIALIZE LANGCHAIN MESSAGE
# ==================================================

def serialize_message(message) -> dict:

    if isinstance(message, HumanMessage):

        return {
            "type": "human",
            "content": message.content,
        }

    if isinstance(message, AIMessage):

        return {
            "type": "ai",
            "content": message.content,
            "tool_calls": getattr(
                message,
                "tool_calls",
                [],
            ),
        }

    if isinstance(message, ToolMessage):

        return {
            "type": "tool",
            "content": message.content,
            "tool_call_id": getattr(
                message,
                "tool_call_id",
                None,
            ),
        }

    if isinstance(message, SystemMessage):

        return {
            "type": "system",
            "content": message.content,
        }

    return {
        "type": "unknown",
        "content": str(
            getattr(
                message,
                "content",
                message,
            )
        ),
    }


# ==================================================
# DESERIALIZE MESSAGE
# ==================================================

def deserialize_message(
    data: dict,
):

    message_type = data.get(
        "type"
    )

    content = data.get(
        "content",
        "",
    )

    # --------------------------------------------------
    # HUMAN
    # --------------------------------------------------

    if message_type == "human":

        return HumanMessage(
            content=content,
        )

    # --------------------------------------------------
    # AI
    # --------------------------------------------------

    if message_type == "ai":

        tool_calls = data.get(
            "tool_calls",
            [],
        )

        if tool_calls:

            return AIMessage(
                content=content,
                tool_calls=tool_calls,
            )

        return AIMessage(
            content=content,
        )

    # --------------------------------------------------
    # TOOL
    # --------------------------------------------------

    if message_type == "tool":

        tool_call_id = data.get(
            "tool_call_id"
        )

        if not tool_call_id:

            return None

        return ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
        )

    # --------------------------------------------------
    # SYSTEM
    # --------------------------------------------------

    if message_type == "system":

        return SystemMessage(
            content=content,
        )

    return None


# ==================================================
# GET HISTORY
# ==================================================

def get_cached_history(
    conversation_id: int,
):

    redis_client = get_redis()

    key = create_history_cache_key(
        conversation_id
    )

    print("\n==============================")
    print("REDIS HISTORY GET")
    print("==============================")

    print(
        "Conversation ID:",
        conversation_id,
    )

    print(
        "History Cache Key:",
        key,
    )

    value = redis_client.get(
        key
    )

    if value is None:

        print(
            "🔴 REDIS HISTORY CACHE MISS"
        )

        return None

    print(
        "🟢 REDIS HISTORY CACHE HIT"
    )

    try:

        data = json.loads(
            value
        )

        if not isinstance(
            data,
            list,
        ):

            print(
                "⚠️ Invalid history format"
            )

            return None

        messages = []

        for item in data:

            if not isinstance(
                item,
                dict,
            ):

                print(
                    "⚠️ Invalid history item:",
                    item,
                )

                continue

            message = deserialize_message(
                item
            )

            if message is not None:

                messages.append(
                    message
                )

        print(
            "Cached message count:",
            len(messages),
        )

        return messages

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as e:

        print(
            "⚠️ Failed to decode Redis history:",
            e,
        )

        return None


# ==================================================
# SET HISTORY
# ==================================================

def set_cached_history(
    conversation_id: int,
    messages: list,
):

    redis_client = get_redis()

    key = create_history_cache_key(
        conversation_id
    )

    serialized_messages = []

    for message in messages:

        serialized_messages.append(
            serialize_message(
                message
            )
        )

    redis_client.setex(
        key,
        HISTORY_CACHE_TTL,
        json.dumps(
            serialized_messages
        ),
    )

    print("\n==============================")
    print("REDIS HISTORY SET")
    print("==============================")

    print(
        "Conversation ID:",
        conversation_id,
    )

    print(
        "History Cache Key:",
        key,
    )

    print(
        "Message count:",
        len(messages),
    )

    print(
        "TTL:",
        HISTORY_CACHE_TTL,
    )

    print(
        "🟢 CONVERSATION HISTORY CACHED"
    )


# ==================================================
# INVALIDATE HISTORY
# ==================================================

def invalidate_history_cache(
    conversation_id: int,
):

    redis_client = get_redis()

    key = create_history_cache_key(
        conversation_id
    )

    deleted = redis_client.delete(
        key
    )

    if deleted:

        print(
            f"🟢 HISTORY CACHE DELETED: {key}"
        )

    else:

        print(
            f"⚠️ HISTORY CACHE NOT FOUND: {key}"
        )
        

# append a cached histroy
def append_to_cached_history(
    conversation_id: int,
    messages: list,
):
    """
    Append new LangChain messages to existing Redis history.
    """

    redis_client = get_redis()

    key = create_history_cache_key(
        conversation_id
    )

    cached_history = get_cached_history(
        conversation_id
    )

    if cached_history is None:

        # No Redis history yet.
        # Store the complete history.
        set_cached_history(
            conversation_id=conversation_id,
            messages=messages,
        )

        return

    cached_history.extend(
        messages
    )

    set_cached_history(
        conversation_id=conversation_id,
        messages=cached_history,
    )

    print(
        "🟢 REDIS HISTORY UPDATED"
    )