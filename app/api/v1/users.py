"""User-related endpoints"""

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.session_service import SessionService
from app.services.context_service import ContextService
from app.schemas.user import UserSessionsResponse, UserSessionSummary
from app.schemas.session import SessionResponse
from app.schemas.chat import MessagesResponse, ChatMessage

router = APIRouter(prefix="/users")


@router.get("/{user_id}/sessions", response_model=UserSessionsResponse)
async def get_user_sessions(
    user_id: str,
    session: AsyncSession = Depends(get_session),
) -> UserSessionsResponse:
    """Get all sessions for a user."""
    service = SessionService(session)
    sessions = await service.get_user_sessions(user_id)

    return UserSessionsResponse(
        user_id=user_id,
        sessions=[
            UserSessionSummary(
                id=s.id,
                created_at=s.created_at,
                status=s.status,
                message_count=s.message_count,
            )
            for s in sessions
        ],
    )


@router.get("/{user_id}/sessions/{session_id}", response_model=SessionResponse)
async def get_user_session(
    user_id: str,
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> SessionResponse:
    """Get a specific session for a user."""
    service = SessionService(session)
    chat_session = await service.get_user_session(user_id, session_id)

    return SessionResponse(
        id=chat_session.id,
        user_id=chat_session.user_id,
        created_at=chat_session.created_at,
        status=chat_session.status,
        message_count=chat_session.message_count,
    )


@router.get(
    "/{user_id}/sessions/{session_id}/messages",
    response_model=MessagesResponse,
)
async def get_user_session_messages(
    user_id: str,
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> MessagesResponse:
    """Get all messages for a user's session."""
    session_service = SessionService(session)
    context_service = ContextService(session)

    # Verify session belongs to user
    chat_session = await session_service.get_user_session(user_id, session_id)

    # Get messages
    messages = await context_service.get_session_messages(session_id)

    return MessagesResponse(
        session_id=chat_session.id,
        user_id=chat_session.user_id,
        messages=[
            ChatMessage(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )
