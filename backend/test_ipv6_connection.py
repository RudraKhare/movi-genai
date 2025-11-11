"""
Test IPv6 connectivity to Supabase directly.
This script tests if asyncpg can connect using IPv6.
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

async def test_ipv6_connection():
    """Test direct connection with IPv6 address."""
    
    print("🧪 Testing IPv6 Connection to Supabase\n")
    
    # Get credentials from environment
    db_url = os.getenv("DATABASE_URL")
    
    # Parse the URL to extract components
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    
    # Try with hostname first
    print(f"🔍 Attempting connection to: {parsed.hostname}")
    print(f"   Username: {parsed.username}")
    print(f"   Database: {parsed.path.lstrip('/')}")
    print(f"   Port: {parsed.port or 5432}\n")
    
    try:
        print("📡 Method 1: Connecting with hostname...")
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            ssl='require',
            timeout=10
        )
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        print(f"✅ Connection successful! Result: {result}\n")
        return True
    except Exception as e:
        print(f"❌ Method 1 failed: {e}\n")
        
        # Try with IPv6 address directly
        print("📡 Method 2: Trying with IPv6 address directly...")
        ipv6_address = "2406:da18:243:741b:8c33:603b:36c:e5da"
        print(f"   Using IP: {ipv6_address}")
        
        try:
            conn = await asyncpg.connect(
                host=ipv6_address,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                ssl='require',
                timeout=10
            )
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            print(f"✅ IPv6 connection successful! Result: {result}\n")
            print("💡 Your system can connect via IPv6. Will update configuration.\n")
            return True
        except Exception as e2:
            print(f"❌ Method 2 also failed: {e2}\n")
            
            # Check Windows IPv6 status
            print("🔍 Checking Windows IPv6 configuration...")
            import subprocess
            try:
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                if 'IPv6' in result.stdout:
                    print("✅ IPv6 is enabled on Windows")
                else:
                    print("⚠️  IPv6 may not be properly configured")
            except Exception:
                pass
            
            print("\n💡 Possible solutions:")
            print("   1. Enable IPv6 in Windows network settings")
            print("   2. Check if your ISP supports IPv6")
            print("   3. Contact Supabase support to enable IPv4 for your project")
            print("   4. Use a VPN that supports IPv6")
            print("   5. Run: netsh interface ipv6 show interface")
            
            return False

if __name__ == "__main__":
    success = asyncio.run(test_ipv6_connection())
    exit(0 if success else 1)
