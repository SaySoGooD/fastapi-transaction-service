from app.config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from contextlib import asynccontextmanager

import redis.asyncio as redis
from loguru import logger

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD
)

@asynccontextmanager
async def acquire_locks(user_ids: list[int], timeout=10):
    locks = []
    try:
        for user_id in sorted(user_ids):
            key = f"lock:user:{user_id}"
            locked = await redis_client.set(key, "1", nx=True, ex=timeout)
            if not locked:
                raise Exception(f"User {user_id} is locked, aborting transaction")
            locks.append(key)
        yield
    finally:
        for key in locks:
            try:
                await redis_client.delete(key)
                logger.debug(f"Lock released for {key}")
            except Exception as e:
                logger.error(f"Error releasing lock for {key}: {e}")


async def is_locked(user_ids: list[int]) -> bool:
    for user_id in user_ids:
        key = f"lock:user:{user_id}"
        if await redis_client.exists(key):
            return True
    return False
