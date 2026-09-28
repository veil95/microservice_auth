import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from clients.chat_service import ChatServiceClient
from dependencies import get_chat_service

os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

from errors import UserAlreadyExists
from controllers.jwt_handler import ALGORITHM, SECRET_KEY  # noqa: E402
from main import app  # noqa: E402
from views.auth import ratelimit  # noqa: E402

class FakeChatService():
    def __init__(self):
        self.users_db = {}

    async def create_user(self, username: str, hashed_password: str, display_name: str) -> dict | None:
        if username in self.users_db:
            raise UserAlreadyExists
        self.users_db[username] = {"hashed_password": hashed_password,
                                   "display_name": display_name,
                                   "user_id": str(uuid.uuid4()),
                                   "deleted_at": None}
        return self.users_db[username]

    async def get_credential(self, username: str) -> dict | None:
        if not username in self.users_db:
            return None
        return {"username": username,
                "user_id": self.users_db[username]["user_id"],
                "hashed_password": self.users_db[username]["hashed_password"]}

    async def get_user(self, user_id: str) -> dict | None:
        for username, user in self.users_db.items():
            if user_id == user["user_id"]:
                return {"username": username,
                        "user_id": user["user_id"],
                        "display_name": user["display_name"],
                        "deleted_at": user["deleted_at"]}
        return None

@pytest.fixture
def fake_chat_service():
    fake = FakeChatService()
    app.dependency_overrides[get_chat_service] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_state():
    ratelimit.login_attempts.clear()
    yield
    ratelimit.login_attempts.clear()


@pytest.fixture
def client(fake_chat_service):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def create_user(client):
    def _create(username="bob", password="secret123", display_name="Bob"):
        response = client.post(
            "/auth/register",
            json={
                "username": username,
                "display_name": display_name,
                "password_plaintext": password,
            },
        )
        response.raise_for_status()
        return {"username": username, "password": password}

    return _create


@pytest.fixture
def make_token():
    def _make(sub="bob", token_type="access_token", expires_in=timedelta(minutes=15), secret=SECRET_KEY):
        payload = {"type": token_type, "exp": datetime.now(timezone.utc) + expires_in}
        if sub is not None:
            payload["sub"] = sub
        return jwt.encode(payload, secret, algorithm=ALGORITHM)

    return _make


class FakeClock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    fake_clock = FakeClock()
    monkeypatch.setattr("controllers.check_rate_limit.time", fake_clock)
    return fake_clock

@pytest.fixture
def make_chat_service():
    def _make(status_code=200, json=None, exc=None):
        requests = []
        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if exc is not None:
                raise exc
            return httpx.Response(status_code, json=json)

        http = httpx.AsyncClient(
            base_url="http://test",
            transport=httpx.MockTransport(handler),
        )
        return ChatServiceClient(http), requests

    return _make