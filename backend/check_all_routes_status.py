#!/usr/bin/env python3
"""
Check current status of all routes with driver, vehicle, and timing info
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def check_all_routes_status():
    """Check status of all routes with assignments and timing"""
    try:
        from app.core.supabase_client import get_conn
        
        conn = await get_conn()
        try:
            print("🔍 ALL ROUTES STATUS REPORT")
            print("=" * 80)
            print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
            # Get all routes with trip details and assignments
            query = """
            SELECT 
                r.route_id,
                r.route_name,
                r.start_location,
                r.end_location,
                r.distance_km,
                r.estimated_duration_minutes,
                dt.trip_id,
                dt.display_name as trip_name,
                dt.trip_date,
                dt.live_status,
                dt.booking_status_percentage,
                d.deployment_id,
                d.vehicle_id,
                d.driver_id,
                d.deployed_at,
                v.registration_number as vehicle_reg,
                v.vehicle_type,
                v.capacity,
                dr.name as driver_name,
                dr.license_number
            FROM routes r
            LEFT JOIN daily_trips dt ON r.route_id = dt.route_id
            LEFT JOIN deployments d ON dt.trip_id = d.trip_id
            LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
            LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
            ORDER BY r.route_id, dt.trip_date, dt.trip_id
            """
            
            results = await conn.fetch(query)
            
            if not results:
                print("❌ No routes found in database")
                return
            
            current_route_id = None
            route_count = 0
            trip_count = 0
            assigned_count = 0
            
            for row in results:
                route_id = row['route_id']
                
                # New route header
                if current_route_id != route_id:
                    current_route_id = route_id
                    route_count += 1
                    
                    if route_count > 1:
                        print()  # Spacing between routes
                    
                    print(f"🛤️  ROUTE {route_id}: {row['route_name']}")
                    print(f"   📍 {row['start_location']} → {row['end_location']}")
                    print(f"   📏 Distance: {row['distance_km']} km | ⏱️  Duration: {row['estimated_duration_minutes']} min")
                    print(f"   {'─' * 70}")
                
                # Trip details
                if row['trip_id']:
                    trip_count += 1
                    print(f"   🚌 Trip {row['trip_id']}: {row['trip_name']}")
                    print(f"      📅 Date: {row['trip_date']}")
                    print(f"      📊 Status: {row['live_status']} | Booking: {row['booking_status_percentage']}%")
                    
                    # Assignment status
                    if row['deployment_id']:
                        assigned_count += 1
                        vehicle_info = f"{row['vehicle_reg']} ({row['vehicle_type']}, {row['capacity']} seats)" if row['vehicle_reg'] else "None"
                        driver_info = f"{row['driver_name']} (License: {row['license_number']})" if row['driver_name'] else "None"
                        
                        print(f"      ✅ ASSIGNED (Deployment {row['deployment_id']})")
                        print(f"         🚗 Vehicle: {vehicle_info}")
                        print(f"         👨‍💼 Driver: {driver_info}")
                        print(f"         📋 Deployed: {row['deployed_at']}")
                    else:
                        print(f"      ⏳ NOT ASSIGNED")
                    print()
                else:
                    print(f"   📝 No trips scheduled for this route")
                    print()
            
            # Summary
            print("=" * 80)
            print("📊 SUMMARY STATISTICS")
            print("=" * 80)
            print(f"🛤️  Total Routes: {route_count}")
            print(f"🚌 Total Trips: {trip_count}")
            print(f"✅ Assigned Trips: {assigned_count}")
            print(f"⏳ Unassigned Trips: {trip_count - assigned_count}")
            
            if trip_count > 0:
                assignment_rate = (assigned_count / trip_count) * 100
                print(f"📈 Assignment Rate: {assignment_rate:.1f}%")
            
            # Deployment status breakdown
            print("\n🔍 DEPLOYMENT STATUS BREAKDOWN:")
            deployment_query = """
            SELECT 
                COUNT(*) as total_deployments,
                COUNT(vehicle_id) as complete_assignments,
                COUNT(*) - COUNT(vehicle_id) as orphaned_deployments
            FROM deployments
            """
            
            deployment_stats = await conn.fetchrow(deployment_query)
            print(f"   📋 Total Deployments: {deployment_stats['total_deployments']}")
            print(f"   ✅ Complete Assignments: {deployment_stats['complete_assignments']}")
            print(f"   🔄 Orphaned Deployments: {deployment_stats['orphaned_deployments']}")
            
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_all_routes_status())
