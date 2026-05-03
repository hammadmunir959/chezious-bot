"""
session_service.py — Service layer for session management (Async).
"""

import logging
from sqlmodel import select
from app.db.database import AsyncSessionLocal
from app.models.session import Session as SessionModel
from app.models.user import User as UserModel

logger = logging.getLogger(__name__)

class SessionError(Exception):
    """Base class for session service errors."""
    pass

class SessionOwnershipError(SessionError):
    """Raised when a session does not belong to the provided user."""
    pass

class UserNotFoundError(SessionError):
    """Raised when a user is not found during session operations."""
    pass

async def resolve_session_id(session_id: str, user_id: str) -> str:
    """
    Validates if the provided session_id belongs to the user_id.
    """
    try:
        async with AsyncSessionLocal() as session:
            db_session = await session.get(SessionModel, session_id)
            
            if not db_session:
                raise SessionOwnershipError(f"Session '{session_id}' not found.")
            
            if db_session.user_id != user_id:
                logger.warning(f"Session ownership mismatch: Session {session_id} belongs to {db_session.user_id}, but {user_id} tried to access it.")
                raise SessionOwnershipError(f"Session '{session_id}' does not belong to user '{user_id}'.")
            
            return session_id
            
    except SessionOwnershipError:
        raise
    except Exception as e:
        logger.exception(f"Error resolving session {session_id} for user {user_id}")
        raise SessionError(f"Internal error during session resolution: {str(e)}")

async def get_session_id(user_id: str) -> str:
    """
    Generates and persists a new session for the given user.
    """
    try:
        async with AsyncSessionLocal() as session:
            user = await session.get(UserModel, user_id)
            if not user:
                raise UserNotFoundError(f"Cannot create session: User '{user_id}' not found.")
            
            new_session = SessionModel(user_id=user_id)
            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)
            
            logger.info(f"Generated new session {new_session.id} for user {user_id}")
            return new_session.id
            
    except UserNotFoundError:
        raise
    except Exception as e:
        logger.exception(f"Error creating session for user {user_id}")
        raise SessionError(f"Failed to generate session: {str(e)}")

async def resolve_or_create(user_id: str, session_id: str = None) -> str:
    """
    Business logic: if session_id exists, validate it. If not, create one.
    """
    if session_id:
        try:
            return await resolve_session_id(session_id, user_id)
        except SessionOwnershipError:
            logger.info(f"Session {session_id} invalid for user {user_id}. Creating new.")
            return await get_session_id(user_id)
    return await get_session_id(user_id)
