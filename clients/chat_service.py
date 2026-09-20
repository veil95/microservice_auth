import uuid
from errors import UserAlreadyExists, ChatServiceUnavailable
import httpx


class ChatServiceClient:
    def __init__(self, http: httpx.AsyncClient):
        self._http = http

    async def _make_request(self,
            method: str,
            url: str,
            *,
            headers=None,
            params=None,
            json=None
    ):
        try:
            response = await self._http.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json
            )
            return response
        except httpx.RequestError:
            raise ChatServiceUnavailable("не было ответа от чат сервиса")

    async def get_credential(self, username: str) -> dict | None:
        response = await self._make_request(
            method="GET",
            url=f"/api/users/by-username/{username}/credential"
        )
        if response.is_success:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise ChatServiceUnavailable(f"chat-service не ответил на GET /api/users/by-username/{username}/credential")

    async def get_user(self, user_id: uuid.UUID) -> dict | None:
        response = await self._make_request(
            method="GET",
            url=f"/api/users/{user_id}"
        )
        if response.is_success:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise ChatServiceUnavailable(f"chat-service не ответил на GET /api/users/{user_id}")

    async def create_user(self, username: str, hashed_password: str, display_name: str) -> dict:
        response = await self._make_request(
            method="POST",
            url="/api/users/",
            json={
                "username": username,
                "display_name": display_name,
                "hashed_password": hashed_password
            }
        )
        if response.is_success:
            return response.json()
        elif response.status_code == 409:
            raise UserAlreadyExists("пользователь с таким именем уже существует")
        else:
            raise ChatServiceUnavailable("chat-service не ответил на POST /api/users/")
