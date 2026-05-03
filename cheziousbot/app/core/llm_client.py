from langchain_openai import ChatOpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_llm(use_fallback: bool = False) -> ChatOpenAI:
    """Return configured LLM. Qwen primary, OpenAI fallback."""
    if use_fallback:
        logger.warning("LLM fallback: switching to OpenAI")
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
    return ChatOpenAI(
        model=settings.QWEN_MODEL,
        base_url=settings.QWEN_BASE_URL,
        api_key=settings.QWEN_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )

# Convenience singletons used in nodes
# Nodes import: from app.core.llm_client import llm, advanced_llm
llm = get_llm()
advanced_llm = get_llm()
