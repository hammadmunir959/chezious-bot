"""Session-related endpoints"""

from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.session_service import SessionService
from app.services.context_service import ContextService
from app.schemas.session import SessionCreate, SessionResponse
from app.schemas.chat import MessagesResponse, ChatMessage

router = APIRouter(prefix="/sessions")


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    request: SessionCreate,
    session: AsyncSession = Depends(get_session),
) -> SessionResponse:
    """Create a new chat session."""
    service = SessionService(session)
    chat_session = await service.create_session(request.user_id)

    return SessionResponse(
        id=chat_session.id,
        user_id=chat_session.user_id,
        created_at=chat_session.created_at,
        status=chat_session.status,
        message_count=chat_session.message_count,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_details(
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> SessionResponse:
    """Get session details."""
    service = SessionService(session)
    chat_session = await service.get_session(session_id)

    return SessionResponse(
        id=chat_session.id,
        user_id=chat_session.user_id,
        created_at=chat_session.created_at,
        status=chat_session.status,
        message_count=chat_session.message_count,
    )


@router.get("/{session_id}/messages", response_model=MessagesResponse)
async def get_session_messages(
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> MessagesResponse:
    """Get all messages for a session."""
    session_service = SessionService(session)
    context_service = ContextService(session)

    chat_session = await session_service.get_session(session_id)
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


@router.delete("/{session_id}", response_model=SessionResponse)
async def archive_session(
    session_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> SessionResponse:
    """Archive a session."""
    service = SessionService(session)
    chat_session = await service.archive_session(session_id)

    return SessionResponse(
        id=chat_session.id,
        user_id=chat_session.user_id,
        created_at=chat_session.created_at,
        status=chat_session.status,
        message_count=chat_session.message_count,
    )
