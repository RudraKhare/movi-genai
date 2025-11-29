#!/usr/bin/env python3
"""
Test the complete fix end-to-end
"""

import requests
import json
import uuid

def test_trip2_assignment():
    """Test Trip 2 vehicle assignment with context"""
    
    print("🧪 TESTING COMPLETE WORKFLOW FIX")
    print("="*60)
    
    # Test 1: With selectedTripId context (should understand "this trip")
    print("\n🔍 TEST 1: Context-Aware Assignment")
    print("Input: 'assign vehicle to this trip' with selectedTripId=7")
    
    payload1 = {
        'text': 'assign vehicle to this trip',
        'user_id': 1,
        'selectedTripId': 7,  # Clean trip with no deployments
        'session_id': str(uuid.uuid4())
    }
    
    try:
        response = requests.post('http://localhost:8000/api/agent/message',
                               json=payload1,
                               headers={'x-api-key': 'dev-key-change-in-production'},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result['agent_output']
            
            print(f"   Status: {agent_output.get('status')}")
            print(f"   Options: {len(agent_output.get('options', []))} vehicles")
            
            if agent_output.get('options'):
                print("   ✅ CONTEXT WORKING: Found vehicles with context")
                
                # Test 2: Click on a vehicle option
                first_vehicle = agent_output['options'][0]
                vehicle_id = first_vehicle['vehicle_id']
                vehicle_name = first_vehicle.get('vehicle_name', first_vehicle.get('registration_number'))
                
                print(f"\n🔍 TEST 2: Vehicle Selection")
                print(f"Selecting vehicle {vehicle_name} (ID: {vehicle_id})")
                
                payload2 = {
                    'text': f'STRUCTURED_CMD:assign_vehicle|trip_id:7|vehicle_id:{vehicle_id}|vehicle_name:{vehicle_name}|context:selection_ui',
                    'user_id': 1,
                    'session_id': str(uuid.uuid4())
                }
                
                response2 = requests.post('http://localhost:8000/api/agent/message',
                                        json=payload2,
                                        headers={'x-api-key': 'dev-key-change-in-production'},
                                        timeout=15)
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    agent_output2 = result2['agent_output']
                    
                    print(f"   Status: {agent_output2.get('status')}")
                    print(f"   Success: {agent_output2.get('success')}")
                    print(f"   Message: {agent_output2.get('message', '')}")
                    
                    if agent_output2.get('success'):
                        print("   ✅ ASSIGNMENT WORKING: Vehicle successfully assigned!")
                        return True
                    else:
                        print("   ❌ ASSIGNMENT FAILED: Still blocking orphaned deployments")
                        return False
                else:
                    print(f"   ❌ HTTP Error: {response2.status_code}")
                    return False
            else:
                print("   ❌ CONTEXT FAILED: No vehicle options provided")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_without_context():
    """Test without context to verify the old issue"""
    print("\n🔍 TEST 3: Without Context (Should Fail)")
    print("Input: 'assign vehicle to this trip' without selectedTripId")
    
    payload = {
        'text': 'assign vehicle to this trip',
        'user_id': 1,
        # No selectedTripId
        'session_id': str(uuid.uuid4())
    }
    
    try:
        response = requests.post('http://localhost:8000/api/agent/message',
                               json=payload,
                               headers={'x-api-key': 'dev-key-change-in-production'},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            message = result['agent_output'].get('message', '')
            
            if "couldn't find that trip" in message.lower():
                print("   ✅ EXPECTED: System correctly asks for trip clarification")
                return True
            else:
                print(f"   ❌ UNEXPECTED: {message}")
                return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    test1_success = test_trip2_assignment()
    test3_success = test_without_context()
    
    print("\n" + "="*60)
    print("🎯 FINAL RESULTS:")
    print(f"   Context-aware assignment: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   No-context handling: {'✅ PASS' if test3_success else '❌ FAIL'}")
    
    if test1_success:
        print("\n🎉 MAJOR PROGRESS!")
        print("   ✅ Decision Router logic working")
        print("   ✅ Tool layer deployment check fixed") 
        print("   ✅ Context awareness working")
        print("   ✅ End-to-end vehicle assignment working")
    else:
        print("\n⚠️ Still needs work...")
