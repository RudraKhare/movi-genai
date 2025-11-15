#!/usr/bin/env python3
"""
Schema Alignment Checker
Compares Supabase database schema with backend code expectations
"""
import os
import sys
import asyncpg
from dotenv import load_dotenv
from typing import Dict, List, Set

# Load environment variables from backend/.env
backend_env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
load_dotenv(backend_env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    sys.exit(1)

# Expected schema based on backend code
EXPECTED_SCHEMA = {
    "stops": {
        "stop_id": "serial PRIMARY KEY",
        "name": "text NOT NULL",
        "status": "text",  # MISSING - backend expects this
        "latitude": "numeric(10, 6)",
        "longitude": "numeric(10, 6)",
        "address": "text",
        "created_at": "timestamptz"
    },
    "paths": {
        "path_id": "serial PRIMARY KEY",
        "path_name": "text NOT NULL",  # Backend uses path_name, schema has 'name'
        "description": "text",
        "created_at": "timestamptz"
    },
    "routes": {
        "route_id": "serial PRIMARY KEY",
        "path_id": "int",
        "route_name": "text NOT NULL",  # Backend uses route_name, schema has route_display_name
        "shift_time": "time",
        "direction": "text",
        "status": "text",
        "start_point": "text",
        "end_point": "text",
        "created_at": "timestamptz"
    },
    "vehicles": {
        "vehicle_id": "serial PRIMARY KEY",
        "registration_number": "text",  # Backend uses registration_number, schema has license_plate
        "capacity": "int",
        "vehicle_type": "text",
        "status": "text",
        "created_at": "timestamptz"
    },
    "drivers": {
        "driver_id": "serial PRIMARY KEY",
        "name": "text NOT NULL",
        "phone": "text",
        "license_number": "text",
        "status": "text",
        "created_at": "timestamptz"
    },
    "daily_trips": {
        "trip_id": "serial PRIMARY KEY",
        "route_id": "int",
        "display_name": "text NOT NULL",
        "trip_date": "date",
        "booking_status_percentage": "int",
        "live_status": "text",
        "created_at": "timestamptz"
    },
    "path_stops": {
        "id": "serial PRIMARY KEY",
        "path_id": "int",
        "stop_id": "int",
        "stop_order": "int"
    },
    "deployments": {
        "deployment_id": "serial PRIMARY KEY",
        "trip_id": "int",
        "vehicle_id": "int",
        "driver_id": "int",
        "deployed_at": "timestamptz"
    },
    "bookings": {
        "booking_id": "serial PRIMARY KEY",
        "trip_id": "int",
        "user_id": "int",
        "user_name": "text",
        "seats": "int",
        "status": "text",
        "created_at": "timestamptz"
    },
    "audit_logs": {
        "log_id": "serial PRIMARY KEY",
        "action": "text NOT NULL",
        "user_id": "int",
        "entity_type": "text",
        "entity_id": "int",
        "details": "jsonb",
        "created_at": "timestamptz"
    }
}


async def get_actual_columns(conn: asyncpg.Connection, table_name: str) -> Set[str]:
    """Get actual columns from database table"""
    query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = $1
        ORDER BY ordinal_position
    """
    rows = await conn.fetch(query, table_name)
    return {row['column_name'] for row in rows}


async def check_schema_alignment():
    """Main function to check schema alignment"""
    print("=" * 60)
    print("🔍 MOVI SCHEMA ALIGNMENT CHECK")
    print("=" * 60)
    print()
    
    issues_found = []
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to Supabase database")
        print()
        
        for table_name, expected_cols in EXPECTED_SCHEMA.items():
            print(f"📋 Checking table: {table_name}")
            
            # Check if table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, table_name)
            
            if not table_exists:
                print(f"   ❌ Table '{table_name}' does NOT exist!")
                issues_found.append(f"Table '{table_name}' missing")
                print()
                continue
            
            # Get actual columns
            actual_cols = await get_actual_columns(conn, table_name)
            expected_col_names = set(expected_cols.keys())
            
            # Find missing columns
            missing = expected_col_names - actual_cols
            # Find extra columns (in DB but not expected)
            extra = actual_cols - expected_col_names
            
            if missing:
                print(f"   ❌ Missing columns: {', '.join(missing)}")
                for col in missing:
                    issues_found.append(f"{table_name}.{col}")
            
            if extra:
                print(f"   ⚠️  Extra columns (not in backend): {', '.join(extra)}")
            
            if not missing and not extra:
                print(f"   ✅ All columns aligned ({len(actual_cols)} columns)")
            
            print()
        
        await conn.close()
        
        # Summary
        print("=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        if issues_found:
            print(f"\n❌ Found {len(issues_found)} schema issues:\n")
            for issue in issues_found:
                print(f"   • {issue}")
            print("\n⚠️  Run fix_schema_mismatch.sql to resolve these issues.")
            return False
        else:
            print("\n✅ All tables and columns are aligned!")
            print("✅ Backend and Supabase schemas match.")
            return True
            
    except Exception as e:
        print(f"\n❌ Error during schema check: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(check_schema_alignment())
    sys.exit(0 if success else 1)
