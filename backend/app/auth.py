import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings

JWT_ALGORITHM = "HS256"

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/api/admin/auth", tags=["admin-auth"])


class AdminLoginIn(BaseModel):
    username: str
    password: str


class AdminTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminProfileOut(BaseModel):
    username: str


def verify_admin_credentials(username: str, password: str) -> bool:
    if not hmac.compare_digest(username, settings.admin_username):
        return False

    if settings.admin_password:
        return hmac.compare_digest(password, settings.admin_password)

    if not settings.admin_password_hash:
        return False

    try:
        return password_context.verify(password, settings.admin_password_hash)
    except ValueError:
        return False


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
    if not isinstance(subject, str) or not hmac.compare_digest(subject, settings.admin_username):
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

    token = create_access_token(settings.admin_username)
    return AdminTokenOut(access_token=token)


@router.get("/me", response_model=AdminProfileOut)
def admin_me(username: str = Depends(require_admin)) -> AdminProfileOut:
    return AdminProfileOut(username=username)
