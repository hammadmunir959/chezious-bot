import logging
logger = logging.getLogger(__name__)

"""
info_node.py — LLM-only info retrieval node with structured output (Async).
"""

import json
from app.core.llm_client import llm, advanced_llm
from app.agent.state import State
from app.utils.knowledge_base import search
from app.agent.prompts.prompts import (
    INFO_CLASSIFICATION_PROMPT, 
    SYSTEM_PROMPT_TEMPLATE, 
    INFO_FALLBACK_MSG
)
from app.schemas.agent import InfoClassification
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from app.agent.nodes.node_utils import prepare_node_context
from app.core.config import settings


_prompt = ChatPromptTemplate.from_messages([
    ("system", INFO_CLASSIFICATION_PROMPT),
    ("human", "{user_msg}"),
])

_classifier = _prompt | advanced_llm.bind(temperature=0).with_structured_output(InfoClassification)

async def info_node(state: State) -> dict:
    user_message = state["messages"][-1].content if state.get("messages") else ""
    if not user_message:
        return {}

    # 1. LLM Classification & Data Fetching
    category, query = None, None
    try:
        # Use ainvoke for async
        result: InfoClassification = await _classifier.ainvoke({"user_msg": user_message})
        category, query = result.category, result.query
        if category:
            category = category.lower().strip()
            if category not in ["menu", "locations", "policies"]:
                category = None
    except Exception as e:
        logger.info(f"InfoClassification Error: {str(e)}")

    data = search(category, query)
    
    # 2. Response Synthesis
    temp_state = dict(state)
    temp_state["info_data"] = json.dumps(data, indent=2, ensure_ascii=False) if data else ""
    
    # await the async helper
    context = await prepare_node_context(temp_state)
    
    # 3. Generate Natural Response
    # Note: SYSTEM_PROMPT_TEMPLATE.invoke is usually synchronous if it doesn't involve model calls
    prompt = SYSTEM_PROMPT_TEMPLATE.invoke({"messages": context}).to_messages()

    # 4. Generate Natural Response
    try:
        response = await llm.bind(temperature=0).with_retry(
            stop_after_attempt=settings.MAX_LLM_RETRIES
        ).ainvoke(prompt)
    except Exception as e:
        logger.info(f"Info Response Generation Error: {str(e)}")
        response = AIMessage(content=INFO_FALLBACK_MSG)

    return {
        "messages": [response],
        "info_data": temp_state["info_data"],
        "intent": "INFO", # Reset intent so we don't loop back to extract unless needed
    }