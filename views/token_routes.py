from fastapi import HTTPException, APIRouter, Response, Request
from controllers.jwt_handler import verify_refresh_token, create_refresh_token, create_access_token
from model.user import user_instance as user
from model.token import TokenTypeJWT, TokenJWT, TokenTransport
from fastapi import status
token_router = APIRouter(prefix="/auth", tags=["token"])


@token_router.post("/refresh")
async def get_refresh_token(request: Request, response: Response) -> TokenJWT:
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found")

    payload = verify_refresh_token(refresh_token)

    user_data = user.get_user(payload.get("sub"))

    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user does not exist")
    new_access_token = create_access_token(payload.get("sub"))
    new_refresh_token = create_refresh_token(payload.get("sub"))

    response.set_cookie(
    key="refresh_token",
    value=new_refresh_token,
    httponly=True,
    secure=False,
    samesite="lax"
    )

    return TokenJWT(token=new_access_token, type=TokenTypeJWT.ACCESS_TOKEN, transport=TokenTransport.BEARER)
