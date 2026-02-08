"""API Key authentication for CheziousBot."""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """
    Verify the API key from request header.
    
    When api_key_enabled is True, requests must include a valid X-API-Key header.
    When disabled, all requests pass through.
    
    Returns:
        The API key if valid, empty string if auth is disabled.
        
    Raises:
        HTTPException: 401 if API key is invalid or missing when auth is enabled.
    """
    if settings.api_key_enabled:
        if not api_key:
            logger.warning("Request without API key rejected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        if api_key != settings.api_key:
            logger.warning("Request with invalid API key rejected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        logger.debug("API key verified")
    return api_key or ""
