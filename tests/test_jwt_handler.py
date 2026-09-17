from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from controllers.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_access_token,
    verify_refresh_token,
)


def seconds_until(exp):
    return exp - datetime.now(timezone.utc).timestamp()


def test_access_token_payload():
    payload = decode_token(create_access_token("bob"))

    assert payload["sub"] == "bob"
    assert payload["type"] == "access_token"


def test_access_token_expires_in_15_minutes():
    payload = decode_token(create_access_token("bob"))

    assert seconds_until(payload["exp"]) == pytest.approx(15 * 60, abs=5)


def test_refresh_token_payload():
    payload = decode_token(create_refresh_token("bob"))

    assert payload["sub"] == "bob"
    assert payload["type"] == "refresh_token"


def test_refresh_token_expires_in_7_days():
    payload = decode_token(create_refresh_token("bob"))

    assert seconds_until(payload["exp"]) == pytest.approx(7 * 24 * 60 * 60, abs=5)


def test_verify_access_token_accepts_access_token():
    assert verify_access_token(create_access_token("bob"))["sub"] == "bob"


def test_verify_access_token_rejects_refresh_token():
    with pytest.raises(HTTPException) as exc_info:
        verify_access_token(create_refresh_token("bob"))

    assert exc_info.value.status_code == 401


def test_verify_refresh_token_accepts_refresh_token():
    assert verify_refresh_token(create_refresh_token("bob"))["sub"] == "bob"


def test_verify_refresh_token_rejects_access_token():
    with pytest.raises(HTTPException) as exc_info:
        verify_refresh_token(create_access_token("bob"))

    assert exc_info.value.status_code == 401


def test_decode_token_rejects_garbage():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not-a-jwt")

    assert exc_info.value.status_code == 401


def test_decode_token_rejects_tampered_token():
    header, payload, signature = create_access_token("bob").split(".")
    tampered = f"{header}.{payload}.{signature[:-2]}xx"

    with pytest.raises(HTTPException) as exc_info:
        decode_token(tampered)

    assert exc_info.value.status_code == 401
