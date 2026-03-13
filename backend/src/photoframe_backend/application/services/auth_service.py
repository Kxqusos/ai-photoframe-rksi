import hmac
from datetime import datetime, timedelta, timezone

import jwt


class AuthService:
    def __init__(
        self,
        *,
        admin_username: str,
        admin_password: str,
        jwt_secret: str,
        jwt_expire_minutes: int,
    ) -> None:
        self._admin_username = admin_username
        self._admin_password = admin_password
        self._jwt_secret = jwt_secret
        self._jwt_expire_minutes = jwt_expire_minutes

    @property
    def admin_username(self) -> str:
        return self._admin_username

    def verify_admin_credentials(self, username: str, password: str) -> bool:
        if not hmac.compare_digest(username, self._admin_username):
            return False
        if not self._admin_password:
            return False
        return hmac.compare_digest(password, self._admin_password)

    def create_access_token(self, subject: str) -> str:
        expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=self._jwt_expire_minutes)
        payload = {"sub": subject, "exp": expires_at}
        return jwt.encode(payload, self._jwt_secret, algorithm="HS256")

    def decode_access_token(self, token: str) -> dict:
        payload = jwt.decode(token, self._jwt_secret, algorithms=["HS256"])
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise ValueError("invalid token payload")
        return payload
