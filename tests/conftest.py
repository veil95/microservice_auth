import os
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from clients.chat_service import ChatServiceClient
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

from controllers.jwt_handler import ALGORITHM, SECRET_KEY  # noqa: E402
from main import app  # noqa: E402
from model.user import user_instance  # noqa: E402
from views.auth import ratelimit  # noqa: E402


@pytest.fixture(autouse=True)
def reset_state():
    user_instance.users_db.clear()
    ratelimit.login_attempts.clear()
    yield
    user_instance.users_db.clear()
    ratelimit.login_attempts.clear()


@pytest.fixture
def client():
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