from fastapi import APIRouter

v1_router = APIRouter()


@v1_router.get("/")
async def v1_root():
    return {"message": "API v1"}
