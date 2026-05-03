"""
execute_order_node.py — Final order execution via service layer (Async).
"""
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from app.agent.state import State
from app.services.order_service import create_order, UserNotFoundError, ServiceError
from app.agent.prompts.prompts import (
    EXECUTE_UNREGISTERED_MSG,
    EXECUTE_SERVICE_ERROR_MSG,
    EXECUTE_GENERIC_ERROR_MSG,
    EXECUTION_FALLBACK_MSG,
    SYSTEM_ORDER_CREATED
)
from app.agent.nodes.node_utils import prepare_node_context
from app.core.llm_client import llm
from app.core.config import settings


async def execute_order_node(state: State, config: RunnableConfig) -> dict:
    """Submit the validated order to the service layer and generate a natural response."""
    user_id = config.get("configurable", {}).get("user_id", "guest")

    # 1. Final Attempt
    try:
        order = await create_order(
            user_id=user_id,
            items=state.get("items", []),
            delivery_address=state.get("delivery_address", "").strip(),
            payment_method=state.get("payment_method", "").lower(),
        )
        # SUCCESS
        success_txt = SYSTEM_ORDER_CREATED.format(order_id=order.id)
        final_msg = AIMessage(content=success_txt)
        
        return {
            "order_status": "created",
            "order_error": None,
            "order_id": order.id,
            "messages": [final_msg],
            "items": [],
            "delivery_address": None,
            "payment_method": None,
            "clean_items": [],
            "total": 0,
            "validation_errors": [],
            "pending_user_input": "",
            "intent": "INFO", # Reset to INFO after terminal state
        }

    except UserNotFoundError:
        order_error = EXECUTE_UNREGISTERED_MSG
    except ServiceError as e:
        order_error = EXECUTE_SERVICE_ERROR_MSG.format(error=e)
    except Exception as e:
        order_error = EXECUTE_GENERIC_ERROR_MSG.format(error=e)

    # 2. ERROR Handling (Dynamic LLM Response)
    temp_state = dict(state)
    temp_state["order_status"] = "error"
    temp_state["order_error"] = order_error
    
    context = await prepare_node_context(temp_state)
    try:
        response = await llm.bind(temperature=0).with_retry(
            stop_after_attempt=settings.MAX_LLM_RETRIES
        ).ainvoke(context)
    except Exception:
        response = AIMessage(content=EXECUTION_FALLBACK_MSG)

    return {
        "order_status": "in_cart", # Reset status so user can fix issue and retry
        "order_error": order_error,
        "messages": [response],
        "order_id": None
    }