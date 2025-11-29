import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')
from app.core.supabase_client import get_conn

async def apply_conversation_history_migration():
    print("📦 Adding conversation_history column to agent_sessions...")
    
    with open('migrations/005_conversation_history.sql', 'r') as f:
        sql = f.read()
    
    pool = await get_conn()
    async with pool.acquire() as conn:
        try:
            # Execute the migration
            await conn.execute(sql)
            print('✅ Migration executed successfully')
        except Exception as e:
            print(f'⚠️  Migration execution: {e}')
        
        # Verify column added
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name='agent_sessions' AND column_name='conversation_history'
            )
        """)
        
        if result:
            print('\n✅ conversation_history column added successfully!')
            
            # Check updated table structure
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name='agent_sessions'
                ORDER BY ordinal_position
            """)
            print('\n📋 Updated table structure:')
            for col in columns:
                print(f'   - {col["column_name"]}: {col["data_type"]}')
        else:
            print('\n❌ Migration failed - conversation_history column not found')

asyncio.run(apply_conversation_history_migration())
