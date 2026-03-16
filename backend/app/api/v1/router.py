from fastapi import APIRouter

from app.api.v1.endpoints.questionnaire import router as questionnaire_router
from app.api.v1.endpoints.result import router as result_router

v1_router = APIRouter()

v1_router.include_router(questionnaire_router, tags=["환자"])
v1_router.include_router(result_router, tags=["환자"])


@v1_router.get("/")
async def v1_root():
    return {"message": "API v1"}
