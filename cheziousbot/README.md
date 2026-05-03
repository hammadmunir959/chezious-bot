# CheziousBot Production API

A stateful, production-grade AI Agent for Cheezious restaurant, built with **FastAPI** and **LangGraph**.

## Key Features

- **Stateful Conversation**: Powered by LangGraph with persistent checkpointers (SQLite for dev, Redis for prod).
- **Dual LLM Strategy**: Uses **Alibaba Qwen** as primary and **OpenAI GPT-4o-mini** as fallback.
- **Production Infrastructure**:
  - Structured logging.
  - IP-based rate limiting via `slowapi`.
  - Configurable environment variables.
  - Decoupled Service/Agent/API layers.

## Tech Stack

- **Core**: Python 3.11+, FastAPI.
- **Agent**: LangChain, LangGraph.
- **Database**: SQLModel (SQLAlchemy) + SQLite/PostgreSQL.
- **Caching/State**: Redis (optional for dev).
- **Dependency Management**: `uv`.

## Getting Started

1. **Clone the repository**.
2. **Install dependencies**:
   ```bash
   uv sync
   ```
3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```
4. **Initialize Database**:
   ```bash
   uv run python -c "from app.db.database import init_db; init_db()"
   ```
5. **Run the server**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

- `app/core/`: Centralized configurations, LLM client, and logging.
- `app/agent/`: LangGraph definition, nodes, and prompts.
- `app/api/`: FastAPI routes and endpoints.
- `app/services/`: Pure business logic and database interactions.
- `app/models/`: SQLModel database tables.
- `app/schemas/`: Pydantic I/O models.
- `app/utils/`: Shared helper functions and Knowledge Base.
