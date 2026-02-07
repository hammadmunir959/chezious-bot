# Product Requirements Document (PRD)

## CheziousBot — AI‑Powered Food Business Chatbot

---

## 1. Executive Summary

CheziousBot is a **production‑grade AI chatbot** designed for Chezious, a food business, to handle customer queries such as menu details, business hours, ordering guidance, and general assistance. The chatbot prioritizes **speed, reliability, and engineering discipline** over unnecessary model complexity.

The system leverages **Groq’s ultra‑fast inference** with a carefully chosen lightweight LLM to ensure sub‑second responses while operating safely within free‑tier rate limits. The project is scoped as a **weekend build**, but architected to reflect real‑world backend engineering standards.

---

## 2. Problem Statement

Food businesses often face:

* Repetitive customer queries (menu, hours, location)
* Delayed responses during peak hours
* No persistent conversational memory

CheziousBot addresses this by acting as a **first‑line conversational interface**, reducing manual load while improving customer experience.

---

## 3. Design Principles (Reasoned Decisions)

### 3.1 Model Selection Philosophy

**Assumption tested:** Bigger models = better chatbot ❌

Reality:

* Food chatbots require **clarity, speed, and correctness**, not deep reasoning
* Large context windows waste tokens and increase latency
* Free‑tier Groq limits demand **token efficiency**

**Decision:** Use a fast, small, instruction‑tuned model optimized for chat.

➡ **Selected Model:** `llama-3.1-8b-instant`

**Why:**

* Sub‑500ms first‑token latency
* Excellent streaming performance
* More than sufficient conversational intelligence
* Token‑efficient and free‑tier safe

---

### 3.2 Context Strategy

**Assumption tested:** Full conversation history improves quality ❌

Reality:

* Older messages often degrade relevance
* Token limits are a real constraint

**Decision:**

* Use **last N messages (default = 10)**
* Design for future summarization (not implemented in v1)

---

## 4. Goals & Success Metrics

### 4.1 Goals

* Deliver **sub‑second streaming responses**
* Maintain **contextual continuity** per session
* Ensure **zero unhandled exceptions**
* Persist all conversations reliably
* Follow real‑world backend engineering standards

### 4.2 Success Metrics

| Metric                  | Target  |
| ----------------------- | ------- |
| First token latency     | < 500ms |
| Typical response time   | < 2s    |
| Unhandled exceptions    | 0       |
| Conversations persisted | 100%    |
| API uptime              | 99%     |

---

## 5. Technology Stack

### Backend

* **FastAPI** — async, high‑performance API
* **Python 3.10+**

### Data Layer

* **SQLModel** — ORM + Pydantic integration
* **SQLite** — lightweight persistence 
* **Alembic** — schema migrations

### AI Integration

* **Groq API** — fast LLM inference
* **Streaming (SSE)** — token‑by‑token delivery

### Engineering

* Structured JSON logging
* Typed exception hierarchy
* Full type hints

---

## 6. High‑Level Architecture

```
Client (Web / Mobile)
        │
        ▼
FastAPI Application
  ├── API Layer
  ├── Business Logic
  ├── Context Manager
  ├── Exception Handling
  ├── Logging
        │
        ├── SQLite Database
        └── Groq API (LLM)
```

---

## 7. Core Features

### 7.1 Streaming Chat Responses (P0)

**Description:**
Responses are streamed token‑by‑token for real‑time UX.

**Acceptance Criteria:**

* SSE‑based streaming
* First token < 500ms
* Graceful stream termination
* Error‑safe interruption handling

---

### 7.2 Context‑Aware Conversations (P0)

**Description:**
Bot uses recent messages to generate relevant responses.

**Rules:**

* Fetch last N messages per session
* Enforce strict context window limits
* Handle truncation safely

---

### 7.3 Session Management (P0)

**Capabilities:**

* UUID‑based session creation
* Persistent session storage
* Session history retrieval

---

### 7.4 User-Based Tracking (P0)

**Description:**
Simple username-based user identification without authentication.

**Capabilities:**

* Get all conversations for a user via `user_id`
* Get specific conversation using `user_id` + `session_id`
* Automatic user creation on first session
* No authentication or authorization required

---

### 7.5 Food Business Knowledge (P1)

**Bot understands:**

* Menu items & prices
* Business hours
* Location & contact info
* Ordering instructions

**Implementation:**

* Static system prompt
* Config‑driven updates (no code change)

---

## 8. Non‑Functional Requirements

### 8.1 Performance

* Async endpoints only
* DB queries < 100ms (P95)
* Efficient token usage

---

### 8.2 Reliability

**Exception Strategy:**

```python
ChatBotException
 ├── ValidationException
 ├── SessionNotFoundException
 ├── GroqAPIException
 ├── DatabaseException
 └── RateLimitException
```

* No raw exceptions leak to client
* All errors logged with request_id

---

### 8.3 Logging

**Structured JSON logs include:**

* timestamp
* request_id
* session_id
* user_id (optional)
* log level
* message

Sensitive data excluded by default.

---

### 8.4 Security

* Input validation via Pydantic
* Max message length enforced
* Per‑user rate limiting
* API key protection

---

## 9. Data Models

### User

```python
user_id: str (PK)  # Simple username, e.g., "john_doe"
created_at: datetime
session_count: int
```

> **Note:** No authentication. `user_id` is just a username string.

### ChatSession

```python
id: UUID (PK)
user_id: str (FK)  # Links to User
created_at: datetime
status: active | archived
message_count: int
```

### Message

```python
id: UUID (PK)
session_id: UUID (FK)
role: user | assistant
content: str
created_at: datetime
```

---

## 10. Groq Configuration

```env
GROQ_MODEL=llama-3.1-8b-instant
GROQ_MAX_TOKENS=512
GROQ_TEMPERATURE=0.6
```

**Reasoning:**

* Fastest streaming
* Stable chat behavior
* Token‑efficient for free tier

---

## 11. Risks & Mitigation

| Risk                | Mitigation           |
| ------------------- | -------------------- |
| Groq rate limits    | Token caps, retries  |
| Context overflow    | Message windowing    |
| SQLite bottleneck   | Clear migration path |
| Model hallucination | Low temperature      |

---

## 12. Out‑of‑Scope (Explicit)

* Payment processing
* Order placement
* Multilingual support
* Image / voice input

---

## 13. Future Enhancements

* Context summarization
* PostgreSQL migration
* Redis caching
* Admin dashboard
* Multi‑model routing

---

## 14. Final Verdict

CheziousBot is intentionally **simple, fast, and reliable**.

The system favors **engineering correctness over model hype**, making it suitable for real food businesses and defensible in technical interviews.

---

