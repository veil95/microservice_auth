from redis.asyncio import Redis, RedisError
from errors import RateLimiterUnavailable


RATE_LIMIT_LOGIN_ATTEMPTS = 5
TTL_SECONDS = 60


class Ratelimit:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_rate_limit(self, username: str) -> bool:
        try:
            attempts = await self.redis.get(f"auth:login:{username}")
        except RedisError:
            raise RateLimiterUnavailable
        if attempts is None:
            return True
        elif int(attempts) < RATE_LIMIT_LOGIN_ATTEMPTS:
            return True
        else:
            return False

    async def increment_login_attempt(self, username: str) -> None:
        try:
            key = f"auth:login:{username}"
            async with self.redis.pipeline(transaction=True) as pipeline:
                pipeline.incr(key)
                pipeline.expire(key, TTL_SECONDS)
                await pipeline.execute()
        except RedisError:
            raise RateLimiterUnavailable

    async def reset_attempts(self, username: str) -> None:
        try:
            await self.redis.delete(f"auth:login:{username}")
        except RedisError:
            raise RateLimiterUnavailable
        return


