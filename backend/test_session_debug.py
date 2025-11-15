"""
Test script to debug session_id creation issue
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.core.supabase_client import get_conn
import json


async def test_session_creation():
    """Test if we can create a session in the database"""
    print("=" * 60)
    print("Testing agent_sessions table")
    print("=" * 60)
    
    try:
        pool = await get_conn()
        print("✅ Got connection pool")
        
        async with pool.acquire() as conn:
            print("✅ Acquired connection")
            
            # Check if table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'agent_sessions'
                )
            """)
            print(f"\nTable exists: {table_exists}")
            
            if not table_exists:
                print("❌ agent_sessions table does not exist!")
                print("   Run: python apply_migration.py")
                return
            
            # Count existing sessions
            count = await conn.fetchval("SELECT COUNT(*) FROM agent_sessions")
            print(f"Existing sessions: {count}")
            
            # Try to insert a test session
            print("\n📝 Attempting to insert test session...")
            pending_action = {
                "action": "test_action",
                "trip_id": 999,
                "test": True
            }
            
            session = await conn.fetchrow("""
                INSERT INTO agent_sessions (user_id, pending_action, status)
                VALUES ($1, $2, 'PENDING')
                RETURNING session_id, user_id, status, created_at
            """, 1, json.dumps(pending_action))
            
            if session:
                print(f"✅ Successfully created session!")
                print(f"   session_id: {session['session_id']}")
                print(f"   user_id: {session['user_id']}")
                print(f"   status: {session['status']}")
                print(f"   created_at: {session['created_at']}")
                
                # Clean up test session
                await conn.execute("DELETE FROM agent_sessions WHERE session_id = $1", session['session_id'])
                print("\n🧹 Cleaned up test session")
            else:
                print("❌ INSERT returned None - this is the problem!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_session_creation())
