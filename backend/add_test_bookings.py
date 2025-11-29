"""Add test bookings to trips for testing"""
import asyncio
from app.core.supabase_client import get_conn
from datetime import date
import random

async def add_test_bookings():
    pool = await get_conn()
    async with pool.acquire() as conn:
        # Get today's trips
        trips = await conn.fetch('''
            SELECT t.trip_id, t.display_name, t.live_status, t.booking_status_percentage,
                   r.route_name, r.shift_time
            FROM daily_trips t
            LEFT JOIN routes r ON t.route_id = r.route_id
            WHERE t.trip_date = CURRENT_DATE
            ORDER BY r.shift_time
        ''')
        
        print('=== Today\'s Trips ===')
        for t in trips:
            print(f"Trip {t['trip_id']}: {t['display_name']} | Status: {t['live_status']} | Booked: {t['booking_status_percentage']}%")
        
        if not trips:
            print("\nNo trips found for today!")
            return
        
        # Check existing bookings count
        booking_count = await conn.fetchval('SELECT COUNT(*) FROM bookings')
        print(f'\nExisting bookings in database: {booking_count}')
        
        # Test users for bookings
        test_users = [
            (101, "Rahul Sharma"),
            (102, "Priya Patel"),
            (103, "Amit Kumar"),
            (104, "Sneha Gupta"),
            (105, "Vikram Singh"),
            (106, "Anita Reddy"),
            (107, "Raj Malhotra"),
            (108, "Kavitha Nair"),
            (109, "Deepak Verma"),
            (110, "Sunita Joshi"),
            (111, "Arjun Mehta"),
            (112, "Neha Agarwal"),
            (113, "Suresh Pillai"),
            (114, "Lakshmi Iyer"),
            (115, "Kiran Desai"),
            (116, "Pooja Saxena"),
        ]
        
        # Skip last 2 trips (leave them without bookings)
        trips_to_book = trips[:-2] if len(trips) > 2 else trips
        trips_without_bookings = trips[-2:] if len(trips) > 2 else []
        
        print(f"\n📋 Will add bookings to {len(trips_to_book)} trips")
        print(f"⏭️  Leaving {len(trips_without_bookings)} trips without bookings")
        
        bookings_added = 0
        user_index = 0
        
        for i, trip in enumerate(trips_to_book):
            trip_id = trip['trip_id']
            
            # Vary number of bookings per trip (2-5 bookings)
            num_bookings = random.randint(2, 5)
            
            print(f"\n🚌 Trip {trip_id}: {trip['display_name']}")
            
            for j in range(num_bookings):
                user_id, user_name = test_users[user_index % len(test_users)]
                user_index += 1
                seats = random.randint(1, 3)  # 1-3 seats per booking
                
                # Check if booking already exists
                existing = await conn.fetchval('''
                    SELECT booking_id FROM bookings 
                    WHERE trip_id = $1 AND user_id = $2
                ''', trip_id, user_id)
                
                if not existing:
                    await conn.execute('''
                        INSERT INTO bookings (trip_id, user_id, user_name, seats, status)
                        VALUES ($1, $2, $3, $4, 'CONFIRMED')
                    ''', trip_id, user_id, user_name, seats)
                    print(f"  ✅ {user_name} ({seats} seat(s))")
                    bookings_added += 1
                else:
                    print(f"  ⏭️ Already exists: {user_name}")
        
        # Update booking_status_percentage for all trips
        print("\n📊 Updating booking percentages...")
        for trip in trips:
            trip_id = trip['trip_id']
            total_seats = await conn.fetchval('''
                SELECT COALESCE(SUM(seats), 0) FROM bookings 
                WHERE trip_id = $1 AND status = 'CONFIRMED'
            ''', trip_id)
            
            # Calculate percentage (assuming 40 seat capacity)
            percentage = min(100, int((total_seats / 40) * 100))
            
            await conn.execute('''
                UPDATE daily_trips SET booking_status_percentage = $1 WHERE trip_id = $2
            ''', percentage, trip_id)
        
        print(f'\n✅ Added {bookings_added} new bookings!')
        
        # Show final state
        print('\n' + '='*60)
        print('=== FINAL BOOKING SUMMARY ===')
        print('='*60)
        summary = await conn.fetch('''
            SELECT t.trip_id, t.display_name, t.booking_status_percentage,
                   COUNT(b.booking_id) as booking_count,
                   COALESCE(SUM(b.seats), 0) as total_seats
            FROM daily_trips t
            LEFT JOIN bookings b ON t.trip_id = b.trip_id AND b.status = 'CONFIRMED'
            WHERE t.trip_date = CURRENT_DATE
            GROUP BY t.trip_id, t.display_name, t.booking_status_percentage
            ORDER BY t.trip_id
        ''')
        
        for s in summary:
            status = "🟢" if s['booking_count'] > 0 else "⚪"
            print(f"{status} Trip {s['trip_id']}: {s['display_name'][:25]:<25} | {s['booking_count']} bookings | {s['total_seats']} seats | {s['booking_status_percentage']}%")

if __name__ == "__main__":
    asyncio.run(add_test_bookings())
