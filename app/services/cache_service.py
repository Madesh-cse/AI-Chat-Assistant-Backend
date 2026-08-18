import json
import hashlib

from app.core.redis import redis_client


CACHE_TTL = 60 * 60  # 1 hour


def generate_cache_key(
    user_id: int,
    message: str,
) -> str:

    normalized_message = message.strip().lower()

    message_hash = hashlib.sha256(
        normalized_message.encode("utf-8")
    ).hexdigest()

    return f"chat:{user_id}:{message_hash}"


def get_cached_response(
    user_id: int,
    message: str,
):

    key = generate_cache_key(
        user_id,
        message,
    )

    cached = redis_client.get(key)

    if not cached:
        return None

    try:
        return json.loads(cached)
    except json.JSONDecodeError:
        return cached


def set_cached_response(
    user_id: int,
    message: str,
    response,
):

    key = generate_cache_key(
        user_id,
        message,
    )

    if isinstance(response, str):
        value = response
    else:
        value = json.dumps(response)

    redis_client.setex(
        key,
        CACHE_TTL,
        value,
    )


def delete_cached_response(
    user_id: int,
    message: str,
):

    key = generate_cache_key(
        user_id,
        message,
    )

    redis_client.delete(key)