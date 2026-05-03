# app/agent/order_subgraph/nodes/confirm_node.py
from langchain_core.messages import AIMessage, HumanMessage
from app.agent.state import State
from app.utils.utils import compute_total
from app.utils.knowledge_base import search
import json

from app.agent.prompts.prompts import SYSTEM_ORDER_CANCELLED


_INFO_KEYWORDS = ["menu", "what", "options", "prices", "available", "do you have", "show me"]

def _is_inline_info_query(text: str) -> bool:
    t = text.lower().strip()
    return any(kw in t for kw in _INFO_KEYWORDS)

async def confirm_node(state: State) -> dict:
    """Analyze user response to order summary via keyword. Handle inline info queries (Async)."""
    user_input  = state.get("pending_user_input", "")
    retries     = state.get("retries", 0)
    clean_items = state.get("clean_items", [])
    all_errors  = state.get("validation_errors", [])

    if not user_input:
        user_input = "confirm" # safety fallback

    # 1. Handle Inline Info Queries mid-confirmation (Loop on itself)
    if _is_inline_info_query(user_input):
        
        menu_data = search("menu", None)
        menu_txt = json.dumps(menu_data, indent=2, ensure_ascii=False) if menu_data else "Menu unavailable."
        
        return {
            "order_status": "awaiting_confirmation",
            "messages": [
                HumanMessage(content=user_input),
                AIMessage(content=f"System: [MENU INFO]\n{menu_txt}"),
            ],
            "last_analysis": {"decision": "info", "modifications": "User asked for info mid-confirmation."},
            "retries": retries + 1,
            "items":   clean_items,
            "total":   compute_total(clean_items),
            "pending_user_input": "", 
        }

    # 2. Determine Decision cleanly without LLM overhead
    ui_lower = user_input.lower().strip()
    decision = "edit"

    if ui_lower in ("confirm", "yes", "ok", "place order", "go ahead"):
        decision = "confirm"
    
    elif ui_lower in ("cancel", "stop", "abort", "no nevermind"):
        decision = "cancel"

    if all_errors and decision == "confirm":
        decision = "edit" 

    # 3. Handle Cancellation
    if decision == "cancel":
        return {
            "order_status":     "cancelled",
            "order_error":      None,
            "items":            [],
            "clean_items":      [],
            "delivery_address": None,
            "payment_method":   None,
            "validation_errors": [],
            "last_analysis":    {"decision": "cancel", "modifications": None},
            "total":            0,
            "messages": [
                HumanMessage(content=user_input),
                AIMessage(content=SYSTEM_ORDER_CANCELLED),
            ],
            "intent": "INFO", # Reset to INFO after cancellation
        }

    # 4. Handle Confirm / Edit
    return {
        "order_status":  "confirmed" if decision == "confirm" else "extracting",
        "messages":      [HumanMessage(content=user_input)],
        "last_analysis": {"decision": decision, "modifications": user_input if decision == "edit" else None},
        "retries":       retries + 1,
        "items":         clean_items,
        "total":         compute_total(clean_items) if not all_errors else state.get("total", 0),
    }