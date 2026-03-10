from __future__ import annotations

import re
import secrets

PUBLIC_ID_LENGTH = 8
PUBLIC_ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
PUBLIC_ID_PATTERN = rf"^[a-z0-9]{{{PUBLIC_ID_LENGTH}}}$"
PUBLIC_ID_REGEX = re.compile(PUBLIC_ID_PATTERN)
DEFAULT_PUBLIC_ID = "ph000000"


def normalize_public_id(value: str | None, *, fallback: str = DEFAULT_PUBLIC_ID) -> str:
    candidate = (value or "").strip().lower()
    if PUBLIC_ID_REGEX.fullmatch(candidate):
        return candidate
    return fallback


def is_public_id(value: str | None) -> bool:
    candidate = (value or "").strip().lower()
    return bool(PUBLIC_ID_REGEX.fullmatch(candidate))


def generate_public_id() -> str:
    return "".join(secrets.choice(PUBLIC_ID_ALPHABET) for _ in range(PUBLIC_ID_LENGTH))
