"""
extract_node.py — Lean orchestrator for order extraction (Async).
Refactored for readability and separation of concerns.
"""
from langchain_core.messages import AIMessage
from app.core.llm_client import advanced_llm
from app.agent.state import State
from app.agent.prompts.prompts import (
    COLLECT_PROMPT, 
    SYSTEM_ORDER_CANCELLED,
    EXTRACTION_TRAFFIC_MSG,
    EXTRACTION_RETRY_MSG
)
from app.schemas.agent import OrderDetailsSchema
from app.core.config import settings
from app.utils.utils import (
    build_menu_summary, _cart_txt, 
    prepare_extraction_inputs, format_extraction_result
)

# Shared Structured LLM Configuration
_chain = (
    COLLECT_PROMPT | 
    advanced_llm.bind(temperature=0).with_structured_output(OrderDetailsSchema).with_retry(
        stop_after_attempt=settings.MAX_LLM_RETRIES
    )
)

async def extract_node(state: State) -> dict:
    """Extraction Pipeline: Logic -> LLM -> State Updates."""
    
    # 1. State Inspection
    current_status = state.get("order_status")
    new_status = "in_cart" if current_status in (None, "created", "cancelled", "error") else "extracting"

    errors   = state.get("validation_errors", [])
    pending  = state.get("pending_user_input", "")
    cart_txt = _cart_txt(state.get("items", []))
    analysis = state.get("last_analysis", {})

    # 2. Preparation (Logic extracted to utils.py)
    inputs = prepare_extraction_inputs(state, cart_txt, analysis, errors, pending, build_menu_summary())

    # 3. LLM Orchestration
    try:
        # Use ainvoke for async
        extraction = await _chain.ainvoke(inputs)
        if not extraction:
            raise ValueError("Empty extraction from LLM.")
    except Exception as e:
        return _handle_extraction_fail(e)

    # 4. Handle Cancellation (Trusting LLM decision)
    if extraction.is_cancelled:
        return _aborted_result()

    # 5. Result Formatting & Item Resolution
    result = format_extraction_result(state, extraction, pending)
    result["order_status"] = new_status
    result["order_error"] = None
    
    return result


# --- Response Templates ---

def _aborted_result() -> dict:
    """Returns a clean state and a system cancellation message."""
    return {
        "order_status":        "cancelled",
        "order_error":         None,
        "items":               [],
        "delivery_address":    None,
        "payment_method":      None,
        "messages":            [AIMessage(content=f"System: {SYSTEM_ORDER_CANCELLED}")],
        "pending_user_input":  "",
        "validation_passed":   False,
        "last_analysis":       None,
    }

def _handle_extraction_fail(e: Exception) -> dict:
    """Provides a user-friendly error response based on the exception type."""
    error_str = str(e).lower()
    msg = (
        EXTRACTION_TRAFFIC_MSG
        if "rate limit" in error_str else
        EXTRACTION_RETRY_MSG
    )
    return {
        "order_status": "error",
        "order_error": f"extraction_failed: {str(e)}",
        "messages": [AIMessage(content=msg)],
    }