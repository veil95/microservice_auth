from fastapi import Request
from typing import Annotated
from fastapi import Depends
from clients.chat_service import ChatServiceClient
from controllers.check_rate_limit import Ratelimit
from controllers.registration_store import RegistrationStore


def get_chat_service(request: Request) -> ChatServiceClient:
    return request.app.state.chat_service


def get_rate_limiter(request: Request) -> Ratelimit:
    return request.app.state.rate_limiter


def get_registration_store(request: Request) -> RegistrationStore:
    return request.app.state.registration_store


ChatServiceDep = Annotated[ChatServiceClient, Depends(get_chat_service)]
RatelimiterDep = Annotated[Ratelimit, Depends(get_rate_limiter)]
RegistrationStoreDep = Annotated[RegistrationStore, Depends(get_registration_store)]
