#!/usr/bin/env python3
"""CheziousBot CLI - Interactive chat client with streaming"""

import asyncio
import signal
import sys
import httpx
from uuid import UUID, uuid4


API_BASE = "http://localhost:8000/api/v1"


async def create_user(client: httpx.AsyncClient, user_id: str, name: str, city: str | None = None) -> dict:
    """Create or update a user."""
    payload = {"user_id": user_id, "name": name}
    if city:
        payload["city"] = city
    response = await client.post(f"{API_BASE}/users/", json=payload)
    response.raise_for_status()
    return response.json()


async def stream_chat(
    client: httpx.AsyncClient,
    session_id: UUID,
    message: str,
    user_id: str,
) -> None:
    """Send a message and stream the response."""
    import json
    
    print("\n🤖 ", end="", flush=True)

    try:
        async with client.stream(
            "POST",
            f"{API_BASE}/chat",
            json={"session_id": str(session_id), "message": message, "user_id": user_id},
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
    except asyncio.CancelledError:
        print("\n[Cancelled]")
        raise

    print()  # New line after response


def generate_session_id() -> UUID:
    """Generate a new session ID locally."""
    return uuid4()


async def main():
    """Main CLI loop."""
    print("=" * 50)
    print("🍕 Welcome to CheziousBot CLI!")
    print("=" * 50)
    print("\nType your message and press Enter.")
    print("Commands: /new (new session), /quit (exit)\n")

    # Get user info
    try:
        name = input("Enter your name: ").strip() or "Guest"
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Goodbye!")
        return
        
    user_id = name.lower().replace(" ", "_")
    
    # Get city for location-aware responses
    print("\nCities: Lahore, Islamabad, Rawalpindi, Peshawar, Kasur, Mardan, Sahiwal")
    try:
        city = input("Enter your city (optional): ").strip() or None
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Goodbye!")
        return
    
    print(f"\nHello, {name}! Setting up...\n")

    async with httpx.AsyncClient() as client:
        try:
            # Create/update user
            await create_user(client, user_id, name, city)
            print("✅ User registered")
            
            # Generate session ID locally (lazy creation on first message)
            session_id = generate_session_id()
            print(f"✅ Session ready: {str(session_id)[:8]}...\n")
        except httpx.HTTPError as e:
            print(f"❌ Failed to connect: {e}")
            print("Make sure the server is running: uvicorn app.main:app --reload")
            return
        except asyncio.CancelledError:
            print("\n\n👋 Goodbye!")
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
                    session_id = generate_session_id()
                    print(f"\n✅ New session ready: {str(session_id)[:8]}...\n")
                    continue

                await stream_chat(client, session_id, user_input, user_id)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except asyncio.CancelledError:
                print("\n\n👋 Cancelled!")
                break
            except httpx.HTTPError as e:
                print(f"\n❌ API Error: {e}")
            except Exception as e:
                print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
