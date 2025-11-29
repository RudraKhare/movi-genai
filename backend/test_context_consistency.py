#!/usr/bin/env python3
"""
Test both vehicle and driver assignment with context
"""

import requests
import uuid

def test_context_consistency():
    """Test that both vehicle and driver assignment work with context"""
    print("🔍 TESTING CONTEXT CONSISTENCY")
    print("=" * 60)
    
    # Test 1: Vehicle assignment with context
    print("\n📋 TEST 1: Vehicle Assignment with Context")
    payload1 = {
        'text': 'assign vehicle to this trip',
        'user_id': 1,
        'selectedTripId': 8,  # Providing context
        'session_id': str(uuid.uuid4())
    }
    
    try:
        response1 = requests.post('http://localhost:8000/api/agent/message',
                                json=payload1,
                                headers={'x-api-key': 'dev-key-change-in-production'},
                                timeout=15)
        
        if response1.status_code == 200:
            result1 = response1.json()
            agent_output1 = result1['agent_output']
            print(f"   Status: {agent_output1.get('status')}")
            print(f"   Success: {agent_output1.get('success', False)}")
            
            if agent_output1.get('status') == 'options_provided':
                print("   ✅ VEHICLE CONTEXT: Working")
            else:
                print("   ❌ VEHICLE CONTEXT: Failed")
        else:
            print(f"   ❌ HTTP Error: {response1.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Driver assignment with context  
    print("\n📋 TEST 2: Driver Assignment with Context")
    payload2 = {
        'text': 'assign driver to this trip',
        'user_id': 1,
        'selectedTripId': 8,  # Same context
        'session_id': str(uuid.uuid4())
    }
    
    try:
        response2 = requests.post('http://localhost:8000/api/agent/message',
                                json=payload2,
                                headers={'x-api-key': 'dev-key-change-in-production'},
                                timeout=15)
        
        if response2.status_code == 200:
            result2 = response2.json()
            agent_output2 = result2['agent_output']
            print(f"   Status: {agent_output2.get('status')}")
            print(f"   Success: {agent_output2.get('success', False)}")
            
            if agent_output2.get('status') == 'options_provided':
                print("   ✅ DRIVER CONTEXT: Working")
            else:
                print("   ❌ DRIVER CONTEXT: Failed")
                print(f"   Message: {agent_output2.get('message', '')}")
        else:
            print(f"   ❌ HTTP Error: {response2.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n💡 RECOMMENDATION:")
    print("   If vehicle context works but driver context fails,")
    print("   check frontend state management and ensure context")
    print("   is maintained consistently across different actions.")

if __name__ == "__main__":
    test_context_consistency()
