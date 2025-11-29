#!/usr/bin/env python3
"""
Fixed quick validation script for driver assignment core functionality
Tests the most critical fixes with correct API endpoints
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"  # Default dev key

def test_basic_driver_assignment():
    """Test basic driver assignment with structured command"""
    print("🧪 Testing structured driver assignment...")
    
    test_input = {
        "text": "STRUCTURED_CMD:assign_driver|trip_id:1|driver_id:2|driver_name:John|context:selection_ui",
        "user_id": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=test_input, 
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, 
                               timeout=15)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2)}")
            
            agent_output = result.get("agent_output", {})
            action = agent_output.get("action")
            status = agent_output.get("status")
            
            if action == "assign_driver":
                print("✅ Action correctly identified as assign_driver")
            else:
                print(f"❌ Expected assign_driver, got: {action}")
                
            if status != "error":
                print("✅ Assignment completed successfully")
            else:
                print(f"❌ Assignment failed: {agent_output.get('message', '')}")
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_context_assignment():
    """Test assignment with selectedTripId context"""
    print("\n🧪 Testing context-aware assignment...")
    
    test_input = {
        "text": "assign driver",
        "user_id": 1,
        "selectedTripId": 1,
        "session_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/agent/message", json=test_input, 
                               headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, 
                               timeout=15)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2)}")
            
            agent_output = result.get("agent_output", {})
            needs_clarification = agent_output.get("needs_clarification", False)
            options = agent_output.get("options", [])
            
            if not needs_clarification:
                print("✅ No clarification needed (good)")
            else:
                print("❌ Unnecessarily asking for clarification")
                
            if len(options) > 0:
                print(f"✅ Found {len(options)} driver options")
            else:
                print("ℹ️ No driver options (may be normal if no drivers available)")
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_server_health():
    """Test server health and available endpoints"""
    print("\n🧪 Testing server health...")
    
    try:
        response = requests.get(f"{API_BASE}/health", 
                              headers={"x-api-key": API_KEY}, 
                              timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Server is healthy: {health}")
        else:
            print(f"❌ Health check failed: {response.text}")
            
        # Also test API docs availability
        docs_response = requests.get(f"{API_BASE}/docs", timeout=10)
        print(f"📚 API docs status: {docs_response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    print("🚀 Fixed Quick Driver Assignment Test")
    print(f"⏰ {datetime.now().isoformat()}")
    print(f"🌐 Testing against: {API_BASE}")
    print("="*60)
    
    # Run tests
    test_server_health()
    test_basic_driver_assignment()
    test_context_assignment()
    
    print("\n" + "="*60)
    print("🏁 Test completed")
    print("💡 If tests pass, the driver assignment fixes are working!")
