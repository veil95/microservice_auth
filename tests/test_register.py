import pytest

VALID_USER = {"username": "bob", "display_name": "Bob", "password_plaintext": "secret123"}

def register(client, **overrides):
    return client.post("/auth/register", json={**VALID_USER, **overrides})


def test_register_success(client, fake_chat_service):
    response = register(client)

    assert response.status_code == 201
    assert "bob" in fake_chat_service.users_db
    assert fake_chat_service.users_db["bob"]["user_id"] in response.json()["message"]


def test_register_stores_argon2_hash_not_plaintext(client, fake_chat_service):
    register(client)

    stored = fake_chat_service.users_db["bob"]["hashed_password"]
    assert stored != "secret123"
    assert stored.startswith("$argon2id$")


def test_register_stores_display_name(client, fake_chat_service):
    register(client, display_name="Bobby")

    assert fake_chat_service.users_db["bob"]["display_name"] == "Bobby"


def test_register_duplicate_username_returns_409(client):
    register(client)

    response = register(client, display_name="Another Bob")

    assert response.status_code == 409


@pytest.mark.parametrize("username", ["bob", "BOB", "bob_1", "a_b", "x" * 25])
def test_register_accepts_valid_usernames(client, username):
    assert register(client, username=username).status_code == 201


@pytest.mark.parametrize("username", ["bad name", "bob!", "bob-1", "боб", "bob\n"])
def test_register_rejects_invalid_username_chars(client, username):
    response = register(client, username=username)

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["type"] == "username_invalid_chars"
    assert error["loc"] == ["body", "username"]


@pytest.mark.parametrize(
    ("field", "value", "error_type"),
    [
        ("username", "ab", "string_too_short"),
        ("username", "x" * 26, "string_too_long"),
        ("username", 123, "string_type"),
        ("display_name", "", "string_too_short"),
        ("display_name", "x" * 31, "string_too_long"),
        ("password_plaintext", "1234", "string_too_short"),
    ],
)
def test_register_field_constraints(client, field, value, error_type):
    response = register(client, **{field: value})

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["type"] == error_type
    assert error["loc"] == ["body", field]


@pytest.mark.parametrize("missing_field", ["username", "display_name", "password_plaintext"])
def test_register_missing_field_returns_422(client, missing_field):
    payload = {k: v for k, v in VALID_USER.items() if k != missing_field}

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422
    error = response.json()["detail"][0]
    assert error["type"] == "missing"
    assert error["loc"] == ["body", missing_field]


def test_register_reports_all_invalid_fields_at_once(client):
    response = client.post(
        "/auth/register",
        json={"username": "bad name!", "display_name": "", "password_plaintext": "123"},
    )

    assert response.status_code == 422
    invalid_fields = {error["loc"][1] for error in response.json()["detail"]}
    assert invalid_fields == {"username", "display_name", "password_plaintext"}


def test_register_does_not_create_user_on_validation_error(client, fake_chat_service):
    register(client, password_plaintext="123")

    assert "bob" not in fake_chat_service.users_db
