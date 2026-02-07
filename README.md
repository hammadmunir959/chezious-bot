# CheziousBot

A production-ready AI-powered chatbot for Cheezious, Pakistan's popular pizza brand. Built with FastAPI and Groq LLM for fast, streaming responses.

## Overview

CheziousBot is designed to handle customer queries about menu items, pricing, branch locations, operating hours, and ordering assistance. The system uses a lightweight LLM with server-sent events (SSE) for real-time streaming responses.

## Features

- **Real-time Streaming**: Token-by-token responses via Server-Sent Events
- **LLM Integration**: Groq API with llama-3.1-8b-instant model
- **Session Management**: UUID-based sessions with persistent conversation history
- **User Tracking**: Simple username-based identification for conversation retrieval
- **Context Management**: Sliding window approach for conversation context
- **Rate Limiting**: Configurable per-user request throttling
- **Structured Logging**: JSON-formatted logs with request tracking

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| LLM Provider | Groq |
| Database | SQLite with SQLModel |
| Streaming | SSE (Server-Sent Events) |
| Containerization | Docker |

## Quick Start

### Prerequisites

- Python 3.10+
- Groq API key ([get one here](https://console.groq.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/hammadmunir959/chezious-bot.git
cd chezious-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### CLI Client

```bash
python3 cli.py
```

## API Reference

### Health Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Basic health check |
| GET | `/api/v1/health/ready` | Readiness check with DB and Groq status |

### Session Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sessions` | Create a new chat session |
| GET | `/api/v1/sessions/{id}` | Get session details |
| GET | `/api/v1/sessions/{id}/messages` | Get all messages in a session |
| DELETE | `/api/v1/sessions/{id}` | Archive a session |

### User Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/{user_id}/sessions` | Get all sessions for a user |
| GET | `/api/v1/users/{user_id}/sessions/{id}` | Get specific session for a user |
| GET | `/api/v1/users/{user_id}/sessions/{id}/messages` | Get messages for a user's session |

### Chat Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat` | Send message and receive streaming response |

## Usage Examples

### Create a Session

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
  "created_at": "2024-01-15T10:30:00Z",
  "status": "active",
  "message_count": 0
}
```

### Send a Chat Message

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

event: done
data: {"status": "complete"}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | Required | Groq API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | LLM model identifier |
| `GROQ_MAX_TOKENS` | `512` | Maximum response tokens |
| `GROQ_TEMPERATURE` | `0.6` | Response creativity (0-1) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./cheziousbot.db` | Database connection string |
| `CONTEXT_WINDOW_SIZE` | `10` | Number of messages to include in context |
| `RATE_LIMIT_PER_MINUTE` | `20` | Maximum requests per user per minute |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Project Structure

```
chezious-bot/
├── app/
│   ├── api/v1/          # API route handlers
│   ├── core/            # Configuration, logging, exceptions
│   ├── db/              # Database engine and session management
│   ├── models/          # SQLModel database models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic layer
│   ├── llm/             # Groq client and prompts
│   ├── utils/           # Helper utilities
│   └── main.py          # Application entry point
├── Docs/                # Project documentation
├── cli.py               # Command-line interface client
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

## Documentation

Detailed documentation is available in the `Docs/` directory:

- `prd.md` - Product Requirements Document
- `specs.md` - Technical Specifications
- `features.md` - Feature List
- `file_structure.md` - Detailed File Structure
- `context_management.md` - Context Management Strategy
- `implementation_plan.md` - Development Phases

## License

MIT License
