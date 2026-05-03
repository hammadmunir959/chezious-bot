from typing import Any, List, Literal, Optional
from langgraph.graph import MessagesState
from app.schemas.agent import MenuItem

# Canonical order lifecycle statuses
ORDER_STATUSES = Literal[
    "in_cart",                 # Items being collected
    "extracting",              # Re-extracting after edit / correction
    "validating",              # Cart validation in progress
    "awaiting_confirmation",   # Summary shown, waiting for user
    "confirmed",                 # User confirmed, about to execute
    "created",                 # Order placed in DB
    "cancelled",               # User cancelled
    "error",                   # Node failed — agent_node translates
]

class State(MessagesState):
    """
    Conversation state for CheziousBot.
    Inherits `messages` from MessagesState.
    """
    
    # NEW — multi-channel fields
    channel: str = "web"             # web | whatsapp | mobile | instagram
    language: str = "en"             # en | ur

    # Intent classification (classify_intent_node)
    reasoning: Optional[str] = None
    intent: Optional[str] = None  # "ORDER" | "INFO" | "SPAM"

    # Info retrieval (info_node)
    info_data: Optional[str] = None

    # Conversation memory (summarize_node)
    summary: str = ""
    last_summarized_index: int = 0

    # Order lifecycle
    order_status: Optional[ORDER_STATUSES] = None
    order_error: Optional[str] = None

    # Order fields (shared with order subgraph via checkpoint)
    order_id: Optional[str] = None
    items: List[MenuItem] = []
    total: int = 0
    delivery_address: Optional[str] = None
    payment_method: Optional[Literal["cash", "card", "online"]] = None
    last_analysis: Optional[Any] = None  # ConfirmationAnalysis schema or dict
    retries: int = 0

    # Validation pipeline (validate_node → extract_node)
    validation_passed: bool = False
    validation_errors: List[str] = []
    clean_items: List[MenuItem] = []
    pending_user_input: str = ""
