from fastapi import Request
from typing import Annotated
from fastapi import Depends
from clients.chat_service import ChatServiceClient
from controllers.check_rate_limit import Ratelimit


def get_chat_service(request: Request) -> ChatServiceClient:
    return request.app.state.chat_service


def get_rate_limiter(request: Request) -> Ratelimit:
    return request.app.state.rate_limiter


ChatServiceDep = Annotated[ChatServiceClient, Depends(get_chat_service)]
RatelimiterDep = Annotated[Ratelimit, Depends(get_rate_limiter)]
