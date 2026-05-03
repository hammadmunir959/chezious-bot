import logging
logger = logging.getLogger(__name__)

"""
classify_intent_node.py — Lightweight intent classification (Async).
Classifies user intent as: ORDER / INFO / SPAM.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.core.llm_client import llm, advanced_llm
from app.agent.state import State
from app.schemas.agent import IntentClassification
from app.agent.prompts.prompts import INTENT_CLASSIFICATION_PROMPT
from app.core.config import settings

_prompt = ChatPromptTemplate([
    ("system", INTENT_CLASSIFICATION_PROMPT),
    MessagesPlaceholder("history"),        # recent conversation context
    ("human", "Classify this: {user_msg}"), # explicit last message to classify
])

_chain = _prompt | advanced_llm.bind(temperature=0).with_structured_output(IntentClassification)


async def classify_intent_node(state: State) -> dict:
    """Classify user intent as ORDER, INFO, or SPAM."""
    messages = state.get("messages", [])
    recent = messages[-settings.RECENT_CONTEXT_MESSAGES:-1] 
    user_msg = messages[-1].content if messages else ""

    try:
        # Use ainvoke for async compatibility
        result = await _chain.ainvoke({
            "history": recent,
            "user_msg": user_msg,
        })
        return {
            "intent": result.intent, 
            "reasoning": result.reasoning
        }

    except Exception as e:
        # SECURE FALLBACK: Default to SPAM if classification fails on complex/poisoned inputs
        logger.info(f"Fallback due to classification error or safety filter trigger. {e}")
        return {
            "intent": "SPAM", 
            "reasoning": "Fallback due to classification error or safety filter trigger."
        }