from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.database import get_db
from app.services.order_service import get_user_orders, OrderNotFoundError
from app.schemas.order import OrderListResponse, OrderResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{user_id}", response_model=OrderListResponse, status_code=status.HTTP_200_OK)
async def list_orders(user_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch all completed orders for a user."""
    try:
        orders = await get_user_orders(user_id)
        return OrderListResponse(orders=orders)
    except Exception as e:
        logger.error(f"Error fetching orders for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order history."
        )
