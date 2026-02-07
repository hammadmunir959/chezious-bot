"""User service for managing user operations"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.exceptions import UserNotFoundException
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, user_id: str) -> User:
        """
        Get existing user or create a new one.

        Args:
            user_id: The username/user_id string

        Returns:
            User instance
        """
        # Try to get existing user
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            logger.debug(f"Found existing user: {user_id}")
            return user

        # Create new user
        user = User(user_id=user_id)
        self.session.add(user)
        await self.session.flush()

        logger.info(f"Created new user: {user_id}")
        return user

    async def get_user(self, user_id: str) -> User:
        """
        Get a user by ID.

        Args:
            user_id: The username/user_id string

        Returns:
            User instance

        Raises:
            UserNotFoundException: If user doesn't exist
        """
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundException(user_id)

        return user

    async def increment_session_count(self, user_id: str) -> None:
        """Increment the user's session count."""
        user = await self.get_user(user_id)
        user.increment_session_count()
        await self.session.flush()
