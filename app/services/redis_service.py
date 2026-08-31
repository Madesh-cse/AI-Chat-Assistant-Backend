import json

from app.core.redis import redis_client


def get_history(conversation_id: str):
    key = f"chat:{conversation_id}:messages"

    messages = redis_client.lrange(key, 0, -1)

    return [json.loads(message) for message in messages]


def add_message(
    conversation_id: str,
    role: str,
    content: str,
):
    key = f"chat:{conversation_id}:messages"

    message = {
        "role": role,
        "content": content,
    }

    redis_client.rpush(
        key,
        json.dumps(message),
    )


def clear_history(conversation_id: str):
    key = f"chat:{conversation_id}:messages"

    redis_client.delete(key)