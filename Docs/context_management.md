# Context Management Strategy

## Overview

Context management is critical for maintaining coherent, multi-turn conversations while staying within LLM token limits. CheziousBot uses a **hybrid sliding window approach** optimized for the food ordering use case.

---

## The Problem

LLMs have a limited **context window** (the amount of text they can process at once). For Groq's `llama-3.1-8b-instant`:

- **Context Window:** 8,192 tokens
- **Max Output Tokens:** 512 tokens (configured)
- **Usable Context:** ~7,500 tokens

When conversations exceed this limit, the model:
- Forgets earlier instructions
- Loses important context
- Produces irrelevant responses

---

## Context Management Techniques

### 1. Sliding Window (Selected ✅)

Keep only the **last N messages** in context, discarding older ones.

```
Message 1 ──────────────────────────┐
Message 2 ─────────────────────┐    │ Discarded
Message 3 ────────────────┐    │    │
Message 4 ───────────┐    │    │    │
Message 5 ──────┐    │    │    ├────┘
Message 6 ─┐    │    │    │    │
Message 7  │    │    │    ├────┘
Message 8  │    │    ├────┘
Message 9  │    ├────┘
Message 10 ├────┘◄─── Context Window (Last 10)
```

**Pros:**
- Simple to implement
- Predictable token usage
- Fast — no extra LLM calls

**Cons:**
- Loses older context entirely

### 2. Summarization (Future Enhancement)

Periodically summarize older messages into a compressed form.

**Types:**
- **Running Summary:** LLM summarizes after every N messages
- **Summary Buffer:** Keep recent messages + summary of older ones
- **Hierarchical:** Chunk → Summarize → Combine

**Pros:**
- Retains important context longer
- Better for complex conversations

**Cons:**
- Adds latency (extra LLM call)
- Increases API costs
- Risk of losing details in summary

### 3. RAG (Retrieval-Augmented Generation)

Store messages in a vector database, retrieve only relevant ones.

**Pros:**
- Handles very long conversations
- Only includes relevant context

**Cons:**
- Complex to implement
- Overkill for simple Q&A chatbots

### 4. Truncation

Simply cut off excess tokens when limit is reached.

**Pros:**
- Simplest approach

**Cons:**
- Loses context mid-sentence
- Poor user experience

---

## CheziousBot Implementation

### Chosen Approach: Sliding Window

For a food ordering chatbot, conversations are typically:
- Short (5-15 messages)
- Task-focused (menu, prices, ordering)
- Low complexity

**Sliding window is ideal** because:
1. Most conversations fit entirely in context
2. Recent messages are most relevant
3. No additional latency or cost
4. Simple, reliable implementation

### Configuration

```python
# app/core/config.py
CONTEXT_WINDOW_SIZE = 10  # Last 10 messages
```

### Context Service Implementation

```python
# app/services/context_service.py

class ContextService:
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
    
    async def get_context_messages(
        self, 
        session_id: UUID
    ) -> list[Message]:
        """Fetch last N messages for a session."""
        messages = await Message.filter(
            session_id=session_id
        ).order_by('-created_at').limit(self.max_messages)
        
        # Reverse to chronological order
        return list(reversed(messages))
    
    def build_messages_for_llm(
        self, 
        messages: list[Message],
        system_prompt: str
    ) -> list[dict]:
        """Format messages for Groq API."""
        llm_messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        for msg in messages:
            llm_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return llm_messages
```

### Token Budget Allocation

| Component | Tokens | Purpose |
|-----------|--------|---------|
| System Prompt | ~2,500 | Brand info, menu, branches |
| Context Messages | ~4,500 | Last 10 messages |
| Response | 512 | Max output tokens |
| **Total** | ~7,500 | Within 8K limit |

### Message Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User sends message                                       │
├─────────────────────────────────────────────────────────────┤
│ 2. Save user message to DB                                  │
├─────────────────────────────────────────────────────────────┤
│ 3. Fetch last N messages from session                       │
│    SELECT * FROM messages                                   │
│    WHERE session_id = ?                                     │
│    ORDER BY created_at DESC                                 │
│    LIMIT 10                                                 │
├─────────────────────────────────────────────────────────────┤
│ 4. Build LLM messages:                                      │
│    [                                                        │
│      {"role": "system", "content": "<system_prompt>"},      │
│      {"role": "user", "content": "<msg_1>"},                │
│      {"role": "assistant", "content": "<msg_2>"},           │
│      ...                                                    │
│      {"role": "user", "content": "<current_message>"}       │
│    ]                                                        │
├─────────────────────────────────────────────────────────────┤
│ 5. Send to Groq API → Stream response                       │
├─────────────────────────────────────────────────────────────┤
│ 6. Save assistant response to DB                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Edge Cases & Handling

### 1. Very Long User Messages

```python
MAX_MESSAGE_LENGTH = 500  # characters

def validate_message(content: str) -> str:
    if len(content) > MAX_MESSAGE_LENGTH:
        raise ValidationException(
            f"Message exceeds {MAX_MESSAGE_LENGTH} characters"
        )
    return content
```

### 2. Token Overflow Protection

```python
def estimate_tokens(text: str) -> int:
    """Rough estimation: 1 token ≈ 4 characters"""
    return len(text) // 4

def trim_context_to_fit(
    messages: list[dict], 
    max_tokens: int = 6000
) -> list[dict]:
    """Remove oldest messages if context exceeds limit."""
    total = sum(estimate_tokens(m["content"]) for m in messages)
    
    while total > max_tokens and len(messages) > 2:
        # Always keep system prompt (index 0)
        removed = messages.pop(1)  # Remove oldest user message
        total -= estimate_tokens(removed["content"])
    
    return messages
```

### 3. Session Reset

Users can start fresh by creating a new session:
```
POST /sessions
{
  "user_id": "john_doe"
}
```

---

## Future Enhancements

### Phase 2: Summary Buffer Memory

When context window is nearly full:
1. Summarize oldest 5 messages
2. Replace them with summary
3. Keep recent 5 messages verbatim

```python
# Future implementation
class SummaryBufferMemory:
    async def compress_if_needed(self, session_id: UUID):
        messages = await self.get_all_messages(session_id)
        token_count = self.estimate_tokens(messages)
        
        if token_count > TOKEN_THRESHOLD:
            older_messages = messages[:-5]  # Keep last 5
            summary = await self.summarize(older_messages)
            await self.replace_with_summary(session_id, summary)
```

### Phase 3: Semantic Retrieval

For very long conversations or returning users:
1. Store all messages in vector DB
2. On new message, retrieve relevant past context
3. Inject into prompt

---

## Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CONTEXT_WINDOW_SIZE` | 10 | Max messages to include |
| `MAX_MESSAGE_LENGTH` | 500 | Max user message chars |
| `GROQ_MAX_TOKENS` | 512 | Max response tokens |
| `TOKEN_SAFETY_MARGIN` | 500 | Buffer for safety |

---

## Summary

| Aspect | Decision |
|--------|----------|
| **Primary Strategy** | Sliding Window (Last 10 messages) |
| **Why** | Simple, fast, fits use case |
| **Token Budget** | ~7,500 tokens usable |
| **Future** | Summary Buffer Memory (Phase 2) |
