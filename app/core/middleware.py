"""Request logging middleware."""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request duration and status."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and log its details."""
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            
            # Calculate duration in milliseconds
            duration = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration:.0f}ms)"
            )
            return response
            
        except Exception:
            # Calculate duration even for failed requests
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"{request.method} {request.url.path} -> FAILED ({duration:.0f}ms)"
            )
            raise
