# CheziousBot — Project File Structure

## Overview

This document describes the complete file structure of CheziousBot, a production-grade AI chatbot built with FastAPI and Groq LLM integration.

---

## Directory Structure

```
cheziousbot/
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── chat.py
│   │       ├── sessions.py
│   │       ├── users.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── rate_limiter.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── session.py
│   │   └── migrations/
│   │       └── versions/
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── session.py
│   │   └── message.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── session.py
│   │   ├── user.py
│   │   └── common.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py
│   │   ├── context_service.py
│   │   ├── session_service.py
│   │   └── user_service.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── groq_client.py
│   │   └── prompts.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── ids.py
│       ├── time.py
│       └── streaming.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_chat.py
│   ├── test_sessions.py
│   ├── test_users.py
│   └── test_groq.py
│
├── Docs/
│   ├── prd.md
│   ├── implementation_plan.md
│   ├── specs.md
│   ├── features.md
│   ├── context_management.md
│   ├── file_structure.md
│   ├── chezious_bio.md
│   ├── chezious_branches.md
│   └── menu.md
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## File Details by Layer

### Root Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (secrets, API keys). **Never commit.** |
| `.env.example` | Template for `.env` with placeholder values |
| `.gitignore` | Git ignore patterns (venv, .env, __pycache__, etc.) |
| `requirements.txt` | Python dependencies list |
| `Dockerfile` | Container build instructions |
| `docker-compose.yml` | Local development orchestration |
| `README.md` | Project overview and setup instructions |

---

### `app/` — Application Core

#### Entry Point

| File | Scope | Responsibilities |
|------|-------|------------------|
| `__init__.py` | Package init | Exports app version |
| `main.py` | App bootstrap | Create FastAPI instance, register routers, setup middleware, startup/shutdown events. **No business logic.** |

```python
# main.py scope
- Create FastAPI app
- Register v1 routers
- Setup CORS middleware  
- Add exception handlers
- Database initialization (startup)
- Graceful shutdown
```

---

### `app/api/` — HTTP Layer

> **Rule:** Routes delegate, they don't think. No DB queries or LLM calls here.

#### `app/api/v1/`

| File | Endpoints | Scope |
|------|-----------|-------|
| `__init__.py` | — | Router aggregation |
| `health.py` | `GET /health`, `GET /health/ready` | Health checks, DB/Groq connectivity |
| `sessions.py` | `POST /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}` | Session CRUD operations |
| `users.py` | `GET /users/{user_id}/sessions`, `GET /users/{user_id}/sessions/{id}` | User-specific session queries |
| `chat.py` | `POST /chat` | Chat endpoint with SSE streaming |

```python
# Example: chat.py scope
@router.post("/chat")
async def chat(request: ChatRequest):
    return await chat_service.handle_chat(request)
# No business logic - just delegation
```

---

### `app/core/` — Cross-Cutting Concerns

| File | Scope | Details |
|------|-------|---------|
| `config.py` | App configuration | Pydantic settings: `GROQ_API_KEY`, `DATABASE_URL`, `CONTEXT_WINDOW_SIZE`, etc. |
| `logging.py` | Structured logging | JSON logger with `request_id`, `session_id`, `timestamp` |
| `exceptions.py` | Exception hierarchy | `ChatBotException` base + typed exceptions |
| `rate_limiter.py` | Rate limiting | Per-user request throttling middleware |

```python
# exceptions.py hierarchy
ChatBotException
├── ValidationException       # Invalid input
├── SessionNotFoundException  # Session not found
├── UserNotFoundException     # User not found  
├── GroqAPIException         # LLM API errors
├── DatabaseException        # DB failures
└── RateLimitException       # Rate limit exceeded
```

---

### `app/db/` — Persistence Infrastructure

| File | Scope | Details |
|------|-------|---------|
| `engine.py` | Database engine | SQLModel engine setup with SQLite |
| `session.py` | Session dependency | FastAPI dependency for DB session injection |
| `migrations/` | Schema migrations | Alembic migration scripts |

```python
# session.py - DB dependency pattern
async def get_db():
    async with AsyncSession(engine) as session:
        yield session
