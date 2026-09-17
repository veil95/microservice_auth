from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from os import getenv
from dotenv import load_dotenv
from jose import jwt
from model.token import TokenTypeJWT
load_dotenv()

SECRET_KEY = getenv("SECRET_KEY")
ALGORITHM = getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(getenv("REFRESH_TOKEN_EXPIRE_DAYS"))


def create_refresh_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data = {"sub": username,
            "exp": expire,
            "type": "refresh_token"}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {"sub": username,
            "exp": expire,
            "type": "access_token"}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


def verify_access_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != TokenTypeJWT.ACCESS_TOKEN.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type")
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload")
    return payload


def verify_refresh_token(token: str) -> dict:
    payload = decode_token(token)
    if payload.get("type") != TokenTypeJWT.REFRESH_TOKEN.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type")
    username = payload.get("sub")

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload")
    return payload
