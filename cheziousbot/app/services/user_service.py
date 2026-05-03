"""
user_service.py — Service layer for user management (Async).
"""

import logging
from typing import Optional
from sqlmodel import select
from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

class UserNotFoundError(Exception): pass

async def get_user(user_id: str) -> Optional[User]:
    async with AsyncSessionLocal() as session:
        return await session.get(User, user_id)

async def get_or_404(user_id: str) -> User:
    user = await get_user(user_id)
    if not user:
        # For the prototype, we auto-create if missing to lower friction
        import re
        digits = re.sub(r"\D", "", user_id)
        guest_phone = f"03{digits[:9]}" if digits else f"03{str(abs(hash(user_id)))[:9]}"
        return await create_user(UserCreate(name="Guest", phone=guest_phone), user_id=user_id)
    return user

async def create_user(user_data: UserCreate, user_id: str = None) -> User:
    async with AsyncSessionLocal() as session:
        user = User(
            id=user_id,
            name=user_data.name,
            phone=user_data.phone
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"User created: {user.id}")
        return user
