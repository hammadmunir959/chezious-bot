<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
</p>

<h1 align="center">🍕 CheziousBot</h1>

<p align="center">
  <strong>AI-Powered Customer Support Chatbot for Cheezious</strong><br/>
  <em>Real-time streaming responses powered by Groq LLM</em>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-documentation">Documentation</a>
</p>

---

##  Features

<table>
<tr>
<td width="50%">

### AI-Powered Conversations
- Real-time **streaming responses** via SSE
- Sub-500ms first token latency
- Context-aware (remembers last 10 messages)
- Powered by **Groq's ultra-fast inference**

</td>
<td width="50%">

###  Session Management
- UUID-based session creation
- Persistent message history
- Session archiving & restoration
- Multi-session support per user

</td>
</tr>
<tr>
<td width="50%">

### Business Knowledge
- Complete menu with prices & sizes
- Branch locations across Pakistan
- Operating hours & delivery info
- Payment methods & ordering guidance

</td>
<td width="50%">

### 🛡️ Production-Ready
- Rate limiting per user
- Structured JSON logging
- Request tracing via `request_id`
- Typed exception handling

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Groq API Key** — [Get one free](https://console.groq.com)

### Installation

```bash
# Clone the repository
git clone https://github.com/hammadmunir959/chezious-bot.git
cd chezious-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Run the Server

```bash
uvicorn app.main:app --reload
```

<table>
<tr>
<td>🌐 <strong>API Server</strong></td>
<td><code>http://localhost:8000</code></td>
</tr>
<tr>
<td>📚 <strong>Swagger Docs</strong></td>
<td><code>http://localhost:8000/docs</code></td>
</tr>
<tr>
<td>❤️ <strong>Health Check</strong></td>
<td><code>http://localhost:8000/api/v1/health</code></td>
</tr>
</table>

### CLI Client

Interactive terminal client for testing:

```bash
python3 scripts/cli.py
```

---

## 📡 API Reference

### Health Endpoints

| Method | Endpoint | Description |
|:------:|----------|-------------|
| `GET` | `/api/v1/health` | Basic health check |
| `GET` | `/api/v1/health/ready` | Readiness check (DB + LLM status) |

### Session Endpoints

| Method | Endpoint | Description |
|:------:|----------|-------------|
| `POST` | `/api/v1/sessions` | Create new chat session |
| `GET` | `/api/v1/sessions/{id}` | Get session details |
| `GET` | `/api/v1/sessions/{id}/messages` | Get session messages |
| `DELETE` | `/api/v1/sessions/{id}` | Archive session |

### User Endpoints

| Method | Endpoint | Description |
|:------:|----------|-------------|
| `GET` | `/api/v1/users/{user_id}/sessions` | Get all user sessions |
| `GET` | `/api/v1/users/{user_id}/sessions/{id}` | Get specific session |
| `GET` | `/api/v1/users/{user_id}/sessions/{id}/messages` | Get session messages |

### Chat Endpoint

| Method | Endpoint | Description |
|:------:|----------|-------------|
| `POST` | `/api/v1/chat` | Send message (SSE streaming response) |

---

## 💡 Usage Examples

### Create a Session

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john_doe", "city": "lahore"}'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "john_doe",
  "city": "lahore",
  "created_at": "2026-02-08T10:30:00Z",
  "status": "active"
}
```

### Send a Message

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "What pizzas do you have?"
  }'
```

**SSE Response Stream:**
```
event: token
data: {"token": "We"}

event: token
data: {"token": " have"}

event: token
data: {"token": " many"}

event: done
data: {"status": "complete"}
```

---

## ⚙️ Configuration

All settings via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *Required* | Your Groq API key |
| `GROQ_MODEL` | `llama-3.1-8b-instant` | LLM model identifier |
| `GROQ_MAX_TOKENS` | `512` | Max response tokens |
| `GROQ_TEMPERATURE` | `0.6` | Creativity (0-1) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./cheziousbot.db` | Database connection |
| `CONTEXT_WINDOW_SIZE` | `10` | Messages in context |
| `RATE_LIMIT_PER_MINUTE` | `20` | Requests per user/min |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 📁 Project Structure

```
chezious-bot/
├── app/                          # Application source code
│   ├── api/                      # API routes & endpoints
│   ├── core/                     # Config, logging, exceptions
│   ├── db/                       # Database connection & session
│   ├── llm/                      # Groq client & context manager
│   ├── models/                   # SQLModel database models
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── services/                 # Business logic layer
│   ├── utils/                    # Utility functions
│   └── main.py                   # FastAPI application entry
├── scripts/                      # CLI tool
├── requirements.txt

```

---

## 🗣️ What Can CheziousBot Answer?

| Category | Example Questions |
|----------|-------------------|
| **Menu** | "What pizzas do you have?" |
| **Prices** | "How much is a large Chicken Tikka?" |
| **Deals** | "What combos are available?" |
| **Hours** | "What time do you close on Friday?" |
| **Contact** | "What's your phone number?" |
| **Locations** | "Where is the DHA Lahore branch?" |
| **Ordering** | "How can I place an order?" |
| **Delivery** | "Do you deliver? Is it free?" |
| **Payment** | "Can I pay with JazzCash?" |

---


## 📄 License

MIT License — feel free to use this project for your own business!

---

<p align="center">
  Made with ❤️ for <strong>Cheezious</strong> 🍕
</p>
