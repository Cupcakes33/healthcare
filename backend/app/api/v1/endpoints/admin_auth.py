from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.auth import authenticate_admin, create_token
from app.domain.schemas.admin import AdminLoginRequest, AdminLoginResponse

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest) -> AdminLoginResponse:
    if not authenticate_admin(request.username, request.password):
        raise HTTPException(status_code=401, detail="인증에 실패했습니다")

    token, expires_at = create_token()
    return AdminLoginResponse(token=token, expires_at=expires_at)
