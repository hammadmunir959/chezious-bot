"""
chat_node.py — Lean node for handling generic greetings and non-specific queries (Async).
"""
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from app.agent.state import State
from app.core.llm_client import llm
from app.agent.prompts.prompts import SYSTEM_PROMPT_TEMPLATE, SPAM_PROMPT_TEMPLATE, CHAT_FALLBACK_MSG
from app.agent.nodes.node_utils import prepare_node_context
from app.core.config import settings

async def chat_node(state: State, config: RunnableConfig) -> dict:
    """Handles general chatter using the LLM."""
    
    # 1. Synthesis
    context = await prepare_node_context(state)
    intent  = (state.get("intent") or "").upper()

    if intent == "SPAM":
        prompt = SPAM_PROMPT_TEMPLATE.invoke({"messages": context}).to_messages()
    else:
        prompt = SYSTEM_PROMPT_TEMPLATE.invoke({"messages": context}).to_messages()

    # 2. Invoke
    try:
        response = await llm.bind(temperature=0).with_retry(
            stop_after_attempt=settings.MAX_LLM_RETRIES
        ).ainvoke(prompt, config=config)
    except Exception:
        response = AIMessage(content=CHAT_FALLBACK_MSG)

    return {
        "messages": [response],
        "intent": "INFO", # Default back to INFO
    }
