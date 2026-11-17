from contextlib import asynccontextmanager
from os import getenv
from controllers.check_rate_limit import Ratelimit
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from views.auth import router
from views.token_routes import token_router
from errors import UserAlreadyExists, ChatServiceUnavailable, RateLimiterUnavailable, RegistrationStoreUnavailable
from errors import RegistrationNotFound, InvalidRegistrationCode
from clients.chat_service import ChatServiceClient
from redis.asyncio import Redis
from controllers.registration_store import RegistrationStore

CHAT_SERVICE_URL = getenv("CHAT_SERVICE_URL")
REDIS_URL = getenv("REDIS_URL")


@asynccontextmanager
async def lifespan(app: FastAPI):
    http = httpx.AsyncClient(base_url=CHAT_SERVICE_URL, timeout=5)
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    rate_limiter = Ratelimit(redis)
    registration_store = RegistrationStore(redis)
    app.state.registration_store = registration_store
    app.state.chat_service = ChatServiceClient(http)
    app.state.rate_limiter = rate_limiter
    yield
    await http.aclose()
    await redis.aclose()
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


@app.exception_handler(RateLimiterUnavailable)
async def rate_limiter_unavailable_handler(request: Request, exc: RateLimiterUnavailable):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "Rate limiter temporarily unavailable"}
    )


@app.exception_handler(RegistrationStoreUnavailable)
async def registration_store_unavailable(request: Request, exc: RegistrationStoreUnavailable):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "Registration store temporarily unavailable"}
    )


@app.exception_handler(RegistrationNotFound)
async def registration_not_found(request: Request, exc: RegistrationNotFound):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "registration_not_found"}
    )


@app.exception_handler(InvalidRegistrationCode)
async def invalid_registration_code(request: Request, exc: InvalidRegistrationCode):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "invalid_registration_code"}
    )


@app.get("/")
async def root():
    return {"message": "server work"}



