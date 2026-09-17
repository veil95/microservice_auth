from fastapi import APIRouter, HTTPException, status, Response, Depends
from controllers.user_auth import AuthController
from controllers.check_rate_limit import Ratelimit
from controllers.jwt_handler import create_access_token, create_refresh_token, verify_access_token
from model.user import UserLogin, UserRequestRegistration
from model.user import user_instance as user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from model.token import TokenTransport, TokenJWT, TokenTypeJWT

ratelimit = Ratelimit()
auth_controller = AuthController()
security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login")
async def login(user_data: UserLogin, response: Response) -> TokenJWT:
    if not ratelimit.check_rate_limit(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later"
        )

    if (not user.user_exists(user_data.username) or not
    (auth_controller.verify_password(user_data.password, user.get_hashed_password(user_data.username)))):
        ratelimit.increment_login_attempt(user_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password"
        )

    access_token = create_access_token(user_data.username)

    refresh_token = create_refresh_token(user_data.username)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )

    ratelimit.reset_attempts(user_data.username)

    return TokenJWT(token=access_token, type=TokenTypeJWT.ACCESS_TOKEN, transport=TokenTransport.BEARER)


@router.post("/register",status_code=201)
async def register(user_data: UserRequestRegistration):
    if user.user_exists(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username is already registered"
        )

    hashed_password = auth_controller.hash_password(user_data.password_plaintext)

    user.create_user(user_data.username, hashed_password, user_data.displayname)

    return {"message": "пользователь создан"}


@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials

    payload = verify_access_token(token)

    user_data = user.get_user(payload["sub"])

    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "user does not exist")

    return {
        "username": payload["sub"],
        "displayname": user_data.get("displayname")
    }
