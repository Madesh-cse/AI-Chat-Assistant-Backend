from app.core.redis import redis_client


try:
    redis_client.set("test:key", "Redis is working")
    
    value = redis_client.get("test:key")

    print("Redis connection successful")
    print("Value:", value)

except Exception as e:
    print("Redis connection failed:", e)