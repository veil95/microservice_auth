import pytest

from controllers.user_auth import AuthController


@pytest.fixture
def auth():
    return AuthController()


def test_hash_is_not_plaintext(auth):
    hashed = auth.hash_password("secret123")

    assert hashed != "secret123"
    assert hashed.startswith("$argon2id$")


def test_same_password_gives_different_hashes(auth):
    assert auth.hash_password("secret123") != auth.hash_password("secret123")


def test_verify_correct_password(auth):
    hashed = auth.hash_password("secret123")

    assert auth.verify_password("secret123", hashed) is True


def test_verify_wrong_password(auth):
    hashed = auth.hash_password("secret123")

    assert auth.verify_password("wrong", hashed) is False


@pytest.mark.parametrize("hashed", [None, ""])
def test_verify_without_hash_returns_false(auth, hashed):
    assert auth.verify_password("secret123", hashed) is False
