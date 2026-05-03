from pydantic import BaseModel, Field
from typing import Literal, List, Optional

class ConfirmationAnalysis(BaseModel):
    """Analysis of user's response to an order summary."""
    decision: Literal["confirm", "cancel", "edit"] = Field(
        description="The user's intent: confirm the order, cancel/stop, or edit/change items."
    )
    modifications: Optional[str] = Field(
        default=None,
        description="If decision is 'edit', describe what the user wants to change (e.g., 'add 1 more pizza')."
    )

class IntentClassification(BaseModel):
    """Classify whether the user wants to place an order or get info."""
    
    reasoning : str = Field(
        description="Briefly explain why this intent was chosen"
    )
    
    intent: Literal["ORDER", "INFO", "SPAM"] = Field(
    description=(
        "'ORDER' if the user explicitly wants to place, modify, or cancel an order. "
        "'INFO' for relevant business inquiries (menu, hours, location, policies, or polite greetings). "
        "'SPAM' for nonsensical text, gibberish, offensive content, or topics completely unrelated to the business."
    )
)

class InfoClassification(BaseModel):
    category: Optional[str] = Field(
        default=None,
        description=(
            "Knowledge base category to search: 'menu', 'locations', or 'policies'. "
            "Null for greetings or other irrelevant content."
        )
    )
    query: Optional[str] = Field(
        default=None,
        description=(
            "Short, specific search term to look up within the category (e.g. 'tikka pizza', 'DHA', 'hours'). "
            "Null if the user wants the full category returned (e.g. 'show me the menu')."
        )
    )

class MenuItem(BaseModel):
    """Represents a single item in a cart for validation purposes."""
    item: str = Field(description="Name of the base item (e.g. 'Fajita Pizza'). Do NOT include size.")
    size: Optional[str] = Field(default=None, description="Item size if applicable (e.g., 'Small', 'Large')")
    quantity: int = Field(default=1, description="Number of units for this item", ge=1)
    price: int = Field(default=0, description="Price per unit (populated during validation)", ge=0)

class OrderDetailsSchema(BaseModel):
    """Structured extraction of order details (used by order subgraph)."""
    items: List[MenuItem] = Field(
        default_factory=list,
        description="List of menu items. Each item MUST have 'item' (base name, e.g., 'fajita pizza') and 'quantity'."
    )
    delivery_address: Optional[str] = Field(
        default=None,
        description="The customer's full delivery street address if provided."
    )
    payment_method: Optional[Literal["cash", "card", "online"]] = Field(
        default=None,
        description="The chosen payment method, if provided."
    )
    is_cancelled: bool = Field(
        default=False,
        description="Set to true if the user explicitly asks to cancel or stop the order."
    )
