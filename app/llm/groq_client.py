"""Groq API client with streaming support"""

import time
from typing import AsyncGenerator
from groq import AsyncGroq

from app.core.config import settings
from app.core.exceptions import GroqAPIException
from app.core.logging import get_logger

logger = get_logger(__name__)


class GroqClient:
    """Async Groq API client with streaming support."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        self.max_tokens = settings.groq_max_tokens
        self.temperature = settings.groq_temperature

    async def stream_chat(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion tokens from Groq API.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Yields:
            Token strings as they arrive

        Raises:
            GroqAPIException: If API call fails
        """
        start_time = time.perf_counter()
        first_token_time: float | None = None
        total_tokens = 0

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content

                    # Track first token latency
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                        latency = (first_token_time - start_time) * 1000
                        logger.info(
                            f"First token latency: {latency:.0f}ms",
                            extra={"first_token_latency_ms": latency},
                        )

                    total_tokens += 1
                    yield token

            # Log completion stats
            total_time = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"Stream complete: {total_tokens} tokens in {total_time:.0f}ms",
                extra={
                    "total_tokens": total_tokens,
                    "total_time_ms": total_time,
                },
            )

        except Exception as e:
            logger.error(f"Groq API error: {e}", exc_info=True)
            raise GroqAPIException(
                message=f"Failed to get response from Groq: {str(e)}",
                details={"model": self.model},
            )

    async def get_completion(self, messages: list[dict[str, str]]) -> str:
        """
        Get a complete (non-streaming) response.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Complete response text

        Raises:
            GroqAPIException: If API call fails
        """
        tokens: list[str] = []
        async for token in self.stream_chat(messages):
            tokens.append(token)
        return "".join(tokens)

# Lazy singleton holder
_groq_client: GroqClient | None = None


def get_groq_client() -> GroqClient:
    """
    Get or create the Groq client instance.
    
    Uses lazy initialization to avoid import-time failures
    and improve testability.
    """
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client


# For backwards compatibility - use as property access
groq_client = get_groq_client
