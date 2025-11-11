"""
Test multiple Supabase connection string formats to find the working one.
"""
import asyncio
import asyncpg
from urllib.parse import urlparse

# Your credentials
PASSWORD = "IbwmqOoYZKb0MFUS"
PROJECT_REF = "fzxxaqqsfniyefbfccwr"
REGION = "ap-south-1"

# Different connection string formats to try
CONNECTION_STRINGS = [
    {
        "name": "Session Pooler - Port 6543 with project ref in username",
        "url": f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-{REGION}.pooler.supabase.com:6543/postgres"
    },
    {
        "name": "Session Pooler - Port 5432 with regular username",
        "url": f"postgresql://postgres:{PASSWORD}@aws-0-{REGION}.pooler.supabase.com:5432/postgres"
    },
    {
        "name": "Session Pooler - Port 6543 with regular username",
        "url": f"postgresql://postgres:{PASSWORD}@aws-0-{REGION}.pooler.supabase.com:6543/postgres"
    },
    {
        "name": "Pooler with project ref - Port 5432",
        "url": f"postgresql://postgres.{PROJECT_REF}:{PASSWORD}@aws-0-{REGION}.pooler.supabase.com:5432/postgres"
    },
]

async def test_connection(conn_string, name):
    """Test a single connection string."""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    
    parsed = urlparse(conn_string)
    print(f"Host: {parsed.hostname}")
    print(f"Port: {parsed.port}")
    print(f"User: {parsed.username}")
    print(f"Database: {parsed.path.lstrip('/')}")
    
    try:
        print("\n🔌 Attempting connection...")
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            ssl='require',
            timeout=10
        )
        
        # Test the connection
        result = await conn.fetchval('SELECT version()')
        await conn.close()
        
        print(f"✅ SUCCESS! Connection works!")
        print(f"   PostgreSQL version: {result[:50]}...")
        print(f"\n🎉 Working connection string:")
        print(f"   {conn_string}")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

async def main():
    """Test all connection strings."""
    print("\n" + "="*70)
    print(" SUPABASE CONNECTION STRING TESTER")
    print("="*70)
    print(f"\nProject Ref: {PROJECT_REF}")
    print(f"Region: {REGION}")
    print(f"Testing {len(CONNECTION_STRINGS)} different formats...\n")
    
    for i, config in enumerate(CONNECTION_STRINGS, 1):
        success = await test_connection(config["url"], f"{i}. {config['name']}")
        if success:
            print(f"\n{'='*70}")
            print(" ✅ FOUND WORKING CONNECTION!")
            print(f"{'='*70}")
            print(f"\nUpdate your .env file with:")
            print(f"DATABASE_URL={config['url']}")
            return
        
        # Small delay between attempts
        await asyncio.sleep(1)
    
    print(f"\n{'='*70}")
    print(" ❌ NO WORKING CONNECTION FOUND")
    print(f"{'='*70}")
    print("\n💡 Possible issues:")
    print("   1. Your Supabase project may not have Session Pooler enabled")
    print("   2. The pooler hostname format may be different for your region")
    print("   3. You may need to enable IPv4 add-on in Supabase settings")
    print("\n📋 Next steps:")
    print("   1. Go to Supabase Dashboard → Settings → Database")
    print("   2. Look for 'Connection Pooling' or 'Session Pooler' settings")
    print("   3. Copy the exact connection string provided there")
    print("   4. Check if there's an option to enable IPv4 support")

if __name__ == "__main__":
    asyncio.run(main())
