import logging
from typing import List, Optional
from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db.database import AsyncSessionLocal
from app.models.order import Order as OrderModel, OrderItem
from app.models.user import User as UserModel
from app.schemas.agent import MenuItem

logger = logging.getLogger(__name__)

class ServiceError(Exception): pass
class UserNotFoundError(ServiceError): pass
class OrderNotFoundError(ServiceError): pass

async def get_order(order_id: str, user_id: Optional[str] = None) -> OrderModel:
    """Retrieve order with eager-loaded relations, optionally filtered by user."""
    async with AsyncSessionLocal() as session:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        if user_id:
            stmt = stmt.where(OrderModel.user_id == user_id)
        
        result = await session.exec(stmt.options(selectinload(OrderModel.user), selectinload(OrderModel.items)))
        order = result.first()
        if not order:
            raise OrderNotFoundError(f"Order '{order_id}' not found.")
        return order

async def get_user_orders(user_id: str) -> List[OrderModel]:
    """Retrieve all orders for a user."""
    async with AsyncSessionLocal() as session:
        stmt = select(OrderModel).where(OrderModel.user_id == user_id).options(
            selectinload(OrderModel.items)
        ).order_by(OrderModel.created_at.desc())
        
        result = await session.exec(stmt)
        orders = result.all()
        return list(orders)

async def create_order(user_id: str, items: List[MenuItem], delivery_address: str, payment_method: str) -> OrderModel:
    """Create a new order for a user."""
    async with AsyncSessionLocal() as session:
        user = await session.get(UserModel, user_id)
        if not user:
            user = UserModel(id=user_id, name="Guest", phone=f"+920000000{user_id[:4]}")
            session.add(user)
            await session.flush()

        order = OrderModel(
            user_id=user.id,
            status="created",
            payment_method=payment_method.lower(),
            delivery_address=delivery_address.strip(),
        )
        
        for itm in items:
            order.items.append(OrderItem(item_name=itm.item, qty=itm.quantity, price=itm.price))

        session.add(order)
        await session.flush()
        order.compute_total()
        await session.commit()
        return await get_order(order.id, user_id=user.id)
