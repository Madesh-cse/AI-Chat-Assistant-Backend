import os

import redis  # type: ignore
from dotenv import load_dotenv  # type: ignore


load_dotenv()


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)


# ==================================================
# REDIS CLIENT
# ==================================================

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
)


# ==================================================
# GET REDIS
# ==================================================

def get_redis():
    return redis_client


# ==================================================
# TEST CONNECTION
# ==================================================

def test_redis_connection() -> bool:

    try:

        return bool(
            redis_client.ping()
        )

    except redis.RedisError:

        return False