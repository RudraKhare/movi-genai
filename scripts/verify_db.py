"""
Quick verification script to test database connection and query data.

Usage:
    python scripts/verify_db.py
"""

import os
from dotenv import load_dotenv

load_dotenv('.env.local')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: Supabase credentials not found in .env.local")
    print("Please complete Supabase setup first.")
    exit(1)

from supabase import create_client, Client

print("=" * 60)
print("🔍 MOVI Database Verification")
print("=" * 60)

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Test 1: Check tables exist
    print("\n📊 Testing table access...")
    tables_to_check = ["stops", "paths", "routes", "daily_trips", "vehicles", "drivers", "bookings"]
    
    for table in tables_to_check:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            print(f"   ✅ {table}: accessible")
        except Exception as e:
            print(f"   ❌ {table}: {e}")
    
    # Test 2: Count records
    print("\n📈 Record counts:")
    stops_count = len(supabase.table("stops").select("*").execute().data)
    paths_count = len(supabase.table("paths").select("*").execute().data)
    routes_count = len(supabase.table("routes").select("*").execute().data)
    trips_count = len(supabase.table("daily_trips").select("*").execute().data)
    vehicles_count = len(supabase.table("vehicles").select("*").execute().data)
    bookings_count = len(supabase.table("bookings").select("*").execute().data)
    
    print(f"   Stops: {stops_count}")
    print(f"   Paths: {paths_count}")
    print(f"   Routes: {routes_count}")
    print(f"   Daily Trips: {trips_count}")
    print(f"   Vehicles: {vehicles_count}")
    print(f"   Bookings: {bookings_count}")
    
    # Test 3: Sample data
    print("\n🚍 Sample Daily Trips:")
    trips = supabase.table("daily_trips").select("*").limit(5).execute().data
    for trip in trips:
        print(f"   • {trip['display_name']}: {trip['booking_status_percentage']}% booked ({trip['live_status']})")
    
    # Test 4: High booking trips (for consequence testing)
    print("\n⚠️  Trips with >50% bookings (tribal knowledge check targets):")
    high_booking_trips = [t for t in supabase.table("daily_trips").select("*").execute().data 
                          if t['booking_status_percentage'] > 50]
    
    if len(high_booking_trips) >= 3:
        print(f"   ✅ Found {len(high_booking_trips)} trips with high bookings")
        for trip in high_booking_trips[:3]:
            print(f"      • {trip['display_name']}: {trip['booking_status_percentage']}%")
    else:
        print(f"   ⚠️  Only {len(high_booking_trips)} trips with >50% bookings (need at least 3)")
    
    # Test 5: Confirmed bookings
    print("\n📝 Booking Status:")
    confirmed = len([b for b in supabase.table("bookings").select("*").execute().data 
                     if b['status'] == 'CONFIRMED'])
    cancelled = len([b for b in supabase.table("bookings").select("*").execute().data 
                    if b['status'] == 'CANCELLED'])
    
    print(f"   Confirmed: {confirmed}")
    print(f"   Cancelled: {cancelled}")
    print(f"   Total: {confirmed + cancelled}")
    
    # Final status
    print("\n" + "=" * 60)
    if trips_count >= 10 and bookings_count >= 30 and len(high_booking_trips) >= 3:
        print("✅ All acceptance criteria met!")
        print("   Ready for Day 3: FastAPI endpoints")
    else:
        print("⚠️  Some criteria not met:")
        if trips_count < 10:
            print(f"   • Need at least 10 trips (found {trips_count})")
        if bookings_count < 30:
            print(f"   • Need at least 30 bookings (found {bookings_count})")
        if len(high_booking_trips) < 3:
            print(f"   • Need at least 3 high-booking trips (found {len(high_booking_trips)})")
        print("   Run: python scripts/seed_db.py")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error connecting to database: {e}")
    print("\nTroubleshooting:")
    print("1. Check .env.local has correct credentials")
    print("2. Verify Supabase project is active")
    print("3. Run migration: migrations/001_init.sql in Supabase SQL Editor")
    print("4. Run seed: python scripts/seed_db.py")
