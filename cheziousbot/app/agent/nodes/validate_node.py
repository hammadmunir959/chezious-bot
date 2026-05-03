"""
validate_node.py — Validates cart and order fields, routing to confirmation or error handling (Async).
"""
from app.agent.state import State
from app.agent.prompts.prompts import (
    ORDER_INTERRUPT_PROMPT, 
    VALIDATE_GENERIC_MSG,
    EXECUTE_UNREGISTERED_MSG,
    EXECUTE_SERVICE_ERROR_MSG,
    EXECUTE_GENERIC_ERROR_MSG,
)
from app.utils.utils import validate_cart, validate_order_fields, compute_total, build_price_map

from app.agent.nodes.node_utils import prepare_node_context
from app.core.llm_client import llm
from langchain_core.messages import AIMessage
from app.core.config import settings


async def validate_node(state: State) -> dict:
    """Validate cart + fields. Explains errors naturally via LLM if they exist."""
    items   = state.get("items", [])
    address = state.get("delivery_address")
    payment = state.get("payment_method")

    # 1. Component Validation
    pm, sb = build_price_map()
    cart_errors, clean_items = validate_cart(items, pm, sb)
    field_errors              = validate_order_fields(address, payment)
    all_errors                = cart_errors + field_errors

    # 2. Extract Warnings (carried forward)
    from langchain_core.messages import HumanMessage
    messages = state.get("messages", [])
    last_human_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage):
            last_human_idx = i
            break
    
    fresh_messages = messages[last_human_idx + 1:] if last_human_idx != -1 else messages
    item_warnings = [
        m.content.replace("System: ", "⚠️  ")
        for m in fresh_messages
        if hasattr(m, "content") and (m.content or "").startswith("System:")
        and ("not on our menu" in m.content or "removed" in m.content)
    ]

    # 3. Handle Failures Naturallly
    if all_errors:
        return {
            "order_status":       "extracting", # Force stay in extraction loop
            "validation_errors":  all_errors + item_warnings,
            "validation_passed":  False,
            "pending_user_input": "",
        }

    # 4. Success State
    total = compute_total(clean_items)
    return {
        "order_status":       "awaiting_confirmation",
        "validation_errors":  item_warnings,
        "clean_items":        clean_items,
        "total":              total,
        "pending_user_input": "",
        "validation_passed":  True,
    }
