# LLM 기반 스마트 문진 요약 및 검진 패키지 추천

LLM을 활용하여 환자의 문진 데이터를 분석하고, 맞춤형 건강검진 패키지를 추천하는 웹 애플리케이션입니다.

## 라이브 데모

| 서비스 | URL |
|--------|-----|
| Frontend (Vercel) | `배포 후 업데이트` |
| Backend API (Railway) | `배포 후 업데이트` |

## 주요 기능

- **선택지 기반 문진 입력**: 3단계 폼 (기본정보 → 증상 선택 → 상세정보)
- **LLM 문진 요약 + 패키지 추천**: GPT-4o mini / Claude Sonnet 4 기반 분석
- **규칙 기반 Red Flag 탐지**: 5가지 응급 규칙 (심근경색 의심, 벼락두통 등)
- **태그 기반 패키지 매칭**: LLM 실패 시 자동 fallback
- **관리자 대시보드**: 통계 조회 + 검진 패키지 CRUD

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI (Python 3.12), Pydantic v2 |
| Database | PostgreSQL, SQLAlchemy 2.0 (async), Alembic |
| LLM | OpenAI SDK, Anthropic SDK (Strategy 패턴으로 전환) |
| 폼/상태 | React Hook Form + Zod, TanStack Query |
| 테스트 | pytest (Backend), Vitest (Frontend) |
| 배포 | Vercel (FE), Railway (BE + DB) |

## 아키텍처

```
┌──────────────┐     ┌──────────────────────┐     ┌──────────────┐
│   Next.js    │────▶│     FastAPI           │────▶│  PostgreSQL  │
│   (Vercel)   │◀────│     (Railway)         │◀────│  (Railway)   │
└──────────────┘     │                      │     └──────────────┘
                     │  ┌────────────────┐  │
                     │  │ LLM Provider   │  │
                     │  │ (OpenAI /      │  │     ┌──────────────┐
                     │  │  Anthropic)    │──│────▶│  LLM API     │
                     │  └────────────────┘  │     └──────────────┘
                     └──────────────────────┘
```

## 데이터 흐름

```
문진 입력 → Red Flag 규칙 체크 → LLM 분석 (요약 + 태그 추출 + 추천)
                                      │
                                      ├─ 성공 → LLM 추천 결과 사용
                                      │         (신뢰도 낮으면 TagMatcher 보완)
                                      │
                                      └─ 실패 → TagMatcher fallback
                                                (태그 기반 자동 매칭)
                                      │
                                      ▼
                              결과 저장 + 응답 반환
```

## 기술 선택 이유

- **LLM SDK 직접 사용**: LangChain 대신 OpenAI/Anthropic SDK를 Strategy 패턴으로 추상화. 불필요한 의존성 최소화.
- **PackageMatcher 인터페이스 분리**: 현재 `TagMatcher` (태그 기반), 향후 `VectorMatcher` (pgvector) 확장 가능.
- **Red Flag 규칙 외부화**: YAML 기반 규칙 정의로 코드 수정 없이 규칙 추가/변경 가능.
- **Graceful Degradation**: LLM API 장애 시 TagMatcher fallback으로 서비스 연속성 보장.

## 로컬 실행 방법

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에서 DATABASE_URL, LLM API 키, ADMIN_PASSWORD 설정

# DB 마이그레이션 + 시드 데이터
alembic upgrade head
python -m app.seed.packages

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
bun install

# 환경변수 설정
cp .env.local.example .env.local

# 개발 서버 실행
bun dev
```

### 테스트

```bash
# Backend 테스트
cd backend && .venv/bin/python -m pytest -m "not integration"

# Frontend 테스트
cd frontend && bun run test
```

## 환경변수

### Backend (`.env`)

| 변수 | 설명 | 예시 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL | `postgresql+asyncpg://...` |
| `LLM_PROVIDER` | LLM 제공자 | `openai` 또는 `anthropic` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | `sk-ant-...` |
| `CORS_ORIGINS` | 허용 도메인 | `http://localhost:3000` |
| `ADMIN_USERNAME` | 관리자 아이디 | `admin` |
| `ADMIN_PASSWORD` | 관리자 비밀번호 | (보안 문자열 설정) |

### Frontend (`.env.local`)

| 변수 | 설명 | 예시 |
|------|------|------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |

## 의료 면책 조항

> 본 서비스는 의료 행위가 아니며, 참고용 정보만 제공합니다. 정확한 진단과 치료는 반드시 의료 전문가와 상담하시기 바랍니다.
