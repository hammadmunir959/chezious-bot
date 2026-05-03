import logging
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.graph import graph
from app.schemas.chat import ChatResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

async def process_chat(message: str, user_id: str, thread_id: str) -> ChatResponse:
    """
    Invokes the stateful LangGraph agent.
    If the primary LLM fails, falls back to the secondary LLM and retries.
    """
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
    
    # 1. State update
    # In LangGraph 0.2+, appending messages to a channel automatically keeps history.
    try:
        result = await graph.ainvoke({"messages": [HumanMessage(content=message)]}, config)
        
    except Exception as e:
        logger.error(f"Primary LLM or Graph failed: {e}. Attempting fallback...")
        logger.exception("Full traceback for graph.ainvoke failure:")
        
        # We can implement a naive retry if it's a transient API error:
        import asyncio
        await asyncio.sleep(1)
        try:
            result = await graph.ainvoke({"messages": [HumanMessage(content=message)]}, config)
        except Exception as retry_e:
            logger.error(f"Fallback attempt also failed: {retry_e}")
            raise retry_e

    # 2. Extract final AIMessage or handle interrupt
    # If the graph is interrupted, the result might not have the final message yet.
    # We should check if there are any pending interrupts.
    state = await graph.aget_state(config)
    
    if state.next:
        # We are at an interrupt (checkpoint)
        # The interrupt message is usually stored in the 'tasks' or as a value returned by the node.
        # However, our nodes use `interrupt()` which returns the value to the user.
        # Let's extract the last message from state.
        messages = state.values.get("messages", [])
    else:
        messages = result.get("messages", [])

    if not messages:
        return ChatResponse(reply="I encountered an error. Please try again.", thread_id=thread_id)
        
    final_message = messages[-1]
    
    # If the last message is a HumanMessage, it means the bot hasn't replied yet (likely at an interrupt)
    if isinstance(final_message, HumanMessage) and state.next:
        # Try to find the interrupt message
        for task in state.tasks:
            if task.interrupts:
                # Use the first interrupt message
                reply = str(task.interrupts[0].value)
                return ChatResponse(reply=reply, thread_id=thread_id)

    reply = final_message.content if hasattr(final_message, "content") else str(final_message)

    return ChatResponse(reply=reply, thread_id=thread_id)

async def stream_chat(message: str, user_id: str, thread_id: str):
    """
    Streams events from the LangGraph agent as Server-Sent Events (SSE).

    Event types emitted:
    - node:   Agent node entered (e.g. classify, info, chat, extract …)
    - content: Streamed text token from the LLM
    - tool_start: A tool/function call has begun
    - tool_end:   A tool/function call has completed
    - done:   Streaming finished successfully
    - error:  An error occurred
    """
    import json

    # All named graph nodes — used to filter on_chain_start noise
    GRAPH_NODES = {"summarize", "classify", "info", "chat", "extract",
                   "validate", "interrupt", "confirm", "execute"}

    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
    input_data = {"messages": [HumanMessage(content=message)]}

    try:
        async for event in graph.astream_events(input_data, config, version="v2"):
            kind = event["event"]
            name = event.get("name", "")

            # ── Node transitions ─────────────────────────────────────────────
            if kind == "on_chain_start" and name in GRAPH_NODES:
                yield f"data: {json.dumps({'type': 'node', 'node': name})}\n\n"

            # ── LLM token streaming ──────────────────────────────────────────
            elif kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                content = chunk.content if chunk else ""
                if content:
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

            # ── Tool / function calls ────────────────────────────────────────
            elif kind == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'name': name, 'input': event['data'].get('input')})}\n\n"

            elif kind == "on_tool_end":
                # Serialise output safely (may not be JSON-serialisable)
                raw_output = event["data"].get("output")
                try:
                    output_str = raw_output if isinstance(raw_output, str) else json.dumps(raw_output, default=str)
                except Exception:
                    output_str = str(raw_output)
                yield f"data: {json.dumps({'type': 'tool_end', 'name': name, 'output': output_str})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        logger.error(f"Error in stream_chat: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

