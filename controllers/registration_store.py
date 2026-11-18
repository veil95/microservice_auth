import json
from redis.asyncio import Redis, RedisError
from uuid import UUID
from errors import RegistrationStoreUnavailable, RegistrationNotFound, InvalidRegistrationCode
from controllers.user_auth import AuthController


auth_controller = AuthController()


class RegistrationStore:
    TTL_SECONDS = 300

    def __init__(self, redis: Redis):
        self.redis = redis

    async def create_form(self, registration_id: UUID, email: str,
                          username: str, hashed_password: str, display_name: str, token: str):
        key = f"auth:registration:{registration_id}"

        hash_token = auth_controller.hash_password(token)
        data = {
            "email": email,
            "username": username,
            "hashed_password": hashed_password,
            "display_name": display_name,
            "hash_token": hash_token,
        }
        try:
            async with self.redis.pipeline(transaction=True) as pipeline:
                pipeline.set(key, json.dumps(data))
                pipeline.expire(key, self.TTL_SECONDS)
                await pipeline.execute()
        except RedisError:
            raise RegistrationStoreUnavailable

    async def check_form(self, registration_id: UUID, token: str):
        if registration_id is None:
            raise RegistrationNotFound
        key = f"auth:registration:{registration_id}"
        try:
            data = await self.redis.get(key)
            if data is None:
                raise RegistrationNotFound
        except RedisError:
            raise RegistrationStoreUnavailable
        data = json.loads(data)
        hash_token = data["hash_token"]
        check = auth_controller.verify_password(token, hash_token)
        if check:
            return data
        else:
            raise InvalidRegistrationCode
