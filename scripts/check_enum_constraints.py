"""
Check database enum/check constraints and detect mismatches with backend values.
"""
import asyncio
import asyncpg
import re
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Tuple

# Load environment variables
backend_dir = Path(__file__).parent.parent / "backend"
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

async def get_check_constraints():
    """Retrieve all check constraints from the database."""
    conn = await asyncpg.connect(DATABASE_URL)
    
    query = """
        SELECT 
            conname AS constraint_name,
            conrelid::regclass::text AS table_name,
            pg_get_constraintdef(oid) AS definition
        FROM pg_constraint
        WHERE contype = 'c'
        ORDER BY conrelid::regclass::text, conname;
    """
    
    rows = await conn.fetch(query)
    await conn.close()
    return rows

def parse_enum_values(definition: str) -> List[str]:
    """
    Parse allowed values from CHECK constraint definition.
    Example: "CHECK ((direction = ANY (ARRAY['Up'::text, 'Down'::text])))"
    Returns: ['Up', 'Down']
    """
    # Pattern to match values in ARRAY['value1', 'value2', ...]
    pattern = r"'([^']+)'(?:::text)?"
    matches = re.findall(pattern, definition)
    return matches

def detect_mismatches(constraints: List) -> Dict[str, Dict]:
    """
    Detect potential mismatches between database constraints and backend values.
    """
    mismatches = {}
    
    for constraint in constraints:
        table_name = constraint['table_name']
        constraint_name = constraint['constraint_name']
        definition = constraint['definition']
        
        # Extract column name from constraint name (e.g., "routes_direction_check" -> "direction")
        # or from definition
        column_match = re.search(r'CHECK \(\((\w+)', definition)
        if not column_match:
            continue
        
        column_name = column_match.group(1)
        
        # Parse allowed values
        allowed_values = parse_enum_values(definition)
        
        if allowed_values:
            # Check for case mismatches
            upper_values = [v.upper() for v in allowed_values]
            lower_values = [v.lower() for v in allowed_values]
            
            # If values have mixed case, likely need normalization
            has_mixed_case = any(v != v.lower() and v != v.upper() for v in allowed_values)
            
            key = f"{table_name}.{column_name}"
            mismatches[key] = {
                'constraint_name': constraint_name,
                'table': table_name,
                'column': column_name,
                'allowed_values': allowed_values,
                'needs_normalization': has_mixed_case,
                'definition': definition
            }
    
    return mismatches

async def main():
    print("=" * 80)
    print("DATABASE CHECK CONSTRAINT ANALYSIS")
    print("=" * 80)
    
    constraints = await get_check_constraints()
    
    print(f"\nFound {len(constraints)} check constraints\n")
    
    # Display all constraints
    print("ALL CHECK CONSTRAINTS:")
    print("-" * 80)
    for c in constraints:
        print(f"\n{c['table_name']}.{c['constraint_name']}:")
        print(f"  {c['definition']}")
    
    # Detect mismatches
    mismatches = detect_mismatches(constraints)
    
    print("\n" + "=" * 80)
    print("ENUM VALUE ANALYSIS")
    print("=" * 80)
    
    for key, info in mismatches.items():
        print(f"\n{key}:")
        print(f"  Constraint: {info['constraint_name']}")
        print(f"  Allowed values: {info['allowed_values']}")
        print(f"  Needs normalization: {info['needs_normalization']}")
        
        if info['needs_normalization']:
            print(f"  ⚠️  MISMATCH DETECTED: Mixed case values require backend normalization")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    # Routes direction issue
    if 'routes.direction' in mismatches:
        info = mismatches['routes.direction']
        print(f"\n❌ routes.direction:")
        print(f"   Database expects: {info['allowed_values']}")
        print(f"   Backend likely sends: ['UP', 'DOWN'] or ['up', 'down']")
        print(f"   Fix: Normalize to title case before insertion")
    
    # Check for other enum-like constraints
    for key, info in mismatches.items():
        if key != 'routes.direction' and info['allowed_values']:
            print(f"\n✓ {key}:")
            print(f"   Allowed: {info['allowed_values']}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
