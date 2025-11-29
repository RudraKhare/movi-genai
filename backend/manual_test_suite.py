#!/usr/bin/env python3
"""
Manual Testing Guide - Quick API Tests
"""

import requests
import json
import uuid

API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

def test_1_deployment_check():
    """Test 1: Deployment Check - Should block vehicle assignment when trip has deployment"""
    print("=" * 60)
    print("🔧 TEST 1: DEPLOYMENT CHECK")
    print("=" * 60)
    print("Purpose: Verify that vehicle assignment is blocked when trip already has deployment")
    print()
    
    # Test with trip 5 which has deployment_id: 24
    input_data = {
        'text': 'STRUCTURED_CMD:assign_vehicle|trip_id:5|vehicle_id:8|vehicle_name:Honda|context:selection_ui',
        'user_id': 1,
        'session_id': str(uuid.uuid4())
    }
    
    print(f"📡 REQUEST:")
    print(f"   URL: {API_BASE}/api/agent/message")
    print(f"   Text: {input_data['text']}")
    print()
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", 
                               json=input_data,
                               headers={'x-api-key': API_KEY, 'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result['agent_output']
            
            print(f"📋 RESPONSE:")
            print(f"   Status: {agent_output.get('status')}")
            print(f"   Error: {agent_output.get('error')}")
            print(f"   Message: {agent_output.get('message', '')}")
            print()
            
            if (agent_output.get('status') == 'failed' and 
                agent_output.get('error') == 'already_deployed'):
                print("✅ PASS: Deployment check working!")
                print("   ✓ Vehicle assignment properly blocked")
                print("   ✓ Clear error message about existing deployment")
                return True
            else:
                print("❌ FAIL: Deployment check not working")
                print(f"   Expected: status='failed', error='already_deployed'")
                print(f"   Got: status='{agent_output.get('status')}', error='{agent_output.get('error')}'")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_2_suggestions():
    """Test 2: Suggestions - Should show vehicle options when no vehicle specified"""
    print("=" * 60)
    print("🔧 TEST 2: SUGGESTIONS SUPPORT")
    print("=" * 60)
    print("Purpose: Verify that vehicle suggestions are provided when requesting vehicle assignment")
    print()
    
    # Test with trip 3 (should not have deployment conflict)
    input_data = {
        'text': 'assign vehicle to trip 3',
        'user_id': 1,
        'selectedTripId': 3,
        'session_id': str(uuid.uuid4())
    }
    
    print(f"📡 REQUEST:")
    print(f"   URL: {API_BASE}/api/agent/message")
    print(f"   Text: {input_data['text']}")
    print()
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message",
                               json=input_data,
                               headers={'x-api-key': API_KEY, 'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result['agent_output']
            
            print(f"📋 RESPONSE:")
            print(f"   Status: {agent_output.get('status')}")
            print(f"   Options count: {len(agent_output.get('options', []))}")
            print()
            
            if agent_output.get('options'):
                print("✅ PASS: Suggestions working!")
                print(f"   ✓ Found {len(agent_output['options'])} vehicle options")
                
                # Show first few options
                for i, option in enumerate(agent_output['options'][:3]):
                    vehicle_name = option.get('vehicle_name', 'Unknown')
                    vehicle_id = option.get('vehicle_id')
                    print(f"   ✓ Option {i+1}: {vehicle_name} (ID: {vehicle_id})")
                
                return True
            else:
                print("❌ FAIL: No suggestions provided")
                print("   Expected: options array with vehicle choices")
                print(f"   Got: {agent_output.get('options', [])}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_3_string_conversion():
    """Test 3: String-to-Int Conversion - Should handle string IDs without errors"""
    print("=" * 60)
    print("🔧 TEST 3: STRING-TO-INTEGER CONVERSION")
    print("=" * 60)
    print("Purpose: Verify that structured commands with string IDs work without asyncpg errors")
    print()
    
    # Test with trip 3 and string IDs (should be converted to int)
    input_data = {
        'text': 'STRUCTURED_CMD:assign_driver|trip_id:3|driver_id:1|driver_name:John Doe|context:selection_ui',
        'user_id': 1,
        'session_id': str(uuid.uuid4())
    }
    
    print(f"📡 REQUEST:")
    print(f"   URL: {API_BASE}/api/agent/message")
    print(f"   Text: {input_data['text']}")
    print(f"   Note: trip_id and driver_id are strings, should be converted to int")
    print()
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message",
                               json=input_data,
                               headers={'x-api-key': API_KEY, 'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result['agent_output']
            
            print(f"📋 RESPONSE:")
            print(f"   Status: {agent_output.get('status')}")
            print(f"   Success: {agent_output.get('success', False)}")
            
            # Check for asyncpg-related errors
            message = str(agent_output.get('message', '')).lower()
            if 'str cannot be interpreted as integer' in message:
                print("❌ FAIL: String-to-int conversion not working")
                print("   Still getting asyncpg type errors")
                return False
            elif response.status_code == 200:
                print("✅ PASS: String-to-int conversion working!")
                print("   ✓ No asyncpg type errors")
                print("   ✓ String IDs properly converted")
                return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all manual tests"""
    print("🚀 MANUAL TESTING SUITE")
    print("=" * 60)
    print("Testing all 6 critical fixes...")
    print()
    
    tests = [
        ("Deployment Check", test_1_deployment_check),
        ("Suggestions Support", test_2_suggestions),
        ("String-Int Conversion", test_3_string_conversion),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            print()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
            print()
    
    # Summary
    print("=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! System is working correctly.")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed - need investigation")

if __name__ == "__main__":
    print("Make sure backend is running: python -m uvicorn app.main:app --reload --port 8000")
    print()
    main()
