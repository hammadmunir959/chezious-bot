"""
node_utils.py — Shared helper logic for agent nodes (Async).
"""
from langgraph.types import interrupt
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import State
from app.core.llm_client import advanced_llm
from app.agent.prompts.prompts import (
    EXECUTE_UNREGISTERED_MSG,
    EXECUTE_SERVICE_ERROR_MSG,
    EXECUTE_GENERIC_ERROR_MSG,
    ORDER_INTERRUPT_PROMPT
)
from app.core.config import settings
from app.utils.utils import build_menu_summary

_interrupt_chain = ORDER_INTERRUPT_PROMPT | advanced_llm

async def prepare_node_context(state: dict) -> list:
    """Combines summary, grounding data, and filtered history into a simple context for any node."""
    msgs      = state.get("messages", [])
    summary   = state.get("summary", "")
    info_data = state.get("info_data", "")
    
    context_msgs = []
    
    # 1. Add Summary (if any)
    if summary:
        context_msgs.append(SystemMessage(content=f"<past_summary>\n{summary}\n</past_summary>"))
    
    # 2. Add Grounding Data
    if info_data:
        context_msgs.append(SystemMessage(content=f"### [Restaurant Info] START\n{info_data}\n### [Restaurant Info] END"))
    
    # 3. Add Validation Errors (if any)
    order_status = state.get("order_status")
    validation_errors = state.get("validation_errors", [])
    if order_status == "extracting" and validation_errors:
        errors_str = "\n".join(f"- {e}" for e in validation_errors)
        context_msgs.append(
            SystemMessage(
                content=f"<validation_context>\n{errors_str}\n\nExplain these issues to the user concisely. Tell them to correct them. Do not ask for confirmation yet.\n</validation_context>"
            )
        )

    # 4. Add Execution Errors (if any)
    if order_status == "error":
        err_msg = state.get("order_error", "")
            
        context_msgs.append(
            SystemMessage(
                content=(
                    f"<execution_error_context>\n"
                    f"The order placement failed with this internal message: \"{err_msg}\"\n\n"
                    f"COMMUNICATE THIS TO THE USER NATURALLY.\n"
                    f"</execution_error_context>"
                )
            )
        )

    # 5. Add Recent History
    recent = msgs[-settings.RECENT_CONTEXT_MESSAGES:] if msgs else []
    _KEEP_SYSTEM_PREFIXES = ("System: SUCCESS", "System: Order cancelled", "System: [MENU", "System: '")
    filtered = [
        m for m in recent
        if not (
            hasattr(m, "content")
            and (m.content or "").startswith("System:")
            and not any((m.content or "").startswith(p) for p in _KEEP_SYSTEM_PREFIXES)
        )
    ]
    
    return context_msgs + [SystemMessage(content="<conversation_history>")] + filtered + [SystemMessage(content="</conversation_history>")]

async def handle_interrupt(state: State, issue_text: str) -> str:
    """
    Triggers an interrupt with a dynamically generated LLM message.
    """
    # 1. Generate the premium message using LLM
    try:
        menu_summary = build_menu_summary()
        # Use ainvoke for async compatibility
        res = await _interrupt_chain.ainvoke({
            "menu": menu_summary,
            "issues": issue_text,
        })
        prompt_message = res.content
    except Exception:
        # Fallback if LLM fails
        prompt_message = (
            f"I found the following issues that need your attention:\n"
            f"{issue_text}\n\n"
            f"(Reply 'cancel' to stop)"
        )

    # 2. Trigger the interrupt
    user_response = interrupt(prompt_message)
    
    # 3. Return the response text
    if isinstance(user_response, str):
        return user_response
    elif isinstance(user_response, dict) and "resume" in user_response:
        return user_response["resume"]
    
    return str(user_response)
