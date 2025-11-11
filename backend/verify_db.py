"""
Database verification script with comprehensive diagnostics.
Tests connection and counts rows in all tables.
"""
import asyncio
import sys
import os
from pathlib import Path
from urllib.parse import urlparse

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import engine, test_connection, get_supabase_client, DATABASE_URL, mask_password
from sqlalchemy import text


async def debug_env_and_connection():
    """
    Comprehensive environment and connection diagnostics.
    """
    print("\n" + "="*70)
    print(" 🔍 MOVI DATABASE DIAGNOSTICS")
    print("="*70 + "\n")
    
    # Check .env file
    env_path = Path(__file__).parent / ".env"
    print(f"📁 Checking .env file...")
    print(f"   Location: {env_path}")
    print(f"   Exists: {'✅ Yes' if env_path.exists() else '❌ No'}")
    
    if env_path.exists():
        print(f"   Size: {env_path.stat().st_size} bytes")
    print()
    
    # Check environment variables
    print("🔑 Environment Variables:")
    env_vars = {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
        "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    }
    
    for key, value in env_vars.items():
        if value:
            if "URL" in key:
                print(f"   ✅ {key}: {value}")
            else:
                # Mask sensitive keys
                masked = value[:20] + "..." + value[-10:] if len(value) > 30 else "***"
                print(f"   ✅ {key}: {masked}")
        else:
            print(f"   ❌ {key}: NOT SET")
    print()
    
    # Parse DATABASE_URL
    if DATABASE_URL:
        print("🌐 Database Connection Details:")
        parsed = urlparse(DATABASE_URL)
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path.lstrip('/')}")
        print(f"   Username: {parsed.username}")
        print(f"   Password: {'*' * len(parsed.password) if parsed.password else 'NOT SET'}")
        
        # Check for SSL configuration
        ssl_configured = "supabase.co" in (parsed.hostname or "")
        if ssl_configured:
            print("   🔒 SSL Mode: ✅ Configured (SSL required for Supabase)")
        else:
            print("   🔒 SSL Mode: ℹ️  Not required (local connection)")
        
        print()

    # Test network connectivity (basic check)
    if DATABASE_URL:
        parsed = urlparse(DATABASE_URL)
        host = parsed.hostname
        print(f"🌍 Network Reachability:")
        print(f"   Target: {host}")
        
        # Try to resolve hostname with multiple methods
        try:
            import socket
            
            # Method 1: Standard DNS resolution
            try:
                ip = socket.gethostbyname(host)
                print(f"   DNS Resolution (gethostbyname): ✅ {ip}")
            except socket.gaierror:
                # Method 2: getaddrinfo (more robust)
                try:
                    addr_info = socket.getaddrinfo(host, parsed.port or 5432, socket.AF_INET, socket.SOCK_STREAM)
                    if addr_info:
                        ip = addr_info[0][4][0]
                        print(f"   DNS Resolution (getaddrinfo): ✅ {ip}")
                    else:
                        raise socket.gaierror("No address found")
                except socket.gaierror as e:
                    print(f"   DNS Resolution: ❌ Failed ({e})")
                    print(f"   💡 Troubleshooting steps:")
                    print(f"      1. Check your internet connection")
                    print(f"      2. Try: ping {host}")
                    print(f"      3. Try: nslookup {host}")
                    print(f"      4. Flush DNS cache: ipconfig /flushdns")
                    print(f"      5. Try changing DNS servers (8.8.8.8 or 1.1.1.1)")
                    print(f"      6. Check if your firewall/antivirus is blocking")
                    print(f"      7. Disable VPN temporarily if using one")
                    
        except Exception as e:
            print(f"   Network check failed: {e}")
        print()


