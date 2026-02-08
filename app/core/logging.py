"""Structured JSON logging for CheziousBot"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any
from contextvars import ContextVar

from app.core.config import settings

# Context variables for request tracking
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


class ColoredFormatter(logging.Formatter):
    """Human-readable colored formatter for development."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def format(self, record: logging.LogRecord) -> str:
        # Get color for level
        color = self.COLORS.get(record.levelname, "")

        # Format timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Build the log message
        parts = [
            f"{self.DIM}{timestamp}{self.RESET}",
            f"{color}{record.levelname:8}{self.RESET}",
            f"{self.BOLD}{record.name}{self.RESET}",
        ]

        # Add context if present
        context_parts = []
        if request_id := request_id_var.get():
            context_parts.append(f"req={request_id[:8]}")
        if session_id := session_id_var.get():
            context_parts.append(f"session={session_id[:8]}")
        if user_id := user_id_var.get():
            context_parts.append(f"user={user_id}")

        if context_parts:
            parts.append(f"{self.DIM}[{' '.join(context_parts)}]{self.RESET}")

        # Add the actual message
        parts.append(f"→ {record.getMessage()}")

        # Add exception if present
        if record.exc_info:
            parts.append(f"\n{self.formatException(record.exc_info)}")

        return " ".join(parts)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context variables if present
        if request_id := request_id_var.get():
            log_data["request_id"] = request_id

        if session_id := session_id_var.get():
            log_data["session_id"] = session_id

        if user_id := user_id_var.get():
            log_data["user_id"] = user_id

        # Add extra fields from record
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging() -> None:
    """Configure structured logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add handler with appropriate formatter
    handler = logging.StreamHandler(sys.stdout)
    
    # Use colored formatter for development, JSON for production
    if settings.debug:
        handler.setFormatter(ColoredFormatter())
    else:
        handler.setFormatter(JSONFormatter())
        
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class LogContext:
    """Context manager for setting log context variables."""

    def __init__(
        self,
        request_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
    ):
        self.request_id = request_id
        self.session_id = session_id
        self.user_id = user_id
        self._tokens: list = []

    def __enter__(self):
        if self.request_id:
            self._tokens.append(request_id_var.set(self.request_id))
        if self.session_id:
            self._tokens.append(session_id_var.set(self.session_id))
        if self.user_id:
            self._tokens.append(user_id_var.set(self.user_id))
        return self

    def __exit__(self, *args):
        for token in reversed(self._tokens):
            token.var.reset(token)
