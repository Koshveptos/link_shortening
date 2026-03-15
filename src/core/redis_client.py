import redis.asyncio as redis

from src.core.config import settings

redis_client = redis.from_url(  # type: ignore[no-any-return]
    settings.REDIS_URL,
    decode_responses=True,
)


async def close_redis() -> None:
    await redis_client.close()
