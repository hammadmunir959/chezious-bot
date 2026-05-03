"""
interrupt_node.py — Centralized handler for order-related conversational interrupts (Async).
"""
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import interrupt
from app.agent.state import State
from app.agent.prompts.prompts import SYSTEM_ORDER_CANCELLED
from app.agent.nodes.node_utils import handle_interrupt
from app.utils.utils import compute_total

async def interrupt_node(state: State) -> dict:
    """
    Evaluates state for errors or confirmation prompts and triggers an LLM-driven or raw conversational interrupt.
    Returns the user's correction or handles explicit cancellation.
    """
    order_status = state.get("order_status")
    
    # 1. Handle explicit Confirmation interrupts
    if order_status == "awaiting_confirmation":
        address = state.get("delivery_address")
        payment = state.get("payment_method")
        clean_items = state.get("clean_items", [])
        
        items_txt = "\n".join(
            f"  {i.quantity}x {i.item}{f' ({i.size})' if i.size else ''} — ₨{i.price * i.quantity}"
            for i in clean_items
        ) or "None"
        total = compute_total(clean_items)
        
        # Inject warnings if present
        warnings = state.get("validation_errors", [])
        warnings_formatted = "\n".join(warnings) + "\n\n" if warnings else ""
        
        summary = (
            f"{warnings_formatted}"
            f" Order Summary\n"
            f"{items_txt}\n"
            f"  ─────────────────\n"
            f"  Total:    ₨{total}\n"
            f"  Address:  {address}\n"
            f"  Payment:  {payment}\n\n"
            f"Reply 'confirm' to place, 'edit' to change, or 'cancel' to abort."
        )
        user_response = interrupt(summary)
        
    # 2. Handle Error interrupts
    else:
        errors = state.get("validation_errors", [])
        if not errors:
            return {} # Defensive fail-safe
            
        issue_text = "\n".join(errors)
        # await the async helper
        user_response = await handle_interrupt(state, issue_text)
    
    # Handle explicit cancellation for BOTH flows
    if isinstance(user_response, str) and user_response.lower().strip() == "cancel":
        return {
            "order_status":        "cancelled",
            "order_error":         None,
            "items":               [],
            "delivery_address":    None,
            "payment_method":      None,
            "messages":            [HumanMessage(content=user_response), AIMessage(content=SYSTEM_ORDER_CANCELLED)],
            "pending_user_input":  "",
            "validation_passed":   False,
            "validation_errors":   [],
            "last_analysis":       None,
            "total":               0,
        }
        
    # Resume normal flow, retaining the status so routing knows where to go
    return {
        "pending_user_input": user_response,
        "messages":           [HumanMessage(content=str(user_response))],
        # Intentionally NOT resetting order_status so we can route back accurately
    }
