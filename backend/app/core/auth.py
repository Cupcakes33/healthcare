from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

TOKEN_EXPIRY_HOURS = 24

_token_store: Dict[str, datetime] = {}

security = HTTPBearer()


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


def authenticate_admin(username: str, password: str) -> bool:
    return (
        username == settings.ADMIN_USERNAME
        and password == settings.ADMIN_PASSWORD
    )


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    return token
