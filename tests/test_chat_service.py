import json

import httpx
import pytest
import uuid
from errors import ChatServiceUnavailable, UserAlreadyExists


async def test_get_user_returns_none_when_not_found(make_chat_service):
    client, _ = make_chat_service(status_code=404)
    assert await client.get_user(uuid.uuid4()) is None


async def test_chat_service_get_user_unavailable_exc(make_chat_service):
    client, requests = make_chat_service(status_code=500)
    with pytest.raises(ChatServiceUnavailable):
        await client.get_user(uuid.uuid4())


async def test_chat_service_get_user_success(make_chat_service):
    client, requests = make_chat_service(status_code=200, json={"username": "bob"})
    user_id = uuid.uuid4()
    assert await client.get_user(user_id) == {"username": "bob"}
    assert requests[0].url.path == f"/api/users/{user_id}"

async def test_get_credentials_success(make_chat_service):
    client, requests = make_chat_service(status_code=200, json={"username": "bob"})
    assert await client.get_credential("bob") == {"username": "bob"}
    assert requests[0].url.path == "/api/users/by-username/bob/credentials"


async def test_get_credentials_none_when_not_found(make_chat_service):
    client, requests = make_chat_service(status_code=404)
    assert await client.get_credential("username") is None


async def test_chat_service_get_credentials_unavailable_exc(make_chat_service):
    client, requests = make_chat_service(status_code=500)
    with pytest.raises(ChatServiceUnavailable):
        await client.get_credential("username")

async def test_chat_service_create_user_user_already_exist_exc(make_chat_service):
    client, requests = make_chat_service(status_code=409)
    with pytest.raises(UserAlreadyExists):
        await client.create_user(username="123",hashed_password="213",display_name="1231")


async def test_chat_service_create_user_unavailable_exc(make_chat_service):
    client, requests = make_chat_service(status_code=500)
    with pytest.raises(ChatServiceUnavailable):
        await client.create_user(username="123",hashed_password="213",display_name="1231")


async def test_chat_service_create_user_is_success(make_chat_service):
    client, requests = make_chat_service(status_code=201, json={"123": "231"})
    assert await client.create_user(username="123",hashed_password="213",display_name="1231") == {"123": "231"}
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/api/users/"
    body = json.loads(requests[0].content)
    assert body == {
        "username": "123",
        "hashed_password": "213",
        "display_name": "1231"
    }


async def test_connect_error_get_user(make_chat_service):
    client, _ = make_chat_service(exc=httpx.ConnectError("123"))
    with pytest.raises(ChatServiceUnavailable):
        await client.get_user(uuid.uuid4())


async def test_connect_error_get_credential(make_chat_service):
    client, _ = make_chat_service(exc=httpx.ConnectError("123"))
    with pytest.raises(ChatServiceUnavailable):
        await client.get_credential("bob")

async def test_connect_error_create_user(make_chat_service):
    client, _ = make_chat_service(exc=httpx.ConnectError("123"))
    with pytest.raises(ChatServiceUnavailable):
        await client.create_user(username="123",hashed_password="213",display_name="1231") == {"123": "231"}


async def test_read_time_out_get_credential(make_chat_service):
    client, _ = make_chat_service(exc=httpx.ReadTimeout("123"))
    with pytest.raises(ChatServiceUnavailable):
        await client.get_credential("bob")