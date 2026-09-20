from datetime import timedelta

from model.user import user_instance


def get_me(client, token):
    return client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})


def login_token(client, user):
    return client.post("/auth/login", json=user).json()["token"]


def test_me_returns_current_user(client, create_user):
    token = login_token(client, create_user(display_name="Bobby"))

    response = get_me(client, token)

    assert response.status_code == 200
    assert response.json() == {"username": "bob", "display_name": "Bobby"}


def test_me_does_not_expose_password_hash(client, create_user):
    token = login_token(client, create_user())

    body = get_me(client, token).json()

    assert "hashed_password" not in body
    assert "password" not in body


def test_me_without_token_returns_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_with_non_bearer_scheme_returns_401(client, create_user):
    token = login_token(client, create_user())

    response = client.get("/auth/me", headers={"Authorization": f"Basic {token}"})

    assert response.status_code == 401


def test_me_with_refresh_token_returns_401(client, create_user):
    create_user()
    client.post("/auth/login", json={"username": "bob", "password": "secret123"})
    refresh_token = client.cookies["refresh_token"]

    response = get_me(client, refresh_token)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token type"


def test_me_with_expired_token_returns_401(client, create_user, make_token):
    create_user()
    token = make_token(expires_in=timedelta(minutes=-1))

    response = get_me(client, token)

    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


def test_me_with_garbage_token_returns_401(client):
    response = get_me(client, "not-a-jwt")

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid token"


def test_me_with_token_signed_by_other_secret_returns_401(client, create_user, make_token):
    create_user()
    token = make_token(secret="attacker-secret")

    response = get_me(client, token)

    assert response.status_code == 401


def test_me_with_token_without_sub_returns_401(client, make_token):
    token = make_token(sub=None)

    response = get_me(client, token)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token payload"


def test_me_for_deleted_user_returns_401(client, create_user):
    token = login_token(client, create_user())
    user_instance.users_db.pop("bob")

    response = get_me(client, token)

    assert response.status_code == 401
    assert response.json()["detail"] == "user does not exist"
