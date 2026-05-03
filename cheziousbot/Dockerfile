# Use a specialized uv image for faster builds
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set the working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy only the files needed for dependency installation to leverage Docker caching
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
# Using --frozen to ensure the lockfile is respected
RUN uv sync --frozen --no-install-project --no-dev

# Final stage
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application code (respecting .dockerignore)
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application
# Using uvicorn directly from the venv
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
