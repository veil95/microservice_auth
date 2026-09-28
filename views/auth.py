from fastapi import APIRouter, HTTPException, status, Response, Depends
from controllers.user_auth import AuthController
from controllers.check_rate_limit import Ratelimit
from controllers.jwt_handler import create_access_token, create_refresh_token, verify_access_token
from model.user import UserLogin, UserRequestRegistration
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from model.token import TokenTransport, TokenJWT, TokenTypeJWT
from dependencies import ChatServiceDep

ratelimit = Ratelimit()
auth_controller = AuthController()
security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login")
async def login(user_data: UserLogin, response: Response, chat_service: ChatServiceDep) -> TokenJWT:
    username = user_data.username.lower()
    if not ratelimit.check_rate_limit(username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later"
        )
    user_credential = await chat_service.get_credential(username)
    if (not user_credential or not
    (auth_controller.verify_password(user_data.password, user_credential["hashed_password"]))):
        ratelimit.increment_login_attempt(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password"
        )

    access_token = create_access_token(str(user_credential["user_id"]))

    refresh_token = create_refresh_token(str(user_credential["user_id"]))

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )

    ratelimit.reset_attempts(username)

    return TokenJWT(token=access_token, type=TokenTypeJWT.ACCESS_TOKEN, transport=TokenTransport.BEARER)


@router.post("/register", status_code=201)
async def register(user_data: UserRequestRegistration, chat_service: ChatServiceDep):

    hashed_password = auth_controller.hash_password(user_data.password_plaintext)

    created_user = await chat_service.create_user(username=user_data.username,
                             hashed_password=hashed_password,
                             display_name=user_data.display_name
                             )

    return {"message": f"пользователь с user_id {created_user["user_id"]} создан"}


@router.get("/me")
async def get_current_user(chat_service: ChatServiceDep, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials

    payload = verify_access_token(token)

    user_data = await chat_service.get_user(payload["sub"])

    if not user_data or user_data["deleted_at"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user does not exist")

    return {
        "user_id": payload["sub"],
        "username": user_data.get("username"),
        "display_name": user_data.get("display_name")
    }
