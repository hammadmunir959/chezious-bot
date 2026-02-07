# CheziousBot — Technical Specifications

## Overview

CheziousBot is a production-grade AI chatbot API for Chezious pizza brand, built with FastAPI and Groq LLM integration.

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.10+ |
| Framework | FastAPI | Latest |
| ORM | SQLModel | Latest |
| Database | SQLite | 3.x |
| Migrations | Alembic | Latest |
| LLM Provider | Groq API | — |
| LLM Model | llama-3.1-8b-instant | — |

---

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Basic health check |
| `GET` | `/health/ready` | Readiness check (DB + Groq) |

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-07T15:00:00Z"
}
```

---

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users/{user_id}/sessions` | Get all sessions for a user |
| `GET` | `/users/{user_id}/sessions/{session_id}` | Get specific session for a user |
| `GET` | `/users/{user_id}/sessions/{session_id}/messages` | Get messages for a user's session |

**Get User Sessions Response:**
```json
{
  "user_id": "john_doe",
  "sessions": [
    {
      "id": "uuid",
      "created_at": "2026-02-07T15:00:00Z",
      "status": "active",
      "message_count": 5
    }
  ]
}
```

---

### Session Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/sessions` | Create new chat session (requires `user_id`) |
| `GET` | `/sessions/{session_id}` | Get session details |
| `GET` | `/sessions/{session_id}/messages` | Get message history |
| `DELETE` | `/sessions/{session_id}` | Archive session |

**Create Session Request:**
```json
{
  "user_id": "john_doe"
}
```

**Create Session Response:**
```json
{
  "id": "uuid",
  "user_id": "john_doe",
  "created_at": "2026-02-07T15:00:00Z",
  "status": "active",
  "message_count": 0
}
```

**Get Messages Response:**
```json
{
  "session_id": "uuid",
  "user_id": "john_doe",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "What's on the menu?",
      "created_at": "2026-02-07T15:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "Here's our menu...",
      "created_at": "2026-02-07T15:00:01Z"
    }
  ]
}
```

---

### Chat Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send message and stream response |

**Request:**
```json
{
  "session_id": "uuid",
  "message": "What pizzas do you have?"
}
```

**Response:** Server-Sent Events (SSE) stream
```
data: {"token": "We"}
data: {"token": " have"}
data: {"token": " a"}
data: {"token": " variety"}
data: {"token": "..."}
data: [DONE]
```

---

## Data Models

### User

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | Primary key (username) |
| `created_at` | datetime | User first seen time |
| `session_count` | int | Total sessions for user |

> **Note:** `user_id` is a simple username string (e.g., `john_doe`). No authentication required.

### ChatSession

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | string | Foreign key to User |
| `created_at` | datetime | Session creation time |
| `status` | string | `active` or `archived` |
| `message_count` | int | Total messages in session |

### Message

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `session_id` | UUID | Foreign key to ChatSession |
| `role` | string | `user` or `assistant` |
| `content` | string | Message text |
| `created_at` | datetime | Message timestamp |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Groq API key (required) |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | LLM model name |
| `GROQ_MAX_TOKENS` | `512` | Max response tokens |
| `GROQ_TEMPERATURE` | `0.6` | Response randomness |
| `DATABASE_URL` | `sqlite:///./cheziousbot.db` | Database connection |
| `CONTEXT_WINDOW_SIZE` | `10` | Messages to include in context |
| `MAX_MESSAGE_LENGTH` | `500` | Max user message length |
| `RATE_LIMIT_PER_MINUTE` | `20` | Requests per user per minute |

---

## Exception Hierarchy

```
ChatBotException (base)
├── ValidationException      # Invalid input
├── SessionNotFoundException # Session doesn't exist
├── GroqAPIException        # LLM API errors
├── DatabaseException       # DB operation failures
└── RateLimitException      # Rate limit exceeded
```

### Error Response Format

```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session with ID xyz not found",
    "request_id": "uuid"
  }
}
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| First token latency | < 500ms |
| Full response time | < 2s |
| DB queries (P95) | < 100ms |
| API uptime | 99% |

---

## Logging Format

Structured JSON logs:

```json
{
  "timestamp": "2026-02-07T15:00:00Z",
  "level": "INFO",
  "request_id": "uuid",
  "session_id": "uuid",
  "message": "Chat request processed",
  "latency_ms": 450
}
```

---

## Security

- Input validation via Pydantic
- Max message length enforced
- Per-user rate limiting
- API key protection (env vars)
- No sensitive data in logs
