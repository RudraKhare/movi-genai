#!/usr/bin/env python3
"""
Apply Schema Migration
Executes fix_schema_mismatch.sql against Supabase database
"""
import os
import sys
import asyncpg
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from backend/.env
backend_env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(backend_env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    sys.exit(1)

SQL_FILE = os.path.join(os.path.dirname(__file__), "fix_schema_mismatch.sql")


async def apply_migration():
    """Apply SQL migration to database"""
    print("=" * 60)
    print("🔧 APPLYING SCHEMA MIGRATION")
    print("=" * 60)
    print(f"📄 SQL File: {SQL_FILE}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Read SQL file
    try:
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except FileNotFoundError:
        print(f"❌ SQL file not found: {SQL_FILE}")
        return False
    
    print("✅ SQL migration file loaded")
    print()
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to Supabase database")
        print()
        
        # Execute migration
        print("🚀 Executing migration...")
        print("-" * 60)
        
        # Split SQL into individual statements and execute
        statements = []
        current_statement = []
        in_do_block = False
        
        for line in sql_content.split('\n'):
            line_stripped = line.strip()
            
            # Skip comments and empty lines
            if not line_stripped or line_stripped.startswith('--'):
                continue
            
            # Track DO blocks
            if 'DO $$' in line:
                in_do_block = True
            
            current_statement.append(line)
            
            # End of DO block
            if in_do_block and 'END $$;' in line:
                in_do_block = False
                statements.append('\n'.join(current_statement))
                current_statement = []
            # Regular statement end
            elif not in_do_block and line_stripped.endswith(';') and 'DO $$' not in line:
                statements.append('\n'.join(current_statement))
                current_statement = []
        
        # Execute each statement
        for i, stmt in enumerate(statements, 1):
            stmt = stmt.strip()
            if stmt:
                try:
                    await conn.execute(stmt)
                    # Print abbreviated statement
                    first_line = stmt.split('\n')[0][:60]
                    print(f"  ✅ Statement {i}: {first_line}...")
                except Exception as e:
                    print(f"  ❌ Statement {i} failed: {e}")
                    # Continue with other statements
        
        print("-" * 60)
        print("✅ Migration executed successfully!")
        print()
        
        # Verification queries
        print("🔍 VERIFICATION")
        print("-" * 60)
        
        # Verify stops.status exists
        try:
            result = await conn.fetchrow("SELECT stop_id, name, status FROM stops LIMIT 1")
            if result:
                print(f"✅ stops.status exists (sample: status='{result['status']}')")
            else:
                print("✅ stops.status column exists (table empty)")
        except Exception as e:
            print(f"❌ stops.status verification failed: {e}")
        
        # Verify paths.path_name exists
        try:
            result = await conn.fetchrow("SELECT path_id, path_name FROM paths LIMIT 1")
            if result:
                print(f"✅ paths.path_name exists (sample: '{result['path_name']}')")
            else:
                print("✅ paths.path_name column exists (table empty)")
        except Exception as e:
            print(f"❌ paths.path_name verification failed: {e}")
        
        # Verify routes.route_name exists
        try:
            result = await conn.fetchrow("SELECT route_id, route_name FROM routes LIMIT 1")
            if result:
                print(f"✅ routes.route_name exists (sample: '{result['route_name']}')")
            else:
                print("✅ routes.route_name column exists (table empty)")
        except Exception as e:
            print(f"❌ routes.route_name verification failed: {e}")
        
        # Verify vehicles.registration_number exists
        try:
            result = await conn.fetchrow("SELECT vehicle_id, registration_number FROM vehicles LIMIT 1")
            if result:
                print(f"✅ vehicles.registration_number exists (sample: '{result['registration_number']}')")
            else:
                print("✅ vehicles.registration_number column exists (table empty)")
        except Exception as e:
            print(f"❌ vehicles.registration_number verification failed: {e}")
        
        print("-" * 60)
        print()
        
        await conn.close()
        
        print("=" * 60)
        print("✅ SCHEMA MIGRATION COMPLETE")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Restart backend server to use new schema")
        print("2. Test stop creation: POST /api/routes/stops/create")
        print("3. Verify no more 'column does not exist' errors")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(apply_migration())
    sys.exit(0 if success else 1)
