#!/usr/bin/env python3
"""
Check database schema
"""

import asyncio
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def check_schema():
    """Check actual database schema"""
    try:
        from app.core.supabase_client import get_conn
        
        conn = await get_conn()
        try:
            print("📋 DATABASE SCHEMA CHECK")
            print("=" * 60)
            
            # Check each table
            tables = ['routes', 'vehicles', 'drivers', 'daily_trips', 'deployments']
            
            for table in tables:
                print(f"\n🗂️  {table.upper()} TABLE:")
                try:
                    # Get sample row to see columns
                    result = await conn.fetch(f"SELECT * FROM {table} LIMIT 1")
                    if result:
                        columns = list(result[0].keys())
                        print(f"   Columns: {columns}")
                        print(f"   Sample: {dict(result[0])}")
                    else:
                        # Table exists but is empty, get column info differently
                        result = await conn.fetch(f"""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_name = '{table}'
                            ORDER BY ordinal_position
                        """)
                        if result:
                            columns = [row['column_name'] for row in result]
                            print(f"   Columns: {columns}")
                            print(f"   (Table is empty)")
                        else:
                            print(f"   ❌ Table not found")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_schema())
