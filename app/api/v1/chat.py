"""Chat endpoint with SSE streaming"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
import json

from app.db.session import get_session
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest
from app.core.rate_limiter import limiter, get_rate_limit_string
from app.core.logging import get_logger, LogContext
from app.utils.ids import generate_request_id

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat")
@limiter.limit(get_rate_limit_string())
async def chat(
    request: Request,
    chat_request: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> EventSourceResponse:
    """
    Send a message and receive a streaming response.

    Returns Server-Sent Events (SSE) stream with tokens.
    """
    request_id = generate_request_id()

    with LogContext(
        request_id=request_id,
        session_id=str(chat_request.session_id),
    ):
        logger.info(f"Chat request received: {len(chat_request.message)} chars")

        service = ChatService(session)

        async def event_generator():
            """Generate SSE events from chat response."""
            try:
                async for token in service.handle_chat(
                    chat_request.session_id,
                    chat_request.message,
                ):
                    yield {
                        "event": "token",
                        "data": json.dumps({"token": token}),
                    }

                yield {
                    "event": "done",
                    "data": json.dumps({"status": "complete"}),
                }

            except Exception as e:
                logger.error(f"Chat error: {e}", exc_info=True)
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)}),
                }

        return EventSourceResponse(
            event_generator(),
            media_type="text/event-stream",
        )
