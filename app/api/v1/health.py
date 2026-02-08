"""Health check endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_session
from app.schemas.common import HealthResponse, ReadyResponse
from app.utils.time import utc_now
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=utc_now(),
        version=settings.app_version,
    )


@router.get("/health/ready", response_model=ReadyResponse)
async def readiness_check(
    session: AsyncSession = Depends(get_session),
) -> ReadyResponse:
    """
    Readiness check including database and Groq connectivity.
    """
    db_status = "ok"
    groq_status = "ok"

    # Check database
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    # Check Groq API (lightweight check - just verify client is configured)
    try:
        from app.llm.groq_client import groq_client
        if not groq_client.client:
            groq_status = "error"
    except Exception:
        groq_status = "error"

    overall_status = "ready" if db_status == "ok" and groq_status == "ok" else "not_ready"

    return ReadyResponse(
        status=overall_status,
        timestamp=utc_now(),
        database=db_status,
        groq=groq_status,
    )
