import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded .env from {env_path}")
else:
    print(f"⚠️ No .env file found at {env_path}")

async def test_dashboard_query():
    db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if not db_url:
        print("❌ DATABASE_URL or SUPABASE_DB_URL not set!")
        return
    
    conn = await asyncpg.connect(db_url)
    
    # Run the exact same query as dashboard
    trips = await conn.fetch("""
        SELECT 
            dt.trip_id,
            dt.route_id,
            dt.trip_date,
            dt.display_name,
            dt.booking_status_percentage,
            r.route_name,
            r.shift_time,
            r.direction,
            r.start_point,
            r.end_point,
            dt.live_status,
            d.vehicle_id,
            d.driver_id,
            v.registration_number,
            v.capacity,
            dr.name AS driver_name,
            p.path_name,
            COUNT(b.booking_id) FILTER (WHERE b.status='CONFIRMED') AS booked_count,
            COALESCE(SUM(b.seats) FILTER (WHERE b.status='CONFIRMED'), 0) AS seats_booked
        FROM daily_trips dt
        JOIN routes r ON dt.route_id = r.route_id
        LEFT JOIN paths p ON r.path_id = p.path_id
        LEFT JOIN deployments d ON d.trip_id = dt.trip_id
        LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
        LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
        LEFT JOIN bookings b ON b.trip_id = dt.trip_id
        GROUP BY 
            dt.trip_id, dt.route_id, dt.trip_date, dt.display_name, dt.booking_status_percentage,
            r.route_name, r.shift_time, r.direction, r.start_point, r.end_point,
            dt.live_status, d.vehicle_id, d.driver_id, v.registration_number, v.capacity, dr.name,
            p.path_name
        ORDER BY dt.trip_date DESC, r.shift_time
        LIMIT 10
    """)
    
    print(f"\n📊 Query returned {len(trips)} trips\n")
    
    for trip in trips:
        print(f"Trip {trip['trip_id']}: {trip['route_name']}")
        print(f"  Confirmed bookings: {trip['booked_count']}")
        print(f"  Seats booked: {trip['seats_booked']}")
        print(f"  Vehicle: {trip['vehicle_id']}, Capacity: {trip['capacity']}")
        print()
    
    # Now check raw bookings for these trips
    print("\n🔍 Checking raw booking data:")
    raw_bookings = await conn.fetch("""
        SELECT trip_id, status, COUNT(*) as count, SUM(seats) as total_seats
        FROM bookings
        WHERE trip_id IN (SELECT trip_id FROM daily_trips LIMIT 10)
        GROUP BY trip_id, status
        ORDER BY trip_id
    """)
    
    for row in raw_bookings:
        print(f"  Trip {row['trip_id']}: Status={row['status']}, Count={row['count']}, Seats={row['total_seats']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(test_dashboard_query())
