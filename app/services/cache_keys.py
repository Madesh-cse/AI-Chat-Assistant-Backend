import hashlib


def chat_cache_key(message: str) -> str:

    normalized = message.strip().lower()

    message_hash = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()

    return f"chat:response:{message_hash}"