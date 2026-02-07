#!/usr/bin/env python3
"""CheziousBot CLI - Interactive chat client with streaming"""

import asyncio
import sys
import httpx
from uuid import UUID


API_BASE = "http://localhost:8000/api/v1"


async def create_session(client: httpx.AsyncClient, user_id: str) -> UUID:
    """Create a new chat session."""
    response = await client.post(
        f"{API_BASE}/sessions",
        json={"user_id": user_id},
    )
    response.raise_for_status()
    data = response.json()
    return UUID(data["id"])


async def stream_chat(
    client: httpx.AsyncClient,
    session_id: UUID,
    message: str,
) -> None:
    """Send a message and stream the response."""
    print("\n🤖 ", end="", flush=True)

    async with client.stream(
        "POST",
        f"{API_BASE}/chat",
        json={"session_id": str(session_id), "message": message},
        timeout=60.0,
    ) as response:
        response.raise_for_status()

        async for line in response.aiter_lines():
            if not line:
                continue

            # Parse SSE format
            if line.startswith("event:"):
                event_type = line[6:].strip()
                if event_type == "done":
                    break
                continue

            if line.startswith("data:"):
                import json
                data = line[5:].strip()
                if data:
                    try:
                        parsed = json.loads(data)
                        if "token" in parsed:
                            print(parsed["token"], end="", flush=True)
                        elif "error" in parsed:
                            print(f"\n❌ Error: {parsed['error']}")
                    except json.JSONDecodeError:
                        pass

    print()  # New line after response


async def main():
    """Main CLI loop."""
    print("=" * 50)
    print("🍕 Welcome to CheziousBot CLI!")
    print("=" * 50)
    print("\nType your message and press Enter.")
    print("Commands: /new (new session), /quit (exit)\n")

    # Get username
    user_id = input("Enter your name: ").strip() or "guest"
    print(f"\nHello, {user_id}! Creating session...\n")

    async with httpx.AsyncClient() as client:
        try:
            session_id = await create_session(client, user_id)
            print(f"✅ Session created: {session_id}\n")
        except httpx.HTTPError as e:
            print(f"❌ Failed to create session: {e}")
            print("Make sure the server is running: uvicorn app.main:app --reload")
            return

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "/quit":
                    print("\n👋 Goodbye!")
                    break

                if user_input.lower() == "/new":
                    session_id = await create_session(client, user_id)
                    print(f"\n✅ New session created: {session_id}\n")
                    continue

                await stream_chat(client, session_id, user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except httpx.HTTPError as e:
                print(f"\n❌ API Error: {e}")
            except Exception as e:
                print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
