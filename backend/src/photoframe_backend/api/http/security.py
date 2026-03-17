import hmac
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from photoframe_backend.application.services.auth_service import AuthService
from photoframe_backend.infrastructure.settings.runtime import load_settings

JWT_ALGORITHM = "HS256"
settings = load_settings(allow_test_defaults=True)
ROOM_ACCESS_EXPIRE_HOURS = 12

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


def hash_room_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"


def verify_room_password(password: str, password_hash: str) -> bool:
    parts = password_hash.split("$")
    if len(parts) != 3 or parts[0] != "scrypt":
        return False
    try:
      salt = base64.b64decode(parts[1])
      expected = base64.b64decode(parts[2])
    except Exception:
      return False
    actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return hmac.compare_digest(actual, expected)


def create_room_access_token(room_slug: str) -> str:
    expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=ROOM_ACCESS_EXPIRE_HOURS)
    payload = {"sub": room_slug, "scope": "room", "exp": expires_at}
    return jwt.encode(payload, settings.auth.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_room_access_token(token: str) -> dict:
    payload = jwt.decode(token, settings.auth.jwt_secret, algorithms=[JWT_ALGORITHM])
    subject = payload.get("sub")
    scope = payload.get("scope")
    if not isinstance(subject, str) or scope != "room":
        raise ValueError("invalid room token payload")
    return payload


def require_room_access(
    room_slug: str,
    x_room_access_token: str | None = Header(default=None, alias="X-Room-Access-Token"),
) -> str:
    if not x_room_access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="room access token required")

    try:
        payload = decode_room_access_token(x_room_access_token)
    except (jwt.PyJWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid room access token") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not hmac.compare_digest(subject, room_slug):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid room access token")
    return subject


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
