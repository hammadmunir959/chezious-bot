from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderItemResponse(BaseModel):
    """Schema for a single item in a completed order."""
    item_name: str
    qty: int
    price: int
    total: int

class OrderResponse(BaseModel):
    """Schema for full order details."""
    id: str
    user_id: str
    status: str
    payment_method: str
    created_at: datetime
    delivery_address: Optional[str]
    total_bill: int
    items: List[OrderItemResponse]

class OrderListResponse(BaseModel):
    """Schema for a list of orders."""
    orders: List[OrderResponse]
