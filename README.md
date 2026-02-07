# 🍕 CheziousBot

AI-powered chatbot for **Cheezious** — Pakistan's favorite cheese-loaded pizza brand.

Built with **FastAPI** and **Groq LLM** for fast, streaming responses.

---

## Features

- ⚡ **Real-time streaming** responses via SSE
- 🧠 **Groq LLM** integration (llama-3.1-8b-instant)
- 💬 **Session-based** conversation history
- 👤 **User tracking** for personalized conversations
- 📊 **Structured logging** with request tracking
- 🛡️ **Rate limiting** to prevent abuse

---

## Quick Start

### 1. Clone & Setup

```bash
cd Chezious-Bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload
```

The API is now available at **http://localhost:8000**

- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/api/v1/health

---

## API Endpoints

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Basic health check |
| GET | `/api/v1/health/ready` | Readiness check (DB + Groq) |

### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sessions` | Create new session |
| GET | `/api/v1/sessions/{id}` | Get session details |
| GET | `/api/v1/sessions/{id}/messages` | Get session messages |
| DELETE | `/api/v1/sessions/{id}` | Archive session |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/{user_id}/sessions` | Get user's sessions |
| GET | `/api/v1/users/{user_id}/sessions/{id}` | Get specific session |
| GET | `/api/v1/users/{user_id}/sessions/{id}/messages` | Get messages |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Send message (SSE streaming) |

---

## Usage Example

### 1. Create a Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john_doe"}'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "john_doe",
  "status": "active"
}
```

### 2. Send a Chat Message

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What pizzas do you have?"
  }'
```

Response (SSE stream):
```
event: token
data: {"token": "We"}

event: token
data: {"token": " have"}

event: token
data: {"token": " a"}
...
event: done
data: {"status": "complete"}
```

---

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *required* | Your Groq API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | LLM model |
| `DATABASE_URL` | `sqlite+aiosqlite:///./cheziousbot.db` | Database URL |
| `CONTEXT_WINDOW_SIZE` | `10` | Messages to include in context |
| `RATE_LIMIT_PER_MINUTE` | `20` | Rate limit per user |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Project Structure

```
cheziousbot/
├── app/
│   ├── api/v1/          # API routes
│   ├── core/            # Config, logging, exceptions
│   ├── db/              # Database engine & session
│   ├── models/          # SQLModel models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── llm/             # Groq client & prompts
│   ├── utils/           # Helpers
│   └── main.py          # App entry point
├── Docs/                # Documentation
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## License

MIT