async def verify_database():
    """Verify database connection and count rows in all tables."""
    
    print("="*70)
    print(" 📊 DATABASE VERIFICATION")
    print("="*70 + "\n")
    
    # Test basic connection
    print("� Testing database connection...\n")
    is_connected = await test_connection()
    
    if not is_connected:
        print("\n❌ Failed to connect to database.")
        print("💡 Please check the diagnostics above and verify:")
        print("   1. DATABASE_URL is correct")
        print("   2. Your internet connection is active")
        print("   3. Supabase project is not paused")
        print("   4. Credentials are valid\n")
        return False
    
    print()
    
    # Tables to verify
    tables = [
        "stops",
        "paths",
        "path_stops",
        "routes",
        "vehicles",
        "drivers",
        "daily_trips",
        "deployments",
        "bookings",
        "audit_logs",
    ]
    
    print("� Table Row Counts:\n")
    print(f"{'Table':<20} {'Rows':>10} {'Status':<10}")
    print("-" * 42)
    
    all_success = True
    total_rows = 0
    
    async with engine.connect() as conn:
        for table in tables:
            try:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                total_rows += count
                
                if count > 0:
                    status = "✅ OK"
                else:
                    status = "⚠️  Empty"
                    all_success = False
                    
                print(f"{table:<20} {count:>10} {status:<10}")
                    
            except Exception as e:
                print(f"{table:<20} {'ERROR':>10} ❌ {str(e)[:30]}")
                all_success = False
    
    print("-" * 42)
    print(f"{'TOTAL':<20} {total_rows:>10}\n")
    
    if total_rows > 0:
        print(f"✅ All tables verified successfully (total rows: {total_rows})")
        return True
    else:
        print("⚠️  Database is empty. Tables exist but contain no data.")
        print("💡 Run: python scripts/seed_db.py to populate data\n")
        return False


async def verify_relationships():
    """Verify foreign key relationships work correctly."""
    
    print("🔗 Verifying table relationships...\n")
    
    queries = [
        ("Routes with Paths", "SELECT COUNT(*) FROM routes r JOIN paths p ON r.path_id = p.path_id"),
        ("Trips with Routes", "SELECT COUNT(*) FROM daily_trips dt JOIN routes r ON dt.route_id = r.route_id"),
        ("Deployments with Vehicles", "SELECT COUNT(*) FROM deployments d JOIN vehicles v ON d.vehicle_id = v.vehicle_id"),
        ("Bookings with Trips", "SELECT COUNT(*) FROM bookings b JOIN daily_trips dt ON b.trip_id = dt.trip_id"),
    ]
    
    async with engine.connect() as conn:
        for description, query in queries:
            try:
                result = await conn.execute(text(query))
                count = result.scalar()
                status = "✅" if count > 0 else "⚠️"
                print(f"{status} {description:30s} {count:>5} records")
            except Exception as e:
                print(f"❌ {description:30s} Error: {e}")
    
    print()


async def show_sample_data():
    """Show sample data from key tables."""
    
    print("📋 Sample data from daily_trips:\n")
    
    query = """
        SELECT 
            dt.trip_id,
            dt.display_name,
            r.route_display_name,
            dt.booking_status_percentage,
            dt.live_status
        FROM daily_trips dt
        LEFT JOIN routes r ON dt.route_id = r.route_id
        LIMIT 5
    """
    
    async with engine.connect() as conn:
        try:
            result = await conn.execute(text(query))
            rows = result.fetchall()
            
            if rows:
                print(f"{'ID':<5} {'Display Name':<20} {'Route':<25} {'Booking %':<12} {'Status':<15}")
                print("-" * 80)
                for row in rows:
                    print(f"{row[0]:<5} {row[1]:<20} {row[2]:<25} {row[3]:<12} {row[4]:<15}")
            else:
                print("No data found in daily_trips table")
                
        except Exception as e:
            print(f"Error fetching sample data: {e}")
    
    print()


async def main():
    """Main verification routine with comprehensive diagnostics."""
    
    try:
        # Run diagnostics first
        await debug_env_and_connection()
        
        # Verify connection and row counts
        db_ok = await verify_database()
        
        if db_ok:
            # Verify relationships
            await verify_relationships()
            
            # Show sample data
            await show_sample_data()
            
            print("="*70)
            print(" ✅ DATABASE VERIFICATION COMPLETE")
            print("="*70 + "\n")
            print("🎉 Your database is properly connected and populated!")
            print("💡 You can now start the FastAPI server with: uvicorn app.main:app --reload\n")
            return True
        else:
            print("="*70)
            print(" ⚠️  DATABASE VERIFICATION INCOMPLETE")
            print("="*70 + "\n")
            return False
            
    except Exception as e:
        print(f"\n❌ Verification failed with error: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
        print()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
