"""Groq API client with streaming support and resilience."""

import time
import asyncio
from typing import AsyncGenerator
from groq import AsyncGroq, RateLimitError, APIStatusError, APIConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.core.config import settings
from app.core.exceptions import GroqAPIException
from app.core.logging import get_logger

logger = get_logger(__name__)


class GroqClient:
    """Async Groq API client with streaming support and automated retries."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        self.max_tokens = settings.groq_max_tokens
        self.temperature = settings.groq_temperature

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIStatusError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, "INFO"),
        reraise=True,
    )
    async def _create_chat_completion(self, messages: list[dict[str, str]], stream: bool = True):
        """Internal helper to create chat completion with retries."""
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=stream,
        )

    async def stream_chat(
        self, messages: list[dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion tokens from Groq API with resilience.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Yields:
            Token strings as they arrive

        Raises:
            GroqAPIException: If API call fails after retries
        """
        start_time = time.perf_counter()
        first_token_time: float | None = None
        total_tokens = 0

        try:
            # The retry decorator handles RateLimit and Connection errors
            stream = await self._create_chat_completion(messages, stream=True)

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

        except (RateLimitError, APIStatusError, APIConnectionError) as e:
            logger.error(f"Groq API persistent error: {e}", exc_info=True)
            raise GroqAPIException(
                message=f"Groq service is currently unavailable or overloaded: {str(e)}",
                details={"model": self.model, "error_type": type(e).__name__},
            )
        except Exception as e:
            logger.error(f"Unexpected Groq client error: {e}", exc_info=True)
            raise GroqAPIException(
                message=f"An unexpected error occurred while communicating with Groq: {str(e)}",
                details={"model": self.model},
            )

    async def get_completion(self, messages: list[dict[str, str]]) -> str:
        """
        Get a complete (non-streaming) response with retries.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Complete response text
        """
        try:
            response = await self._create_chat_completion(messages, stream=False)
            return response.choices[0].message.content or ""
        except Exception as e:
            # Fallback to streaming implementation if direct completion fails unexpectedly
            # and ensure we catch errors there too
            tokens: list[str] = []
            async for token in self.stream_chat(messages):
                tokens.append(token)
            return "".join(tokens)


# Lazy singleton holder
_groq_client: GroqClient | None = None


def get_groq_client() -> GroqClient:
    """Get or create the Groq client instance."""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client


# For backwards compatibility
groq_client = get_groq_client
