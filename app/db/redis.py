import aioredis
from app.core.config import settings

redis = None


async def connect_redis():
    global redis
    redis = await aioredis.create_redis_pool(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", maxsize=10
    )


async def close_redis():
    redis.close()
    await redis.wait_closed()


async def get_redis_client():
    return redis
