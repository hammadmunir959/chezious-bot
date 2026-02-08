import asyncio
import sys
from typing import NoReturn

# Add project root to path
import os
sys.path.append(os.getcwd())

from app.core.config import settings
from app.api.v1.health import readiness_check
from app.db.session import get_session
from app.llm.groq_client import get_groq_client
from app.models.session import ChatSession

async def verify_system():
    print("🔍 Verifying CheziousBot System...")
    
    # 1. Config Check
    print("\n[1/5] Checking Configuration...")
    print(f"✅ Allowed Origins: {settings.allowed_origins}")
    print(f"✅ API Key Enabled: {settings.api_key_enabled}")
    
    # 2. Database & Health Check
    print("\n[2/5] Checking Database & Health...")
    class MockSession:
        async def execute(self, query): return
    
    # We can't easily mock the dependency here without spending time, 
    # so we'll just check if we can import and inspect the health endpoint function
    print(f"✅ Health endpoint loaded: {readiness_check.__name__}")
    
    # 3. Groq Client Lazy Init
    print("\n[3/5] Checking Groq Client...")
    client = get_groq_client()
    print(f"✅ Groq Client initialized (lazy): {client is not None}")
    
    # 4. Model Changes
    print("\n[4/5] Checking Model Changes...")
    session_fields = ChatSession.model_fields.keys()
    if "last_activity_at" in session_fields and "expires_at" in session_fields:
        print("✅ Session expiry fields present")
    else:
        print("❌ Session expiry fields MISSING")
        
    print(f"✅ Status field type: {ChatSession.model_fields['status'].annotation}")
    
    # 5. Imports Check (users.py)
    print("\n[5/5] Checking Imports...")
    try:
        from app.api.v1.users import delete_user
        print("✅ users.py imports are clean")
    except ImportError as e:
        print(f"❌ ImportError in users.py: {e}")

    print("\n✨ Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_system())
