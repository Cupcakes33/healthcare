from fastapi import FastAPI

app = FastAPI(
    title="스마트 문진 요약 및 검진 패키지 추천",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
