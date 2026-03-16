#!/bin/bash
set -e

echo "Alembic 마이그레이션 실행..."
alembic upgrade head

echo "시드 데이터 확인..."
python -m app.seed.packages

echo "서버 시작..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
