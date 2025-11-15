import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')
from app.core.supabase_client import get_conn

async def apply_migration():
    print("📦 Applying agent_sessions migration...")
    
    with open('migrations/004_agent_sessions.sql', 'r') as f:
        sql = f.read()
    
    pool = await get_conn()
    async with pool.acquire() as conn:
        try:
            # Execute the entire migration as one block
            await conn.execute(sql)
            print('✅ Migration executed successfully')
        except Exception as e:
            print(f'⚠️  Migration execution: {e}')
        
        # Verify table created
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name='agent_sessions'
            )
        """)
        
        if result:
            print('\n✅ Migration 004_agent_sessions.sql applied successfully!')
            print('   Table: agent_sessions created')
            
            # Check column structure
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name='agent_sessions'
                ORDER BY ordinal_position
            """)
            print('\n📋 Table structure:')
            for col in columns:
                print(f'   - {col["column_name"]}: {col["data_type"]}')
        else:
            print('\n❌ Migration failed - table not found')

asyncio.run(apply_migration())
