"""
routings.py — Centralized routing logic for CheziousBot unified graph.
"""
from app.agent.state import State
from app.core.config import settings

_MAX_RETRIES = 5

def should_summarize(state: State) -> bool:
    """Calculates if the conversation history exceeds the character threshold."""
    messages = state.get("messages", [])
    if not messages:
        return False
    
    # Calculate approximate "token" count via characters (1 token ~= 4 chars)
    total_chars = sum(len(m.content) if hasattr(m, "content") and m.content else 0 for m in messages)
    return (total_chars / 4) > settings.SUMMARIZE_TOKEN_THRESHOLD


def route_start(state: State) -> str:
    """Check for crystallization/summarization before even starting the turn."""
    if should_summarize(state):
        return "summarize"
    return "classify"


from langgraph.graph import END

def route_after_classify(state: State) -> str:
    """Route based on classified intent, with active cart awareness."""
    intent       = (state.get("intent") or "").upper()
    order_status = state.get("order_status")

    # Active states mean an order is already in progress — always send to extract
    _ACTIVE = {"in_cart", "extracting", "validating", "awaiting_confirmation"}

    if intent == "ORDER" or order_status in _ACTIVE:
        return "extract"
    if intent == "INFO":
        return "info"
    return "chat"


def route_after_extract(state: State) -> str:
    """Route after extraction."""
    status = state.get("order_status")
    # If extraction led to a natural cancellation, we can end the turn there.
    if status == "cancelled":
        return END
    return "validate"





def route_after_interrupt(state: State) -> str:
    """Route after the central interrupt pause."""
    status = state.get("order_status")
    
    # If the user corrected a validation error or edited an order, go back to extract.
    if status == "awaiting_confirmation":
        return "confirm"
        
    return "extract"


def route_after_confirm(state: State) -> str:
    """Route after confirmation, handle confirm/cancel/edit."""
    status  = state.get("order_status")

    # Cancellations are now handled naturally within confirm_node, so we can END.
    if status == "cancelled":
        return END
        
    if status == "confirmed":
        return "execute"
        
    if status == "awaiting_confirmation":
        return "interrupt"

    return "extract"




