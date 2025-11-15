"""
Comprehensive API Endpoint Validator for MOVI Project
Tests all endpoints with authentication, response validation, timing
"""
import asyncio
import httpx
import time
from typing import Dict, List, Tuple
import json

BASE_URL = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"  # Default from middleware.py
HEADERS = {"x-api-key": API_KEY}

async def test_endpoint(
    client: httpx.AsyncClient, 
    method: str, 
    path: str, 
    expected_status: int = 200,
    data: dict = None,
    description: str = ""
) -> Tuple[bool, float, str, dict]:
    """Test a single endpoint and return results"""
    start = time.time()
    
    try:
        if method == "GET":
            response = await client.get(f"{BASE_URL}{path}", headers=HEADERS)
        elif method == "POST":
            response = await client.post(f"{BASE_URL}{path}", headers=HEADERS, json=data)
        else:
            return False, 0, f"Unsupported method: {method}", {}
        
        duration = time.time() - start
        
        if response.status_code != expected_status:
            return False, duration, f"Expected {expected_status}, got {response.status_code}", {}
        
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text[:200]}
        
        return True, duration, "OK", response_data
        
    except Exception as e:
        duration = time.time() - start
        return False, duration, str(e), {}

async def validate_all_endpoints():
    """Run comprehensive endpoint validation"""
    print("=" * 80)
    print("API ENDPOINT VALIDATION")
    print("=" * 80)
    
    results = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Test 1: Health check
        print("\n[1/9] Testing /api/health...")
        success, duration, message, data = await test_endpoint(
            client, "GET", "/api/health", 200, 
            description="Health check endpoint"
        )
        results.append({
            "endpoint": "GET /api/health",
            "success": success,
            "duration": duration,
            "message": message,
            "has_data": bool(data)
        })
        status = "✅" if success else "❌"
        print(f"  {status} Status: {message} ({duration:.3f}s)")
        
        # Test 2: Dashboard context
        print("\n[2/9] Testing /api/context/dashboard...")
        success, duration, message, data = await test_endpoint(
            client, "GET", "/api/context/dashboard", 200
        )
        results.append({
            "endpoint": "GET /api/context/dashboard",
            "success": success,
            "duration": duration,
            "message": message,
            "has_trips": "trips" in data if data else False,
            "has_deployments": "deployment_summary" in data if data else False
        })
        status = "✅" if success else "❌"
        print(f"  {status} Status: {message} ({duration:.3f}s)")
        if success and data:
            print(f"     Trips: {len(data.get('trips', []))}")
            print(f"     Deployment summary: {'✓' if data.get('deployment_summary') else '✗'}")
        
        # Test 3: Manage context
        print("\n[3/9] Testing /api/context/manage...")
        success, duration, message, data = await test_endpoint(
            client, "GET", "/api/context/manage", 200
        )
        results.append({
            "endpoint": "GET /api/context/manage",
            "success": success,
            "duration": duration,
            "message": message,
            "has_stops": "stops" in data if data else False,
            "has_paths": "paths" in data if data else False,
            "has_routes": "routes" in data if data else False
        })
        status = "✅" if success else "❌"
        print(f"  {status} Status: {message} ({duration:.3f}s)")
        if success and data:
            print(f"     Stops: {len(data.get('stops', []))}")
            print(f"     Paths: {len(data.get('paths', []))}")
            print(f"     Routes: {len(data.get('routes', []))}")
        
        # Test 4: List routes
        print("\n[4/9] Testing /api/routes/...")
        success, duration, message, data = await test_endpoint(
            client, "GET", "/api/routes/", 200
        )
        results.append({
            "endpoint": "GET /api/routes/",
            "success": success,
            "duration": duration,
            "message": message
        })
        status = "✅" if success else "❌"
        print(f"  {status} Status: {message} ({duration:.3f}s)")
        
        # Test 5: Create stop
        print("\n[5/9] Testing POST /api/routes/stops/create...")
        test_stop = {"name": f"QA Test Stop {int(time.time())}"}
        success, duration, message, data = await test_endpoint(
            client, "POST", "/api/routes/stops/create", 200, data=test_stop
        )
        created_stop_id = data.get("stop", {}).get("stop_id") if success else None
        results.append({
            "endpoint": "POST /api/routes/stops/create",
            "success": success,
            "duration": duration,
            "message": message,
            "created_id": created_stop_id
        })
        status = "✅" if success else "❌"
        print(f"  {status} Status: {message} ({duration:.3f}s)")
        if created_stop_id:
            print(f"     Created stop_id: {created_stop_id}")
        
        # Test 6: Create path (requires existing stops)
        print("\n[6/9] Testing POST /api/routes/paths/create...")
        # Get first two stops
        manage_data = await client.get(f"{BASE_URL}/api/context/manage", headers=HEADERS)
        stops = manage_data.json().get("stops", [])
        
        if len(stops) >= 2:
            test_path = {
                "path_name": f"QA Test Path {int(time.time())}",
                "stop_ids": [stops[0]["stop_id"], stops[1]["stop_id"]]
            }
            success, duration, message, data = await test_endpoint(
                client, "POST", "/api/routes/paths/create", 200, data=test_path
            )
            created_path_id = data.get("path", {}).get("path_id") if success else None
            results.append({
                "endpoint": "POST /api/routes/paths/create",
                "success": success,
                "duration": duration,
                "message": message,
                "created_id": created_path_id
            })
            status = "✅" if success else "❌"
            print(f"  {status} Status: {message} ({duration:.3f}s)")
            if created_path_id:
                print(f"     Created path_id: {created_path_id}")
        else:
            print("  ⚠️  Skipped (insufficient stops)")
            results.append({
                "endpoint": "POST /api/routes/paths/create",
                "success": False,
                "duration": 0,
                "message": "Skipped - insufficient test data"
            })
        
        # Test 7: Create route
        print("\n[7/9] Testing POST /api/routes/create...")
        # Get first path
        if len(stops) >= 2:
            manage_data = await client.get(f"{BASE_URL}/api/context/manage", headers=HEADERS)
            paths = manage_data.json().get("paths", [])
            
            if paths:
                test_route = {
                    "route_name": f"QA Test Route {int(time.time())}",
                    "shift_time": "14:30",
                    "path_id": paths[0]["path_id"],
                    "direction": "UP"
                }
                success, duration, message, data = await test_endpoint(
                    client, "POST", "/api/routes/create", 200, data=test_route
                )
                created_route_id = data.get("route", {}).get("route_id") if success else None
                results.append({
                    "endpoint": "POST /api/routes/create",
                    "success": success,
                    "duration": duration,
                    "message": message,
                    "created_id": created_route_id,
                    "normalized_direction": data.get("route", {}).get("direction") if success else None
                })
                status = "✅" if success else "❌"
                print(f"  {status} Status: {message} ({duration:.3f}s)")
                if created_route_id:
                    print(f"     Created route_id: {created_route_id}")
                    print(f"     Direction normalized: UP → {data.get('route', {}).get('direction')}")
            else:
                print("  ⚠️  Skipped (no paths available)")
                results.append({
                    "endpoint": "POST /api/routes/create",
                    "success": False,
                    "duration": 0,
                    "message": "Skipped - no test paths"
                })
        else:
            print("  ⚠️  Skipped (insufficient stops)")
            results.append({
                "endpoint": "POST /api/routes/create",
                "success": False,
                "duration": 0,
                "message": "Skipped - insufficient test data"
            })
        
        # Test 8: List trips
        print("\n[8/9] Testing GET /api/trips/list...")
        success, duration, message, data = await test_endpoint(
            client, "GET", "/api/trips/list", 200
        )
        results.append({
            "endpoint": "GET /api/trips/list",
            "success": success,
            "duration": duration,
            "message": message
        })
        status = "✅" if success else "❌"
        print(f"  {status} Status: {message} ({duration:.3f}s)")
        
        # Test 9: Authentication check (no API key)
        print("\n[9/9] Testing authentication (no API key)...")
        start = time.time()
        try:
            response = await client.get(f"{BASE_URL}/api/context/manage")  # No headers
            duration = time.time() - start
            # Should get 401 or 403 for unauthorized
            success = response.status_code in [401, 403]
            message = "Correctly rejected" if success else f"Got {response.status_code} (expected 401/403)"
        except Exception as e:
            duration = time.time() - start
            success = False
            message = str(e)
        
        results.append({
            "endpoint": "Auth validation (no key)",
            "success": success,
            "duration": duration,
            "message": message
        })
        status = "✅" if success else "❌"
        print(f"  {status} Status: {message} ({duration:.3f}s)")
    
    # Summary
    print("\n" + "=" * 80)
    print("API VALIDATION SUMMARY")
    print("=" * 80)
    
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    avg_duration = sum(r["duration"] for r in results) / total if total > 0 else 0
    
    print(f"\n✅ Tests Passed: {passed}/{total} ({100*passed/total:.1f}%)")
    print(f"⏱️  Average Response Time: {avg_duration:.3f}s")
    print(f"🎯 Performance: {'✅ Good' if avg_duration < 1.0 else '⚠️ Slow'}")
    
    # Failed tests
    failed = [r for r in results if not r["success"]]
    if failed:
        print(f"\n❌ Failed Tests ({len(failed)}):")
        for r in failed:
            print(f"   - {r['endpoint']}: {r['message']}")
    else:
        print(f"\n✅ All API endpoints functioning correctly!")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(validate_all_endpoints())
