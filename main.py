from contextlib import asynccontextmanager
from os import getenv

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from views.auth import router
from views.token_routes import token_router
from errors import UserAlreadyExists, ChatServiceUnavailable
from clients.chat_service import ChatServiceClient


CHAT_SERVICE_URL=getenv("CHAT_SERVICE_URL")


@asynccontextmanager
async def lifespan(app: FastAPI):
    http = httpx.AsyncClient(base_url=CHAT_SERVICE_URL, timeout=5)
    app.state.chat_service = ChatServiceClient(http)
    yield
    await http.aclose()

app = FastAPI(lifespan=lifespan)

app.include_router(router)
app.include_router(token_router)

@app.exception_handler(UserAlreadyExists)
async def user_already_exists_handler(request: Request, exc: UserAlreadyExists):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "username is already registered"}
    )


@app.exception_handler(ChatServiceUnavailable)
async def chat_service_unavailable_handler(request: Request, exc: ChatServiceUnavailable):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "Service temporarily unavailable"}
    )


@app.get("/")
async def root():
    return {"message": "server work"}



