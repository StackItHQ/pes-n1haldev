import redis
from app.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL)

def get_cached_data(key: str):
    data = redis_client.get(key)
    return data.decode('utf-8') if data else None

def set_cached_data(key: str, value: str, expiration: int = 3600):
    redis_client.setex(key, expiration, value)

def invalidate_cache(key: str):
    redis_client.delete(key)