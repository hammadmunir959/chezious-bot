"""Resilience and logging middleware."""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

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
            
        except Exception as e:
            # Calculate duration even for failed requests
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"{request.method} {request.url.path} -> CRASHED ({duration:.0f}ms): {e}",
                exc_info=True
            )
            # Re-raise to let the general exception handler handle it, 
            # or it will be caught by ResilienceMiddleware if that's next in the stack.
            raise


class ResilienceMiddleware(BaseHTTPMiddleware):
    """
    Ultimate safety net middleware. 
    Catches any exception that escaped earlier handlers and returns a clean 500 JSON.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                f"Unhandled Exception caught by ResilienceMiddleware: {str(e)}", 
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "A critical system error occurred. Our team has been notified.",
                        "details": {"type": type(e).__name__} if request.app.debug else {}
                    }
                }
            )
