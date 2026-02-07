# CheziousBot — Features

## Core Features

### 🤖 AI-Powered Chat (P0)
- Real-time streaming responses via SSE
- Sub-500ms first token latency
- Context-aware conversations (remembers last 10 messages)
- Powered by Groq's ultra-fast inference

### 💬 Session Management (P0)
- UUID-based session creation
- Persistent message history
- Session archiving
- Multi-session support

### 👤 User-Based Tracking (P0)
- Simple username-based user identification (no auth required)
- Get all conversations for a user via `user_id`
- Get specific conversation using `user_id` + `session_id`
- Track user session history

### 🍕 Food Business Knowledge (P1)
- **Menu Information** — All items with prices and sizes
- **Business Hours** — Operating times with Friday variations
- **Branch Locations** — All Pakistan-wide locations
- **Ordering Guidance** — Phone, app, website, delivery apps
- **Delivery Policy** — Free delivery, timing, coverage
- **Payment Options** — Cash, JazzCash, Easypaisa, cards

---

## Technical Features

### ⚡ Performance
- Async API endpoints
- Token-by-token streaming
- Efficient context windowing
- DB queries < 100ms (P95)

### 🛡️ Reliability
- Typed exception hierarchy
- No raw exceptions leak to client
- All errors logged with request_id
- Graceful stream termination

### 📊 Observability
- Structured JSON logging
- Request tracing via request_id
- Session tracking
- Latency metrics

### 🔒 Security
- Pydantic input validation
- Max message length enforcement
- Per-user rate limiting
- API key protection

---

## What the Bot Can Answer

| Query Type | Example |
|------------|---------|
| Menu | "What pizzas do you have?" |
| Prices | "How much is a large Chicken Tikka?" |
| Deals | "What combos are available?" |
| Hours | "What time do you close?" |
| Contact | "What's your phone number?" |
| Location | "Where is the DHA Lahore branch?" |
| Ordering | "How can I place an order?" |
| Delivery | "Do you deliver? Is it free?" |
| Payment | "Can I pay with JazzCash?" |

---

## Out of Scope (Not Included)

- ❌ Payment processing
- ❌ Actual order placement
- ❌ Multilingual support
- ❌ Image recognition
- ❌ Voice input

---

## Future Enhancements

- 📝 Context summarization for longer conversations
- 🐘 PostgreSQL for production scale
- ⚡ Redis caching for repeated queries
- 📊 Admin dashboard for analytics
- 🔀 Multi-model routing (fallback LLMs)
