"""SSE (Server-Sent Events) streaming utilities"""

import asyncio
from typing import AsyncGenerator, Any
from sse_starlette.sse import EventSourceResponse


async def create_sse_response(
    generator: AsyncGenerator[str, None],
    media_type: str = "text/event-stream",
) -> EventSourceResponse:
    """Create an SSE response from an async generator."""

    async def event_generator():
        async for token in generator:
            yield {"data": token}
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator(), media_type=media_type)


async def stream_tokens(
    tokens: list[str], delay: float = 0.01
) -> AsyncGenerator[str, None]:
    """Stream tokens with a delay (for testing)."""
    for token in tokens:
        yield token
        await asyncio.sleep(delay)
