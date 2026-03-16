from __future__ import annotations

import hmac
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Tuple

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

TOKEN_EXPIRY_HOURS = 24
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300

_token_store: Dict[str, datetime] = {}
_login_attempts: Dict[str, Tuple[int, float]] = {}


def create_token() -> tuple:
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    _token_store[token] = expires_at
    return token, expires_at


def verify_token(token: str) -> bool:
    expires_at = _token_store.get(token)
    if expires_at is None:
        return False
    if datetime.utcnow() > expires_at:
        del _token_store[token]
        return False
    return True


def _check_rate_limit(client_ip: str) -> None:
    entry = _login_attempts.get(client_ip)
    if entry is None:
        return

    attempts, locked_until = entry
    if locked_until and time.monotonic() < locked_until:
        raise HTTPException(
            status_code=429,
            detail="로그인 시도 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.",
        )

    if locked_until and time.monotonic() >= locked_until:
        del _login_attempts[client_ip]


def _record_failed_attempt(client_ip: str) -> None:
    entry = _login_attempts.get(client_ip)
    attempts = (entry[0] + 1) if entry else 1

    locked_until = None
    if attempts >= MAX_LOGIN_ATTEMPTS:
        locked_until = time.monotonic() + LOGIN_LOCKOUT_SECONDS

    _login_attempts[client_ip] = (attempts, locked_until)


def _clear_attempts(client_ip: str) -> None:
    _login_attempts.pop(client_ip, None)


def authenticate_admin(username: str, password: str, client_ip: str = "unknown") -> bool:
    _check_rate_limit(client_ip)

    if not settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="관리자 비밀번호가 설정되지 않았습니다",
        )

    username_match = hmac.compare_digest(username, settings.ADMIN_USERNAME)
    password_match = hmac.compare_digest(password, settings.ADMIN_PASSWORD)

    if username_match and password_match:
        _clear_attempts(client_ip)
        return True

    _record_failed_attempt(client_ip)
    return False


security = HTTPBearer()


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    return token
