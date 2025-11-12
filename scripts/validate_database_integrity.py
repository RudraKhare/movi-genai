"""
Comprehensive Database Integrity Validator for MOVI Project
Checks tables, constraints, foreign keys, data integrity
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List

# Load environment
backend_dir = Path(__file__).parent.parent / "backend"
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

async def check_database_integrity():
    """Run all database integrity checks"""
    print("=" * 80)
    print("DATABASE INTEGRITY VALIDATION")
    print("=" * 80)
    
    conn = await asyncpg.connect(DATABASE_URL)
    results = {
        "tables": {},
        "constraints": {},
        "foreign_keys": {},
        "data_counts": {},
        "enum_values": {},
        "issues": []
    }
    
    try:
        # 1. Check all required tables exist
        print("\n[1/7] Checking table existence...")
        required_tables = [
            'stops', 'paths', 'path_stops', 'routes', 'vehicles',
            'drivers', 'daily_trips', 'deployments', 'bookings', 'audit_logs'
        ]
        
        existing_tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = ANY($1::text[])
        """, required_tables)
        
        existing_names = [row['table_name'] for row in existing_tables]
        for table in required_tables:
            exists = table in existing_names
            results["tables"][table] = exists
            status = "✅" if exists else "❌"
            print(f"  {status} {table}")
            if not exists:
                results["issues"].append(f"Missing table: {table}")
        
        # 2. Check data counts
        print("\n[2/7] Checking data counts...")
        for table in existing_names:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            results["data_counts"][table] = count
            print(f"  {table}: {count} rows")
        
        # 3. Check foreign key relationships
        print("\n[3/7] Validating foreign key relationships...")
        fk_checks = [
            ("path_stops", "path_id", "paths", "path_id"),
            ("path_stops", "stop_id", "stops", "stop_id"),
            ("routes", "path_id", "paths", "path_id"),
            ("daily_trips", "route_id", "routes", "route_id"),
            ("deployments", "trip_id", "daily_trips", "trip_id"),
            ("deployments", "driver_id", "drivers", "driver_id"),
            ("deployments", "vehicle_id", "vehicles", "vehicle_id"),
            ("bookings", "trip_id", "daily_trips", "trip_id"),
        ]
        
        for child_table, child_col, parent_table, parent_col in fk_checks:
            if child_table not in existing_names or parent_table not in existing_names:
                continue
                
            orphans = await conn.fetchval(f"""
                SELECT COUNT(*) 
                FROM {child_table} c
                WHERE c.{child_col} IS NOT NULL 
                  AND NOT EXISTS (
                      SELECT 1 FROM {parent_table} p 
                      WHERE p.{parent_col} = c.{child_col}
                  )
            """)
            
            key = f"{child_table}.{child_col} → {parent_table}.{parent_col}"
            results["foreign_keys"][key] = orphans == 0
            status = "✅" if orphans == 0 else f"❌ ({orphans} orphans)"
            print(f"  {status} {key}")
            if orphans > 0:
                results["issues"].append(f"FK violation: {key} has {orphans} orphaned records")
        
        # 4. Check NOT NULL constraints
        print("\n[4/7] Validating NOT NULL constraints...")
        critical_not_nulls = [
            ("stops", "name"),
            ("paths", "path_name"),
            ("routes", "route_name"),
            ("routes", "path_id"),
            ("vehicles", "registration_number"),
            ("drivers", "name"),
        ]
        
        for table, column in critical_not_nulls:
            if table not in existing_names:
                continue
                
            null_count = await conn.fetchval(f"""
                SELECT COUNT(*) FROM {table} WHERE {column} IS NULL
            """)
            
            key = f"{table}.{column}"
            status = "✅" if null_count == 0 else f"❌ ({null_count} nulls)"
            print(f"  {status} {key}")
            if null_count > 0:
                results["issues"].append(f"NULL violation: {key} has {null_count} NULL values")
        
        # 5. Check enum/CHECK constraint values
        print("\n[5/7] Validating CHECK constraint values...")
        
        # Check routes.direction
        if 'routes' in existing_names:
            invalid_directions = await conn.fetch("""
                SELECT route_id, direction 
                FROM routes 
                WHERE direction NOT IN ('up', 'down')
            """)
            
            if invalid_directions:
                print(f"  ❌ routes.direction has {len(invalid_directions)} invalid values")
                results["issues"].append(f"Invalid directions: {[r['direction'] for r in invalid_directions]}")
            else:
                print(f"  ✅ routes.direction (all 'up' or 'down')")
            
            results["enum_values"]["routes.direction"] = len(invalid_directions) == 0
        
        # Check vehicles.vehicle_type
        if 'vehicles' in existing_names:
            invalid_types = await conn.fetch("""
                SELECT vehicle_id, vehicle_type 
                FROM vehicles 
                WHERE vehicle_type NOT IN ('Bus', 'Cab')
            """)
            
            if invalid_types:
                print(f"  ❌ vehicles.vehicle_type has {len(invalid_types)} invalid values")
                results["issues"].append(f"Invalid vehicle types: {[r['vehicle_type'] for r in invalid_types]}")
            else:
                print(f"  ✅ vehicles.vehicle_type (all 'Bus' or 'Cab')")
            
            results["enum_values"]["vehicles.vehicle_type"] = len(invalid_types) == 0
        
        # 6. Check default values
        print("\n[6/7] Validating default values...")
        
        # Check routes.status default
        if 'routes' in existing_names:
            routes_without_status = await conn.fetchval("""
                SELECT COUNT(*) FROM routes WHERE status IS NULL
            """)
            status = "✅" if routes_without_status == 0 else f"❌ ({routes_without_status} null)"
            print(f"  {status} routes.status (default 'active')")
        
        # Check stops.status default
        if 'stops' in existing_names:
            stops_without_status = await conn.fetchval("""
                SELECT COUNT(*) FROM stops WHERE status IS NULL
            """)
            status = "✅" if stops_without_status == 0 else f"❌ ({stops_without_status} null)"
            print(f"  {status} stops.status (default 'Active')")
        
        # 7. Check timestamps
        print("\n[7/7] Validating timestamps...")
        
        for table in existing_names:
            # Check if table has created_at column
            has_created_at = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = $1 AND column_name = 'created_at'
                )
            """, table)
            
            if has_created_at:
                null_timestamps = await conn.fetchval(f"""
                    SELECT COUNT(*) FROM {table} WHERE created_at IS NULL
                """)
                status = "✅" if null_timestamps == 0 else f"❌ ({null_timestamps} null)"
                print(f"  {status} {table}.created_at")
        
        # Summary
        print("\n" + "=" * 80)
        print("INTEGRITY SUMMARY")
        print("=" * 80)
        
        total_tables = len(required_tables)
        valid_tables = sum(1 for v in results["tables"].values() if v)
        print(f"\n✅ Tables: {valid_tables}/{total_tables} exist")
        
        total_fks = len(results["foreign_keys"])
        valid_fks = sum(1 for v in results["foreign_keys"].values() if v)
        print(f"✅ Foreign Keys: {valid_fks}/{total_fks} valid")
        
        total_enums = len(results["enum_values"])
        valid_enums = sum(1 for v in results["enum_values"].values() if v)
        print(f"✅ Enum Values: {valid_enums}/{total_enums} correct")
        
        if results["issues"]:
            print(f"\n❌ Issues Found: {len(results['issues'])}")
            for issue in results["issues"]:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No integrity issues detected!")
        
        return results
        
    finally:
        await conn.close()

if __name__ == "__main__":
    results = asyncio.run(check_database_integrity())