```

---

### `app/models/` — Database Models

> **Rule:** If it maps to a table, it lives here. No business logic.

| File | Model | Fields |
|------|-------|--------|
| `user.py` | `User` | `user_id` (PK), `created_at`, `session_count` |
| `session.py` | `ChatSession` | `id` (UUID), `user_id` (FK), `created_at`, `status`, `message_count` |
| `message.py` | `Message` | `id` (UUID), `session_id` (FK), `role`, `content`, `created_at` |

```python
# session.py model example
class ChatSession(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(foreign_key="user.user_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="active")  # active | archived
    message_count: int = Field(default=0)
```

---

### `app/schemas/` — API Contracts

> **Rule:** DB schema ≠ API schema. Keep them separate for flexibility.

| File | Schemas | Purpose |
|------|---------|---------|
| `chat.py` | `ChatRequest`, `ChatResponse` | Chat endpoint contracts |
| `session.py` | `SessionCreate`, `SessionResponse`, `SessionList` | Session API contracts |
| `user.py` | `UserSessionsResponse` | User query responses |
| `common.py` | `ErrorResponse`, `HealthResponse` | Shared response types |

```python
# chat.py schemas
class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(..., max_length=500)

class ChatResponse(BaseModel):
    message_id: UUID
    content: str
```

---

### `app/services/` — Business Logic

> **Rule:** This is where real logic lives. Talks to DB, talks to LLM, raises exceptions.

| File | Scope | Key Methods |
|------|-------|-------------|
| `user_service.py` | User operations | `get_or_create_user()`, `get_user_sessions()` |
| `session_service.py` | Session lifecycle | `create_session()`, `get_session()`, `archive_session()` |
| `context_service.py` | Context management | `get_context_messages()`, `build_messages_for_llm()` |
| `chat_service.py` | Chat orchestration | `handle_chat()` — validates, saves, calls LLM, streams |

```python
# chat_service.py orchestration
async def handle_chat(request: ChatRequest):
    # 1. Validate input
    # 2. Save user message to DB
    # 3. Fetch context (last N messages)
    # 4. Build LLM messages
    # 5. Stream response from Groq
    # 6. Save assistant response
    # 7. Return SSE stream
```

---

### `app/llm/` — LLM Boundary

> **Rule:** If you swap Groq → OpenAI → local LLM, only this folder changes.

| File | Scope | Details |
|------|-------|---------|
| `groq_client.py` | Groq API integration | Async streaming, retries, timeouts, latency logging |
| `prompts.py` | System prompts | Brand info, menu, branches, ordering instructions |

```python
# groq_client.py scope
class GroqClient:
    async def stream_chat(self, messages: list) -> AsyncGenerator:
        # - Initialize stream
        # - Yield tokens
        # - Handle errors
        # - Log latency
```

---

### `app/utils/` — Pure Helpers

> **Rule:** No side effects. No DB. No HTTP. Just pure functions.

| File | Scope | Functions |
|------|-------|-----------|
| `ids.py` | UUID generation | `generate_uuid()`, `generate_request_id()` |
| `time.py` | Time utilities | `utc_now()`, `format_timestamp()` |
| `streaming.py` | SSE helpers | `create_sse_response()`, `stream_tokens()` |

---

### `tests/` — Test Suite

| File | Scope |
|------|-------|
| `conftest.py` | Pytest fixtures (test DB, mock LLM client) |
| `test_chat.py` | Chat flow e2e tests |
| `test_sessions.py` | Session CRUD tests |
| `test_users.py` | User endpoint tests |
| `test_groq.py` | Groq client tests (mocked) |

---

### `Docs/` — Documentation

| File | Content |
|------|---------|
| `prd.md` | Product Requirements Document |
| `implementation_plan.md` | Phased development checklist |
| `specs.md` | Technical specifications, API endpoints |
| `features.md` | Feature list |
| `context_management.md` | Context windowing strategy |
| `file_structure.md` | This file |
| `chezious_bio.md` | Brand info, hours, contact, ordering |
| `chezious_branches.md` | Branch locations |
| `menu.md` | Menu with prices |

---

## Architecture Principles

### 1. Separation of Concerns

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   API       │────▶│  Services   │────▶│   Models    │
│  (routes)   │     │ (business)  │     │    (DB)     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    LLM      │
                    │  (Groq)     │
                    └─────────────┘
```

### 2. Dependency Direction

```
API → Services → Models
         ↓
        LLM
```

- **API** depends on **Services** (never directly on Models)
- **Services** depend on **Models** and **LLM**
- **Models** depend on nothing

### 3. Why This Structure?

> "It enforces separation of concerns, makes failures isolated, and allows swapping infrastructure pieces like the LLM or database without touching business logic."

---

## Quick Reference

| I want to... | Look in... |
|--------------|------------|
| Add a new endpoint | `app/api/v1/` |
| Change LLM settings | `app/core/config.py` |
| Update system prompt | `app/llm/prompts.py` |
| Add a new DB model | `app/models/` |
| Add business logic | `app/services/` |
| Handle a new error type | `app/core/exceptions.py` |
| Add a utility function | `app/utils/` |
