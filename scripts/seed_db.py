"""
Seed the MOVI database with realistic dummy data.

This script populates all tables with data that matches the assignment requirements:
- Static Assets: Stops, Paths, Routes (for manageRoute page)
- Dynamic Operations: Vehicles, Drivers, Trips, Deployments, Bookings (for busDashboard)

Usage:
    python scripts/seed_db.py

Requirements:
    - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.local
    - Or DATABASE_URL for direct psql connection
"""

import os
import sys
import random
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from multiple locations
load_dotenv('.env')
load_dotenv('.env.local')
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

# Check which database connection to use
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

print("=" * 60)
print("🌱 MOVI Database Seed Script")
print("=" * 60)
print()

# Determine connection method - Prefer asyncpg for reliability
if DATABASE_URL:
    print("✅ Using direct PostgreSQL connection (asyncpg)")
    print(f"📡 Database: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'local'}")
    try:
        import asyncpg
        import asyncio
        USE_SUPABASE = False
        print("✅ asyncpg ready for seeding")
    except ImportError:
        print("❌ asyncpg not installed. Run: pip install asyncpg")
        sys.exit(1)
elif SUPABASE_URL and SUPABASE_SERVICE_KEY:
    print("✅ Using Supabase REST API connection")
    print(f"📡 URL: {SUPABASE_URL}")
    try:
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        USE_SUPABASE = True
        print("✅ Supabase client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        print("💡 Falling back to asyncpg if DATABASE_URL is available")
        if DATABASE_URL:
            import asyncpg
            import asyncio
            USE_SUPABASE = False
        else:
            sys.exit(1)
else:
    print("❌ Error: No database credentials found!")
    print()
    print("Please set environment variables in .env file:")
    print("  Option 1 (Direct PostgreSQL - Recommended):")
    print("    DATABASE_URL=postgresql://user:pass@host:5432/dbname")
    print()
    print("  Option 2 (Supabase REST API):")
    print("    SUPABASE_URL=https://xxx.supabase.co")
    print("    SUPABASE_SERVICE_ROLE_KEY=eyJxxx...")
    print()
    sys.exit(1)

print()

# =============================
# DATA DEFINITIONS
# =============================

# Stops (realistic Bangalore locations)
STOPS_DATA = [
    {"name": "Gavipuram", "latitude": 12.9352, "longitude": 77.5847, "address": "Gavipuram Circle, Bangalore"},
    {"name": "Peenya", "latitude": 13.0358, "longitude": 77.5200, "address": "Peenya Industrial Area"},
    {"name": "Electronic City", "latitude": 12.8458, "longitude": 77.6632, "address": "Electronic City Phase 1"},
    {"name": "Whitefield", "latitude": 12.9698, "longitude": 77.7499, "address": "Whitefield Main Road"},
    {"name": "Koramangala", "latitude": 12.9352, "longitude": 77.6245, "address": "Koramangala 4th Block"},
    {"name": "Indiranagar", "latitude": 12.9784, "longitude": 77.6408, "address": "Indiranagar 100 Feet Road"},
    {"name": "JP Nagar", "latitude": 12.9081, "longitude": 77.5858, "address": "JP Nagar 7th Phase"},
    {"name": "HSR Layout", "latitude": 12.9116, "longitude": 77.6473, "address": "HSR Layout Sector 1"},
    {"name": "Marathahalli", "latitude": 12.9591, "longitude": 77.6974, "address": "Marathahalli Junction"},
    {"name": "Yelahanka", "latitude": 13.1007, "longitude": 77.5963, "address": "Yelahanka New Town"},
    {"name": "BTM Layout", "latitude": 12.9165, "longitude": 77.6101, "address": "BTM 2nd Stage"},
    {"name": "Jayanagar", "latitude": 12.9250, "longitude": 77.5838, "address": "Jayanagar 4th Block"},
]

# Paths (ordered sequences of stops)
PATHS_DATA = [
    {
        "name": "Path-1",
        "description": "North to South corridor",
        "stops": ["Yelahanka", "Peenya", "Gavipuram", "Jayanagar", "JP Nagar"]
    },
    {
        "name": "Path-2",
        "description": "East to West route",
        "stops": ["Whitefield", "Marathahalli", "Indiranagar", "Koramangala", "BTM Layout"]
    },
    {
        "name": "Path-3",
        "description": "Tech park shuttle",
        "stops": ["Electronic City", "HSR Layout", "Koramangala", "Indiranagar", "Whitefield"]
    },
    {
        "name": "Bulk Route",
        "description": "Main commuter path",
        "stops": ["Peenya", "Gavipuram", "Jayanagar", "Koramangala", "Electronic City"]
    }
]

# Routes (Path + Time combinations)
ROUTES_DATA = [
    {"path_name": "Path-1", "display_name": "Path-1 - 08:00", "shift_time": "08:00:00", "direction": "up", "start": "Yelahanka", "end": "JP Nagar"},
    {"path_name": "Path-1", "display_name": "Path-1 - 18:30", "shift_time": "18:30:00", "direction": "down", "start": "JP Nagar", "end": "Yelahanka"},
    {"path_name": "Path-2", "display_name": "Path-2 - 09:15", "shift_time": "09:15:00", "direction": "up", "start": "Whitefield", "end": "BTM Layout"},
    {"path_name": "Path-2", "display_name": "Path-2 - 19:45", "shift_time": "19:45:00", "direction": "down", "start": "BTM Layout", "end": "Whitefield"},
    {"path_name": "Path-3", "display_name": "Path-3 - 07:30", "shift_time": "07:30:00", "direction": "up", "start": "Electronic City", "end": "Whitefield"},
    {"path_name": "Path-3", "display_name": "Path-3 - 20:00", "shift_time": "20:00:00", "direction": "down", "start": "Whitefield", "end": "Electronic City"},
    {"path_name": "Bulk Route", "display_name": "Bulk - 00:01", "shift_time": "00:01:00", "direction": "up", "start": "Peenya", "end": "Electronic City"},
    {"path_name": "Path-1", "display_name": "Path-1 - 22:00", "shift_time": "22:00:00", "direction": "up", "start": "Yelahanka", "end": "JP Nagar"},
]

# Vehicles
VEHICLES_DATA = [
    {"license_plate": "KA01AB1234", "vehicle_type": "Bus", "capacity": 40, "status": "available"},
    {"license_plate": "KA01AB5678", "vehicle_type": "Bus", "capacity": 35, "status": "available"},
    {"license_plate": "KA02CD1111", "vehicle_type": "Cab", "capacity": 4, "status": "available"},
    {"license_plate": "KA02CD2222", "vehicle_type": "Cab", "capacity": 4, "status": "available"},
    {"license_plate": "KA03EF3333", "vehicle_type": "Bus", "capacity": 50, "status": "available"},
    {"license_plate": "KA03EF4444", "vehicle_type": "Bus", "capacity": 45, "status": "available"},
    {"license_plate": "KA04GH5555", "vehicle_type": "Bus", "capacity": 42, "status": "available"},
    {"license_plate": "KA05IJ6666", "vehicle_type": "Cab", "capacity": 6, "status": "available"},
    {"license_plate": "MH12XY7777", "vehicle_type": "Bus", "capacity": 38, "status": "maintenance"},
    {"license_plate": "TN09PQ8888", "vehicle_type": "Bus", "capacity": 40, "status": "available"},
]

# Drivers
DRIVERS_DATA = [
    {"name": "Ramesh Kumar", "phone": "9876543210", "license_number": "KA0120230001", "status": "available"},
    {"name": "Suresh Singh", "phone": "9123456780", "license_number": "KA0120230002", "status": "available"},
    {"name": "Anil Mehta", "phone": "9000000001", "license_number": "KA0120230003", "status": "available"},
    {"name": "Rajesh Sharma", "phone": "9123456781", "license_number": "KA0120230004", "status": "available"},
    {"name": "Sunil Das", "phone": "9876500000", "license_number": "KA0120230005", "status": "available"},
    {"name": "Vijay Reddy", "phone": "9988776655", "license_number": "KA0120230006", "status": "on_trip"},
    {"name": "Prakash Rao", "phone": "9876012345", "license_number": "KA0120230007", "status": "available"},
    {"name": "Ganesh Iyer", "phone": "9123009876", "license_number": "KA0120230008", "status": "off_duty"},
]

# =============================
# SEEDING FUNCTIONS
# =============================

def seed_supabase():
    """Seed using Supabase client"""
    print("\n🌱 Seeding via Supabase client...")
    
    # Clear existing data (in reverse order of dependencies)
    print("🧹 Cleaning existing data...")
    tables = ["audit_logs", "bookings", "deployments", "daily_trips", "drivers", "vehicles", "routes", "path_stops", "paths", "stops"]
    for table in tables:
        try:
            supabase.table(table).delete().neq("id", 0).execute()  # Delete all
        except:
            pass  # Table might be empty
    
    # Insert Stops
    print("📍 Inserting stops...")
    stop_ids = {}
    for stop in STOPS_DATA:
        result = supabase.table("stops").insert(stop).execute()
        stop_ids[stop["name"]] = result.data[0]["stop_id"]
    print(f"   ✅ Inserted {len(stop_ids)} stops")
    
    # Insert Paths
    print("🛤️  Inserting paths...")
    path_ids = {}
    for path in PATHS_DATA:
        result = supabase.table("paths").insert({
            "name": path["name"],
            "description": path["description"]
        }).execute()
        path_ids[path["name"]] = result.data[0]["path_id"]
    print(f"   ✅ Inserted {len(path_ids)} paths")
    
    # Insert Path-Stop mappings
    print("🔗 Linking paths to stops...")
    path_stop_count = 0
    for path in PATHS_DATA:
        pid = path_ids[path["name"]]
        for order, stop_name in enumerate(path["stops"], start=1):
            if stop_name in stop_ids:
                supabase.table("path_stops").insert({
                    "path_id": pid,
                    "stop_id": stop_ids[stop_name],
                    "stop_order": order
                }).execute()
                path_stop_count += 1
    print(f"   ✅ Created {path_stop_count} path-stop links")
    
    # Insert Routes
    print("🚏 Inserting routes...")
    route_ids = {}
    for route in ROUTES_DATA:
        result = supabase.table("routes").insert({
            "path_id": path_ids[route["path_name"]],
            "route_display_name": route["display_name"],
            "shift_time": route["shift_time"],
            "direction": route["direction"],
            "start_point": route["start"],
            "end_point": route["end"],
            "status": "active"
        }).execute()
        route_ids[route["display_name"]] = result.data[0]["route_id"]
    print(f"   ✅ Inserted {len(route_ids)} routes")
    
    # Insert Vehicles
    print("🚌 Inserting vehicles...")
    vehicle_ids = []
    for vehicle in VEHICLES_DATA:
        result = supabase.table("vehicles").insert(vehicle).execute()
        vehicle_ids.append(result.data[0]["vehicle_id"])
    print(f"   ✅ Inserted {len(vehicle_ids)} vehicles")
    
    # Insert Drivers
    print("👨‍✈️ Inserting drivers...")
    driver_ids = []
    for driver in DRIVERS_DATA:
        result = supabase.table("drivers").insert(driver).execute()
        driver_ids.append(result.data[0]["driver_id"])
    print(f"   ✅ Inserted {len(driver_ids)} drivers")
    
    # Insert Daily Trips
    print("🚍 Inserting daily trips...")
    today = datetime.date.today()
    trip_ids = []
    trip_data = []
    
    for i, (route_name, route_id) in enumerate(list(route_ids.items())[:10]):
        booking_pct = random.choice([0, 10, 25, 50, 75, 90])  # Ensure some high bookings
        status = random.choice(["SCHEDULED", "IN_PROGRESS", "COMPLETED"])
        
        trip = {
            "route_id": route_id,
            "display_name": f"{route_name.split(' - ')[0]} - {route_name.split(' - ')[1]}",
            "trip_date": str(today),
            "booking_status_percentage": booking_pct,
            "live_status": status
        }
        result = supabase.table("daily_trips").insert(trip).execute()
        trip_ids.append(result.data[0]["trip_id"])
        trip_data.append(trip)
    
    print(f"   ✅ Inserted {len(trip_ids)} daily trips")
    
    # Insert Deployments
    print("🔗 Creating deployments...")
    for i, trip_id in enumerate(trip_ids[:7]):  # Deploy 7 out of 10 trips
        supabase.table("deployments").insert({
            "trip_id": trip_id,
            "vehicle_id": vehicle_ids[i % len(vehicle_ids)],
            "driver_id": driver_ids[i % len(driver_ids)]
        }).execute()
    print(f"   ✅ Created {min(7, len(trip_ids))} deployments")
    
    # Insert Bookings
    print("📝 Creating bookings...")
    booking_count = 0
    for trip_id in trip_ids:
        num_bookings = random.randint(3, 8)
        for _ in range(num_bookings):
            supabase.table("bookings").insert({
                "trip_id": trip_id,
                "user_id": random.randint(1000, 9999),
                "user_name": f"Employee{random.randint(1,1000)}",
                "seats": random.randint(1, 3),
                "status": random.choice(["CONFIRMED", "CONFIRMED", "CONFIRMED", "CANCELLED"])  # 75% confirmed
            }).execute()
            booking_count += 1
    print(f"   ✅ Created {booking_count} bookings")
    
    # Log initial audit entry
    print("📋 Creating audit log entry...")
    supabase.table("audit_logs").insert({
        "action": "SEED_DATABASE",
        "user_id": 0,
        "entity_type": "system",
        "entity_id": 0,
        "details": {"message": "Initial database seed completed", "timestamp": datetime.datetime.now().isoformat()}
    }).execute()
    
    print("\n✅ Supabase seeding complete!")
    return True

async def seed_postgres():
    """Seed using direct PostgreSQL connection"""
    print("\n🌱 Seeding via PostgreSQL connection...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Clear existing data
        print("🧹 Cleaning existing data...")
        await conn.execute("TRUNCATE TABLE audit_logs, bookings, deployments, daily_trips, drivers, vehicles, routes, path_stops, paths, stops RESTART IDENTITY CASCADE;")
        
        # Insert Stops
        print("📍 Inserting stops...")
        stop_ids = {}
        for stop in STOPS_DATA:
            stop_id = await conn.fetchval(
                "INSERT INTO stops (name, latitude, longitude, address) VALUES ($1, $2, $3, $4) RETURNING stop_id",
                stop["name"], stop["latitude"], stop["longitude"], stop["address"]
            )
            stop_ids[stop["name"]] = stop_id
        print(f"   ✅ Inserted {len(stop_ids)} stops")
        
        # Insert Paths
        print("🛤️  Inserting paths...")
        path_ids = {}
        for path in PATHS_DATA:
            path_id = await conn.fetchval(
                "INSERT INTO paths (name, description) VALUES ($1, $2) RETURNING path_id",
                path["name"], path["description"]
            )
            path_ids[path["name"]] = path_id
        print(f"   ✅ Inserted {len(path_ids)} paths")
        
        # Insert Path-Stop mappings
        print("🔗 Linking paths to stops...")
        path_stop_count = 0
        for path in PATHS_DATA:
            pid = path_ids[path["name"]]
            for order, stop_name in enumerate(path["stops"], start=1):
                if stop_name in stop_ids:
                    await conn.execute(
                        "INSERT INTO path_stops (path_id, stop_id, stop_order) VALUES ($1, $2, $3)",
                        pid, stop_ids[stop_name], order
                    )
                    path_stop_count += 1
        print(f"   ✅ Created {path_stop_count} path-stop links")
        
        # Insert Routes
        print("🚏 Inserting routes...")
        route_ids = {}
        for route in ROUTES_DATA:
            # Convert time string to datetime.time object
            time_parts = route["shift_time"].split(":")
            shift_time_obj = datetime.time(int(time_parts[0]), int(time_parts[1]), int(time_parts[2]))
            
            route_id = await conn.fetchval(
                "INSERT INTO routes (path_id, route_display_name, shift_time, direction, start_point, end_point, status) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING route_id",
                path_ids[route["path_name"]], route["display_name"], shift_time_obj, 
                route["direction"], route["start"], route["end"], "active"
            )
            route_ids[route["display_name"]] = route_id
        print(f"   ✅ Inserted {len(route_ids)} routes")
        
        # Insert Vehicles
        print("🚌 Inserting vehicles...")
        vehicle_ids = []
        for vehicle in VEHICLES_DATA:
            vehicle_id = await conn.fetchval(
                "INSERT INTO vehicles (license_plate, vehicle_type, capacity, status) VALUES ($1, $2, $3, $4) RETURNING vehicle_id",
                vehicle["license_plate"], vehicle["vehicle_type"], vehicle["capacity"], vehicle["status"]
            )
            vehicle_ids.append(vehicle_id)
        print(f"   ✅ Inserted {len(vehicle_ids)} vehicles")
        
        # Insert Drivers
        print("👨‍✈️ Inserting drivers...")
        driver_ids = []
        for driver in DRIVERS_DATA:
            driver_id = await conn.fetchval(
                "INSERT INTO drivers (name, phone, license_number, status) VALUES ($1, $2, $3, $4) RETURNING driver_id",
                driver["name"], driver["phone"], driver["license_number"], driver["status"]
            )
            driver_ids.append(driver_id)
        print(f"   ✅ Inserted {len(driver_ids)} drivers")
        
        # Insert Daily Trips
        print("🚍 Inserting daily trips...")
        today = datetime.date.today()
        trip_ids = []
        
        for i, (route_name, route_id) in enumerate(list(route_ids.items())[:10]):
            booking_pct = random.choice([0, 10, 25, 50, 75, 90])
            status = random.choice(["SCHEDULED", "IN_PROGRESS", "COMPLETED"])
            
            trip_id = await conn.fetchval(
                "INSERT INTO daily_trips (route_id, display_name, trip_date, booking_status_percentage, live_status) VALUES ($1, $2, $3, $4, $5) RETURNING trip_id",
                route_id, f"{route_name.split(' - ')[0]} - {route_name.split(' - ')[1]}", 
                today, booking_pct, status
            )
            trip_ids.append(trip_id)
        
        print(f"   ✅ Inserted {len(trip_ids)} daily trips")
        
        # Insert Deployments
        print("🔗 Creating deployments...")
        for i, trip_id in enumerate(trip_ids[:7]):
            await conn.execute(
                "INSERT INTO deployments (trip_id, vehicle_id, driver_id) VALUES ($1, $2, $3)",
                trip_id, vehicle_ids[i % len(vehicle_ids)], driver_ids[i % len(driver_ids)]
            )
        print(f"   ✅ Created {min(7, len(trip_ids))} deployments")
        
        # Insert Bookings
        print("📝 Creating bookings...")
        booking_count = 0
        for trip_id in trip_ids:
            num_bookings = random.randint(3, 8)
            for _ in range(num_bookings):
                await conn.execute(
                    "INSERT INTO bookings (trip_id, user_id, user_name, seats, status) VALUES ($1, $2, $3, $4, $5)",
                    trip_id, random.randint(1000, 9999), f"Employee{random.randint(1,1000)}",
                    random.randint(1, 3), random.choice(["CONFIRMED", "CONFIRMED", "CONFIRMED", "CANCELLED"])
                )
                booking_count += 1
        print(f"   ✅ Created {booking_count} bookings")
        
        print("\n✅ PostgreSQL seeding complete!")
        
    finally:
        await conn.close()
    
    return True

# =============================
# MAIN EXECUTION
# =============================

if __name__ == "__main__":
    try:
        if USE_SUPABASE:
            success = seed_supabase()
        else:
            success = asyncio.run(seed_postgres())
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 Database seeding completed successfully!")
            print("=" * 60)
            print("\n📊 Quick Stats:")
            print(f"   • Stops: {len(STOPS_DATA)}")
            print(f"   • Paths: {len(PATHS_DATA)}")
            print(f"   • Routes: {len(ROUTES_DATA)}")
            print(f"   • Vehicles: {len(VEHICLES_DATA)}")
            print(f"   • Drivers: {len(DRIVERS_DATA)}")
            print(f"   • Daily Trips: 10+")
            print(f"   • Deployments: 7+")
            print(f"   • Bookings: 30+")
            print("\n✅ Ready for Day 3: FastAPI endpoints & LangGraph tools!")
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
