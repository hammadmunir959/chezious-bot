"""
summarize_node.py — Rolling conversation memory compressor (Async).
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.core.llm_client import llm
from app.agent.state import State
from app.agent.prompts.prompts import SUMMARIZE_PROMPT
from app.core.config import settings

async def summarize_node(state: State) -> dict:
    """Compresses conversation history into a rolling summary."""
    
    existing_summary = state.get("summary", "")
    last_index = state.get("last_summarized_index", 0)
    new_messages = state["messages"][last_index:]

    if not new_messages:
        return {}

    # Build the prompt template using ChatPromptTemplate
    if existing_summary:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", SUMMARIZE_PROMPT),
            ("system", f"Current summary:\n{existing_summary}"),
            MessagesPlaceholder("new_messages"),
            ("system", "Update the summary above with the new messages. Preserve all order-critical facts. Keep it under 6 bullet points.")
        ])
    else:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", SUMMARIZE_PROMPT),
            MessagesPlaceholder("new_messages"),
        ])


    try:
        # Use ainvoke for async
        prompt = prompt_template.invoke({"new_messages": new_messages})
        response = await llm.bind(temperature=0).with_retry(
            stop_after_attempt=settings.MAX_LLM_RETRIES
        ).ainvoke(prompt)
        
        if not response:
            raise Exception("LLM returned no response")

        return {
            "summary": response.content,
            "last_summarized_index": len(state["messages"]),
        }
    except Exception:
        return {}
