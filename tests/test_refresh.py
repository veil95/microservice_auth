from datetime import timedelta

from model.user import user_instance


def login(client, user):
    return client.post("/auth/login", json=user)


def test_refresh_returns_new_access_token(client, create_user):
    login(client, create_user())

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "access_token"
    assert body["transport"] == "bearer"
    assert body["token"]


def test_refresh_access_token_works_for_me(client, create_user):
    login(client, create_user())
    token = client.post("/auth/refresh").json()["token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["username"] == "bob"


def test_refresh_sets_httponly_refresh_cookie(client, create_user):
    login(client, create_user())

    response = client.post("/auth/refresh")

    set_cookie = response.headers["set-cookie"]
    assert set_cookie.startswith("refresh_token=")
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie


def test_refresh_can_be_repeated(client, create_user):
    login(client, create_user())

    codes = [client.post("/auth/refresh").status_code for _ in range(3)]

    assert codes == [200, 200, 200]


def test_refresh_without_cookie_returns_401(client):
    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token not found"


def test_refresh_with_access_token_in_cookie_returns_401(client, create_user, make_token):
    create_user()
    client.cookies.set("refresh_token", make_token(token_type="access_token"))

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token type"


def test_refresh_with_expired_token_returns_401(client, create_user, make_token):
    create_user()
    client.cookies.set("refresh_token", make_token(token_type="refresh_token", expires_in=timedelta(days=-1)))

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


def test_refresh_with_garbage_cookie_returns_401(client):
    client.cookies.set("refresh_token", "not-a-jwt")

    response = client.post("/auth/refresh")

    assert response.status_code == 401


def test_refresh_with_token_without_sub_returns_401(client, make_token):
    client.cookies.set("refresh_token", make_token(sub=None, token_type="refresh_token"))

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token payload"


def test_refresh_ignores_bearer_header(client, create_user, make_token):
    create_user()
    token = make_token(token_type="refresh_token")

    response = client.post("/auth/refresh", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token not found"


def test_refresh_for_deleted_user_returns_401(client, create_user):
    login(client, create_user())
    user_instance.users_db.pop("bob")

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "user does not exist"
