from fastapi import APIRouter

from app.api.v1.endpoints.admin_auth import router as admin_auth_router
from app.api.v1.endpoints.admin_packages import router as admin_packages_router
from app.api.v1.endpoints.admin_stats import router as admin_stats_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.questionnaire import router as questionnaire_router
from app.api.v1.endpoints.result import router as result_router

v1_router = APIRouter()

v1_router.include_router(questionnaire_router, tags=["환자"])
v1_router.include_router(result_router, tags=["환자"])
v1_router.include_router(chat_router, prefix="/chat", tags=["채팅 문진"])
v1_router.include_router(admin_auth_router, prefix="/admin", tags=["관리자"])
v1_router.include_router(admin_packages_router, prefix="/admin", tags=["관리자"])
v1_router.include_router(admin_stats_router, prefix="/admin", tags=["관리자"])


@v1_router.get("/")
async def v1_root():
    return {"message": "API v1"}
