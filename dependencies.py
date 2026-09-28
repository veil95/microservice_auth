from fastapi import Request
from typing import Annotated
from fastapi import Depends
from clients.chat_service import ChatServiceClient


def get_chat_service(request: Request) -> ChatServiceClient:
    return request.app.state.chat_service


ChatServiceDep = Annotated[ChatServiceClient, Depends(get_chat_service)]