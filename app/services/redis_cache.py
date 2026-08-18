import json
from typing import Any

from app.db.redis import redis_client


DEFAULT_TTL = 300  # 5 minutes


def get_cache(key: str) -> Any | None:
    try:
        value = redis_client.get(key)

        if value is None:
            return None

        return json.loads(value)

    except Exception as e:
        print(f"Redis GET error: {e}")

        return None


def set_cache(
    key: str,
    value: Any,
    ttl: int = DEFAULT_TTL,
) -> bool:

    try:
        redis_client.setex(
            key,
            ttl,
            json.dumps(value),
        )

        return True

    except Exception as e:
        print(f"Redis SET error: {e}")

        return False


def delete_cache(key: str) -> bool:

    try:
        redis_client.delete(key)

        return True

    except Exception as e:
        print(f"Redis DELETE error: {e}")

        return False