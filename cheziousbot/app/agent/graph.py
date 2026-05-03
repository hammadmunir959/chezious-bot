from langgraph.graph import StateGraph, START, END
from app.agent.state import State
from app.agent.nodes.classify_intent_node import classify_intent_node
from app.agent.nodes.info_node import info_node
from app.agent.nodes.summarize_node import summarize_node
from app.agent.nodes.chat_node import chat_node
from app.agent.nodes.extract_node import extract_node
from app.agent.nodes.validate_node import validate_node
from app.agent.nodes.interrupt_node import interrupt_node
from app.agent.nodes.confirm_node import confirm_node
from app.agent.nodes.execute_order_node import execute_order_node

from app.agent.routings import (
    route_start,
    route_after_classify,
    route_after_extract,
    route_after_interrupt,
    route_after_confirm
)

from app.core.config import settings

# ── 1. Graph Definition ───────────────────────────────────────────────────────

workflow = StateGraph(State)

# ── 2. Add Nodes ─────────────────────────────────────────────────────────────

workflow.add_node("summarize", summarize_node)
workflow.add_node("classify", classify_intent_node)
workflow.add_node("info", info_node)
workflow.add_node("chat", chat_node)
workflow.add_node("extract", extract_node)
workflow.add_node("validate", validate_node)
workflow.add_node("interrupt", interrupt_node)
workflow.add_node("confirm", confirm_node)
workflow.add_node("execute", execute_order_node)

# ── 3. Add Edges ──────────────────────────────────────────────────────────────

# Entry Edge
workflow.set_conditional_entry_point(
    route_start,
    {
        "summarize": "summarize",
        "classify": "classify"
    }
)

# Summarization path
workflow.add_edge("summarize", "classify")

# Intent Classification
workflow.add_conditional_edges(
    "classify",
    route_after_classify,
    {
        "extract": "extract",
        "info": "info",
        "chat": "chat"
    }
)

# Functional paths
workflow.add_conditional_edges(
    "extract", 
    route_after_extract, 
    {   
        "validate": "validate", 
        END: END
    }
)
workflow.add_edge("validate", "interrupt")
workflow.add_conditional_edges(
    "interrupt", 
    route_after_interrupt, 
    {
        "confirm": "confirm", 
        "extract": "extract"
    }
)
workflow.add_conditional_edges(
    "confirm", 
    route_after_confirm, 
    {
        "execute": "execute", 
        "interrupt": "interrupt", 
        "extract": "extract", 
        END: END
    }
)

workflow.add_edge("execute", END)
workflow.add_edge("info", END)
workflow.add_edge("chat", END)

# ── Compile ───────────────────────────────────────────────────────────────────


from langgraph.checkpoint.redis import AsyncRedisSaver

# Initialize Official Redis checkpointer (requires RedisJSON and RediSearch)
checkpointer = AsyncRedisSaver(settings.REDIS_URL)

graph = workflow.compile(checkpointer=checkpointer)
# graph = workflow.compile()

