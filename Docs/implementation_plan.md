# CheziousBot Implementation Plan

## Project Overview

**CheziousBot** is a production-grade AI chatbot for Chezious (Pakistani pizza brand) handling menu queries, business hours, location info, and ordering guidance using **Groq's ultra-fast LLM inference** with FastAPI backend.

---

## ✅ Documentation Status

All required business information has been researched and added:

| Data | Status | File |
|------|--------|------|
| Business Hours | ✅ Complete | `chezious_bio.md` |
| Contact Info | ✅ Complete | `chezious_bio.md` |
| Ordering Instructions | ✅ Complete | `chezious_bio.md` |
| Delivery Policy | ✅ Complete | `chezious_bio.md` |
| Payment Methods | ✅ Complete | `chezious_bio.md` |
| Menu with Prices | ✅ Complete | `menu.md` |
| Branch Locations | ✅ Complete | `chezious_branches.md` |

---

## Phase 1: Project Foundation & Core Infrastructure

### Objectives
Set up project structure, configuration, and core utilities.

### Tasks

- [ ] **1.1 Project Initialization**
  - [ ] Create project directory structure per `file_structure.txt`
  - [ ] Initialize Python virtual environment
  - [ ] Create `requirements.txt`:
    - `fastapi`, `uvicorn`, `sqlmodel`, `alembic`, `groq`, `pydantic-settings`
  - [ ] Create `.env.example` with environment variables

- [ ] **1.2 Core Configuration (`app/core/`)**
  - [ ] `config.py` — Pydantic settings for Groq, DB, context window
  - [ ] `logging.py` — Structured JSON logger
  - [ ] `exceptions.py` — Custom exception hierarchy
  - [ ] `rate_limiter.py` — Per-user rate limiting

- [ ] **1.3 Utility Functions (`app/utils/`)**
  - [ ] `ids.py` — UUID generation helpers
  - [ ] `time.py` — Timezone-aware datetime utilities
  - [ ] `streaming.py` — SSE streaming response helpers

---

## Phase 2: Database Layer

### Objectives
Implement SQLite persistence with SQLModel ORM.

### Tasks

- [ ] **2.1 Database Engine (`app/db/`)**
  - [ ] `engine.py` — SQLModel engine setup with SQLite
  - [ ] `session.py` — FastAPI dependency for DB session

- [ ] **2.2 Data Models (`app/models/`)**
  - [ ] `user.py` — `User` model (user_id as PK, created_at, session_count)
  - [ ] `session.py` — `ChatSession` model (id, user_id FK, created_at, status, message_count)
  - [ ] `message.py` — `Message` model (id, session_id FK, role, content, created_at)

- [ ] **2.3 Migrations**
  - [ ] Initialize Alembic
  - [ ] Create initial migration
  - [ ] Test migration up/down

---

## Phase 3: LLM Integration

### Objectives
Integrate Groq API with streaming support.

### Tasks

- [ ] **3.1 Groq Client (`app/llm/`)**
  - [ ] `groq_client.py` — Async streaming with retry logic
  - [ ] Measure first-token latency
  - [ ] Handle rate limits gracefully

- [ ] **3.2 Prompt Engineering (`app/llm/prompts.py`)**
  - [ ] Create system prompt embedding:
    - Brand identity from `chezious_bio.md`
    - Full menu with prices from `menu.md`
    - Branch locations from `chezious_branches.md`
    - Business hours, ordering, delivery, payment info
  - [ ] Make prompt config-driven

---

## Phase 4: Business Logic Services

### Objectives
Implement core services layer.

### Tasks

- [ ] **4.1 User Service (`app/services/user_service.py`)**
  - [ ] `get_or_create_user(user_id)` — Create user if not exists
  - [ ] `get_user_sessions(user_id)` — Get all sessions for a user
  - [ ] `get_user_session(user_id, session_id)` — Get specific session

- [ ] **4.2 Session Service (`app/services/session_service.py`)**
  - [ ] `create_session(user_id)`, `get_session()`, `list_sessions()`, `archive_session()`

- [ ] **4.3 Context Service (`app/services/context_service.py`)**
  - [ ] `get_context_messages(session_id, limit=10)`
  - [ ] `build_messages_list()` for LLM API

- [ ] **4.4 Chat Service (`app/services/chat_service.py`)**
  - [ ] Validate input, save messages, stream response, persist assistant reply

---

## Phase 5: API Layer

### Objectives
Expose RESTful endpoints with streaming support.

### Tasks

- [ ] **5.1 Pydantic Schemas (`app/schemas/`)**
  - [ ] Chat, session, and error response schemas

- [ ] **5.2 API Routes (`app/api/v1/`)**
  - [ ] `GET /health` — Health check
  - [ ] `GET /users/{user_id}/sessions` — Get all user sessions
  - [ ] `GET /users/{user_id}/sessions/{session_id}` — Get specific user session
  - [ ] `GET /users/{user_id}/sessions/{session_id}/messages` — Get user session messages
  - [ ] `POST /sessions` — Create session (with user_id)
  - [ ] `GET /sessions/{id}` — Get session
  - [ ] `GET /sessions/{id}/messages` — Get history
  - [ ] `POST /chat` — Streaming chat (SSE)

- [ ] **5.3 Application Setup (`app/main.py`)**
  - [ ] Register routers, CORS, exception handlers
  - [ ] Startup/shutdown events

---

## Phase 6: Testing & Validation

### Objectives
Ensure reliability with comprehensive tests.

### Tasks

- [ ] **6.1 Unit Tests**
  - [ ] Session CRUD, chat flow, Groq client mocking

- [ ] **6.2 Integration Tests**
  - [ ] Streaming, context windowing, error handling

- [ ] **6.3 Performance Validation**
  - [ ] First-token < 500ms, response < 2s

---

## Phase 7: Deployment & Documentation

### Objectives
Production-ready finishing touches.

### Tasks

- [ ] **7.1 Documentation**
  - [ ] `README.md` with setup instructions
  - [ ] API documentation

- [ ] **7.2 Deployment**
  - [ ] `Dockerfile`
  - [ ] `docker-compose.yml`
  - [ ] Production deployment guide

---

## Success Metrics

| Metric | Target |
|--------|--------|
| First token latency | < 500ms |
| Typical response time | < 2s |
| Unhandled exceptions | 0 |
| Conversations persisted | 100% |
| API uptime | 99% |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| API Framework | FastAPI |
| ORM | SQLModel |
| Database | SQLite |
| Migrations | Alembic |
| LLM Provider | Groq API |
| LLM Model | llama-3.1-8b-instant |
| Streaming | SSE |

---

## Out of Scope

- ❌ Payment processing
- ❌ Order placement
- ❌ Multilingual support
- ❌ Image/voice input
