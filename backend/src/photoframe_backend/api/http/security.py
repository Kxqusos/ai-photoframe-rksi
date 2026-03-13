import hmac

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from photoframe_backend.application.services.auth_service import AuthService
from photoframe_backend.infrastructure.settings.loader import load_env_file
from photoframe_backend.infrastructure.settings.models import RuntimeSettings
from photoframe_backend.shared.constants import DEFAULT_ENV_FILE

JWT_ALGORITHM = "HS256"
load_env_file(DEFAULT_ENV_FILE)
settings = RuntimeSettings()

router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


class AdminLoginIn(BaseModel):
    username: str
    password: str


class AdminTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminProfileOut(BaseModel):
    username: str


def _auth_service() -> AuthService:
    return AuthService(
        admin_username=settings.auth.admin_username,
        admin_password=settings.auth.admin_password,
        jwt_secret=settings.auth.jwt_secret,
        jwt_expire_minutes=settings.auth.jwt_expire_minutes,
    )


def verify_admin_credentials(username: str, password: str) -> bool:
    return _auth_service().verify_admin_credentials(username, password)


def create_access_token(subject: str) -> str:
    return _auth_service().create_access_token(subject)


def decode_access_token(token: str) -> dict:
    try:
        payload = _auth_service().decode_access_token(token)
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return payload


def require_admin(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    subject = payload.get("sub")
    if not isinstance(subject, str) or not hmac.compare_digest(subject, settings.auth.admin_username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return subject


@router.post("/login", response_model=AdminTokenOut)
def admin_login(payload: AdminLoginIn) -> AdminTokenOut:
    if not verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(settings.auth.admin_username)
    return AdminTokenOut(access_token=token)


@router.get("/me", response_model=AdminProfileOut)
def admin_me(username: str = Depends(require_admin)) -> AdminProfileOut:
    return AdminProfileOut(username=username)
