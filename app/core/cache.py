import hashlib
import json

from app.core.redis import get_redis


CACHE_TTL = 60 * 60


# ==================================================
# CREATE CACHE KEY
# ==================================================

def create_cache_key(
    user_id: int,
    conversation_id: int,
    message: str,
) -> str:

    normalized_message = (
        message.strip().lower()
    )

    raw_key = (
        f"{user_id}:"
        f"{conversation_id}:"
        f"{normalized_message}"
    )

    hashed_key = hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()

    return (
        f"chat:response:{hashed_key}"
    )


# ==================================================
# GET CACHE
# ==================================================

def get_cached_response(
    user_id: int,
    conversation_id: int,
    message: str,
):

    redis_client = get_redis()

    key = create_cache_key(
        user_id=user_id,
        conversation_id=conversation_id,
        message=message,
    )

    print("\n==============================")
    print("REDIS CACHE GET")
    print("==============================")

    print("User ID:", user_id)
    print("Conversation ID:", conversation_id)
    print("Message:", repr(message))
    print("Cache Key:", key)

    value = redis_client.get(key)

    if value is None:

        print("🔴 REDIS CACHE MISS")

        return None

    print("🟢 REDIS CACHE HIT")

    try:

        return json.loads(value)

    except json.JSONDecodeError:

        print(
            "⚠️ Invalid JSON in Redis"
        )

        return None


# ==================================================
# SET CACHE
# ==================================================

def set_cached_response(
    user_id: int,
    conversation_id: int,
    message: str,
    response: str,
):

    redis_client = get_redis()

    key = create_cache_key(
        user_id=user_id,
        conversation_id=conversation_id,
        message=message,
    )

    data = {
        "response": response,
    }

    print("\n==============================")
    print("REDIS CACHE SET")
    print("==============================")

    print("User ID:", user_id)
    print("Conversation ID:", conversation_id)
    print("Message:", repr(message))
    print("Cache Key:", key)
    print("TTL:", CACHE_TTL)

    redis_client.setex(
        key,
        CACHE_TTL,
        json.dumps(data),
    )

    print(
        "🟢 RESPONSE CACHED"
    )