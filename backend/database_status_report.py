#!/usr/bin/env python3
"""
Comprehensive database status report
Shows all routes, trips, vehicles, drivers, and deployments
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

async def generate_status_report():
    """Generate comprehensive status report"""
    try:
        from app.core.supabase_client import get_conn
        
        conn = await get_conn()
        try:
            print("📊 COMPREHENSIVE DATABASE STATUS REPORT")
            print("=" * 80)
            print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
            # 1. ROUTES
            print("\n🛣️  ROUTES")
            print("-" * 40)
            routes = await conn.fetch("""
                SELECT route_id, path_id, route_name, shift_time, direction,
                       start_point, end_point, status, created_at
                FROM routes 
                ORDER BY route_id
            """)
            
            for route in routes:
                print(f"Route {route['route_id']}: {route['route_name']}")
                print(f"  📍 {route['start_point']} → {route['end_point']}")
                print(f"  � Shift Time: {route['shift_time']}")
                print(f"  ↗️  Direction: {route['direction']}")
                print(f"  📊 Status: {route['status']}")
                print(f"  🏷️  Path ID: {route['path_id']}")
                print()
            
            # 2. VEHICLES
            print("\n🚐 VEHICLES")
            print("-" * 40)
            vehicles = await conn.fetch("""
                SELECT vehicle_id, registration_number, vehicle_type, capacity, 
                       status, created_at
                FROM vehicles 
                ORDER BY vehicle_id
            """)
            
            for vehicle in vehicles:
                print(f"Vehicle {vehicle['vehicle_id']}: {vehicle['registration_number']}")
                print(f"  🚗 Type: {vehicle['vehicle_type']}")
                print(f"  👥 Capacity: {vehicle['capacity']}")
                print(f"  📊 Status: {vehicle['status']}")
                print(f"  � Created: {vehicle['created_at'].strftime('%Y-%m-%d %H:%M')}")
                print()
            
            # 3. DRIVERS
            print("\n👨‍✈️ DRIVERS")
            print("-" * 40)
            drivers = await conn.fetch("""
                SELECT driver_id, name, phone, license_number, 
                       status, created_at
                FROM drivers 
                ORDER BY driver_id
            """)
            
            for driver in drivers:
                print(f"Driver {driver['driver_id']}: {driver['name']}")
                print(f"  🆔 License: {driver['license_number']}")
                print(f"  📱 Phone: {driver['phone']}")
                print(f"  � Status: {driver['status']}")
                print(f"  � Created: {driver['created_at'].strftime('%Y-%m-%d %H:%M')}")
                print()
            
            # 4. DAILY TRIPS
            print("\n🗓️  DAILY TRIPS")
            print("-" * 40)
            trips = await conn.fetch("""
                SELECT dt.trip_id, dt.route_id, dt.display_name, dt.trip_date,
                       dt.booking_status_percentage, dt.live_status,
                       r.route_name, r.start_point, r.end_point, r.shift_time
                FROM daily_trips dt
                JOIN routes r ON dt.route_id = r.route_id
                ORDER BY dt.trip_id
            """)
            
            for trip in trips:
                print(f"Trip {trip['trip_id']}: {trip['display_name']}")
                print(f"  🛣️  Route: {trip['route_name']} (ID: {trip['route_id']})")
                print(f"  📍 {trip['start_point']} → {trip['end_point']}")
                print(f"  🕐 Shift: {trip['shift_time']}")
                print(f"  📅 Date: {trip['trip_date']}")
                print(f"  📊 Booking: {trip['booking_status_percentage']}%")
                print(f"  🔴 Live Status: {trip['live_status']}")
                print()
            
            # 5. DEPLOYMENTS (Most Important!)
            print("\n🚀 DEPLOYMENTS & ASSIGNMENTS")
            print("-" * 40)
            deployments = await conn.fetch("""
                SELECT d.deployment_id, d.trip_id, d.vehicle_id, d.driver_id,
                       d.deployed_at,
                       dt.display_name, dt.trip_date,
                       v.registration_number, v.vehicle_type,
                       dr.name as driver_name, dr.phone
                FROM deployments d
                JOIN daily_trips dt ON d.trip_id = dt.trip_id
                LEFT JOIN vehicles v ON d.vehicle_id = v.vehicle_id
                LEFT JOIN drivers dr ON d.driver_id = dr.driver_id
                ORDER BY d.deployment_id
            """)
            
            assigned_trips = set()
            orphaned_deployments = []
            complete_deployments = []
            
            for dep in deployments:
                assigned_trips.add(dep['trip_id'])
                
                print(f"Deployment {dep['deployment_id']}:")
                print(f"  🗓️  Trip: {dep['display_name']} (ID: {dep['trip_id']})")
                print(f"  📅 Date: {dep['trip_date']}")
                
                if dep['vehicle_id'] and dep['driver_id']:
                    # Complete deployment
                    complete_deployments.append(dep['deployment_id'])
                    print(f"  ✅ COMPLETE ASSIGNMENT")
                    print(f"  🚐 Vehicle: {dep['registration_number']} ({dep['vehicle_type']}) [ID: {dep['vehicle_id']}]")
                    print(f"  👨‍✈️ Driver: {dep['driver_name']} ({dep['phone']}) [ID: {dep['driver_id']}]")
                    print(f"  ⏰ Deployed: {dep['deployed_at']}")
                elif dep['vehicle_id'] and not dep['driver_id']:
                    print(f"  ⚠️  PARTIAL: Vehicle Only")
                    print(f"  🚐 Vehicle: {dep['registration_number']} ({dep['vehicle_type']}) [ID: {dep['vehicle_id']}]")
                    print(f"  👨‍✈️ Driver: NOT ASSIGNED")
                elif not dep['vehicle_id'] and dep['driver_id']:
                    print(f"  ⚠️  PARTIAL: Driver Only")
                    print(f"  🚐 Vehicle: NOT ASSIGNED")
                    print(f"  👨‍✈️ Driver: {dep['driver_name']} ({dep['phone']}) [ID: {dep['driver_id']}]")
                else:
                    # Orphaned deployment
                    orphaned_deployments.append(dep['deployment_id'])
                    print(f"  🔴 ORPHANED DEPLOYMENT")
                    print(f"  🚐 Vehicle: NOT ASSIGNED")
                    print(f"  👨‍✈️ Driver: NOT ASSIGNED")
                    print(f"  ⏰ Created: {dep['deployed_at'] or 'Unknown'}")
                
                print()
            
            # 6. UNASSIGNED TRIPS
            print("\n🆓 UNASSIGNED TRIPS")
            print("-" * 40)
            all_trips = await conn.fetch("SELECT trip_id, display_name, trip_date FROM daily_trips ORDER BY trip_id")
            unassigned_trips = [trip for trip in all_trips if trip['trip_id'] not in assigned_trips]
            
            if unassigned_trips:
                for trip in unassigned_trips:
                    print(f"Trip {trip['trip_id']}: {trip['display_name']}")
                    print(f"  📅 Date: {trip['trip_date']}")
                    print(f"  📊 Status: NO DEPLOYMENT")
                    print()
            else:
                print("✅ All trips have deployments (though some may be incomplete)")
                print()
            
            # 7. SUMMARY STATISTICS
            print("\n📈 SUMMARY STATISTICS")
            print("-" * 40)
            total_trips = len(all_trips)
            total_deployments = len(deployments)
            complete_assignments = len(complete_deployments)
            orphaned_count = len(orphaned_deployments)
            unassigned_count = len(unassigned_trips)
            
            print(f"📊 Total Trips: {total_trips}")
            print(f"📊 Total Deployments: {total_deployments}")
            print(f"✅ Complete Assignments: {complete_assignments}")
            print(f"🔴 Orphaned Deployments: {orphaned_count}")
            print(f"🆓 Unassigned Trips: {unassigned_count}")
            print()
            
            # Vehicle and Driver utilization
            vehicle_count = len(vehicles)
            driver_count = len(drivers)
            assigned_vehicles = len([d for d in deployments if d['vehicle_id']])
            assigned_drivers = len([d for d in deployments if d['driver_id']])
            
            print(f"🚐 Total Vehicles: {vehicle_count}")
            print(f"🚐 Vehicles in Use: {assigned_vehicles}")
            print(f"🚐 Available Vehicles: {vehicle_count - assigned_vehicles}")
            print()
            print(f"👨‍✈️ Total Drivers: {driver_count}")
            print(f"👨‍✈️ Drivers in Use: {assigned_drivers}")
            print(f"👨‍✈️ Available Drivers: {driver_count - assigned_drivers}")
            
            # 8. SYSTEM HEALTH
            print("\n🏥 SYSTEM HEALTH")
            print("-" * 40)
            if complete_assignments == total_trips:
                print("✅ PERFECT: All trips fully assigned")
            elif orphaned_count == 0 and unassigned_count == 0:
                print("✅ GOOD: All trips have deployments")
            elif orphaned_count > 0:
                print(f"⚠️  WARNING: {orphaned_count} orphaned deployment(s) need completion")
            elif unassigned_count > 0:
                print(f"⚠️  WARNING: {unassigned_count} trip(s) need deployment")
            else:
                print("🔴 ISSUES: Mixed deployment states")
            
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate_status_report())
