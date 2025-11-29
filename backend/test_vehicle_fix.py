#!/usr/bin/env python3
"""
Test the fixed vehicle availability system
"""

import requests
import uuid

def test_vehicle_availability_fix():
    """Test that vehicle availability properly prevents conflicts"""
    print("🔍 TESTING FIXED VEHICLE AVAILABILITY")
    print("=" * 60)
    
    # Test 1: Try to assign vehicle to trip 38 (should now filter out conflicted vehicles)
    print("\n📋 TEST: Vehicle Options for Trip 38")
    print("Trip 38: 2025-11-15 at 11:00:00")
    print("Vehicle 1: Already assigned to Trip 36 (2025-11-15 at 11:15:00)")
    print("Expected: Vehicle 1 should NOT appear in options")
    
    payload = {
        'text': 'allocate vehicle to trip 38',
        'user_id': 1,
        'session_id': str(uuid.uuid4())
    }
    
    try:
        response = requests.post('http://localhost:8000/api/agent/message',
                               json=payload,
                               headers={'x-api-key': 'dev-key-change-in-production'},
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            agent_output = result['agent_output']
            
            print(f"\n   Status: {agent_output.get('status')}")
            
            if agent_output.get('suggestions'):
                print(f"   Available vehicles: {len(agent_output['suggestions'])}")
                
                # Check if Vehicle 1 (KA01AB1234) is in the suggestions
                vehicle_1_found = False
                for suggestion in agent_output['suggestions']:
                    if hasattr(suggestion, 'get'):
                        label = suggestion.get('label', '')
                        if 'KA01AB1234' in label:
                            vehicle_1_found = True
                            break
                    elif isinstance(suggestion, str) and 'KA01AB1234' in suggestion:
                        vehicle_1_found = True
                        break
                
                if vehicle_1_found:
                    print("   ❌ FAILED: Vehicle 1 (KA01AB1234) still appears in options")
                    print("   🔧 FIX NEEDED: Time-aware filtering not working properly")
                else:
                    print("   ✅ SUCCESS: Vehicle 1 (KA01AB1234) correctly filtered out")
                    print("   🎯 Time conflict detection working!")
                    
                # Show first few vehicles for reference
                print("\n   📋 Available vehicles:")
                for i, suggestion in enumerate(agent_output['suggestions'][:3]):
                    if hasattr(suggestion, 'get'):
                        print(f"      {i+1}. {suggestion.get('label', suggestion)}")
                    else:
                        print(f"      {i+1}. {suggestion}")
            else:
                print("   ⚠️  No vehicle suggestions provided")
                print(f"   Message: {agent_output.get('message', '')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n💡 EXPECTED BEHAVIOR:")
    print(f"   • Vehicle 1 should be filtered out (conflicts with Trip 36)")  
    print(f"   • Other vehicles should be available")
    print(f"   • Assignment should succeed with non-conflicting vehicles")

if __name__ == "__main__":
    test_vehicle_availability_fix()
