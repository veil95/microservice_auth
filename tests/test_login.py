from controllers.check_rate_limit import RATE_LIMIT_LOGIN_ATTEMPTS as RATE_LIMIT_MAX_ATTEMPTS


def login(client, username, password):
    return client.post("/auth/login", json={"username": username, "password": password})


def test_login_success_returns_access_token(client, create_user):
    user = create_user()

    response = client.post("/auth/login", json=user)

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "access_token"
    assert body["transport"] == "bearer"
    assert body["token"]


def test_login_access_token_works_for_me(client, create_user):
    user = create_user()
    token = client.post("/auth/login", json=user).json()["token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["username"] == "bob"


def test_login_sets_httponly_refresh_cookie(client, create_user):
    response = client.post("/auth/login", json=create_user())

    set_cookie = response.headers["set-cookie"]
    assert set_cookie.startswith("refresh_token=")
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "refresh_token" in client.cookies


def test_login_wrong_password_returns_401(client, create_user):
    create_user()

    response = login(client, "bob", "wrong-password")

    assert response.status_code == 401
    assert "refresh_token" not in client.cookies


def test_login_nonexistent_user_returns_401(client):
    response = login(client, "ghost", "whatever")

    assert response.status_code == 401


def test_login_does_not_reveal_whether_user_exists(client, create_user):
    create_user()

    wrong_password = login(client, "bob", "wrong-password")
    nonexistent_user = login(client, "ghost", "wrong-password")

    assert wrong_password.status_code == nonexistent_user.status_code
    assert wrong_password.json() == nonexistent_user.json()


def test_login_password_is_case_sensitive(client, create_user):
    create_user(password="Secret123")

    assert login(client, "bob", "secret123").status_code == 401


def test_login_missing_field_returns_422(client):
    response = client.post("/auth/login", json={"username": "bob"})

    assert response.status_code == 422


def test_login_blocks_after_too_many_failed_attempts(client, create_user):
    create_user()

    codes = [login(client, "bob", "wrong").status_code for _ in range(RATE_LIMIT_MAX_ATTEMPTS + 2)]

    assert codes == [401] * RATE_LIMIT_MAX_ATTEMPTS + [429, 429]


def test_login_blocked_even_with_correct_password(client, create_user):
    user = create_user()
    for _ in range(RATE_LIMIT_MAX_ATTEMPTS):
        login(client, "bob", "wrong")

    response = client.post("/auth/login", json=user)

    assert response.status_code == 429
    assert "refresh_token" not in client.cookies


def test_login_rate_limit_is_per_username(client, create_user):
    create_user("bob")
    alice = create_user("alice")
    for _ in range(RATE_LIMIT_MAX_ATTEMPTS + 1):
        login(client, "bob", "wrong")

    assert client.post("/auth/login", json=alice).status_code == 200


def test_login_success_resets_failed_attempts(client, create_user):
    user = create_user()
    for _ in range(RATE_LIMIT_MAX_ATTEMPTS - 1):
        login(client, "bob", "wrong")
    assert client.post("/auth/login", json=user).status_code == 200

    codes = [login(client, "bob", "wrong").status_code for _ in range(RATE_LIMIT_MAX_ATTEMPTS)]

    assert codes == [401] * RATE_LIMIT_MAX_ATTEMPTS


def test_login_still_blocked_before_cooldown_ends(client, create_user, clock):
    user = create_user()
    for _ in range(RATE_LIMIT_MAX_ATTEMPTS + 1):
        login(client, "bob", "wrong")

    clock.advance(30)

    assert client.post("/auth/login", json=user).status_code == 429


def test_login_unblocked_after_cooldown(client, create_user, clock):
    user = create_user()
    for _ in range(RATE_LIMIT_MAX_ATTEMPTS + 1):
        login(client, "bob", "wrong")

    clock.advance(61)

    assert client.post("/auth/login", json=user).status_code == 200
