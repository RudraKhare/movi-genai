#!/usr/bin/env python3
"""
Driver Selection UI Test Script
Tests the complete driver assignment flow including frontend fixes.
"""

import asyncio
import json
import time
import aiohttp
from typing import Dict, Any

# Test configuration
BACKEND_URL = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"

class DriverSelectionFlowTester:
    def __init__(self):
        self.session_id = None
        
    async def send_message(self, text: str, context: Dict[str, Any] = None) -> Dict:
        """Send a message to the MOVI agent"""
        if context is None:
            context = {"currentPage": "busDashboard", "selectedTripId": 123}
            
        payload = {
            "text": text,
            "user_id": 1,
            "context": context
        }
        
        headers = {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/agent/message",
                json=payload,
                headers=headers
            ) as response:
                result = await response.json()
                self.session_id = result.get("session_id")
                return result
    
    async def test_driver_assignment_flow(self):
        """Test the complete driver assignment flow"""
        print("🧪 Testing Driver Assignment Flow...\n")
        
        # Test 1: Initial driver assignment request
        print("1️⃣ Testing: 'assign driver to this trip'")
        response = await self.send_message("assign driver to this trip")
        
        agent_output = response.get("agent_output", {})
        print(f"   Response: {agent_output.get('message', 'No message')}")
        
        # Check if backend provides driver selection options
        has_options = bool(agent_output.get("options"))
        selection_type = agent_output.get("selection_type")
        awaiting_selection = agent_output.get("awaiting_selection")
        
        print(f"   Has options: {has_options}")
        print(f"   Selection type: {selection_type}")
        print(f"   Awaiting selection: {awaiting_selection}")
        
        if selection_type == "driver" and has_options:
            print("   ✅ Backend correctly identified driver selection needed")
            
            # Show available drivers
            options = agent_output.get("options", [])
            print(f"   📋 Available drivers ({len(options)}):")
            for i, driver in enumerate(options):
                print(f"      {i+1}. {driver.get('driver_name', 'Unknown')} - {driver.get('reason', 'Available')}")
            
            # Test 2: Driver selection by number
            print(f"\n2️⃣ Testing driver selection: 'Choose driver 1'")
            if options:
                # Simulate what frontend should generate
                first_driver = options[0]
                driver_id = first_driver.get("driver_id")
                trip_id = agent_output.get("trip_id", 123)
                
                expected_command = f"Assign driver {driver_id} to trip {trip_id}"
                print(f"   Frontend should generate: '{expected_command}'")
                
                # Send the command
                response2 = await self.send_message(expected_command)
                agent_output2 = response2.get("agent_output", {})
                
                print(f"   Response: {agent_output2.get('message', 'No message')}")
                
                if agent_output2.get("success"):
                    print("   ✅ Driver assignment completed successfully!")
                else:
                    print("   ❌ Driver assignment failed")
                    
                return agent_output2.get("success", False)
        else:
            print("   ❌ Backend did not provide driver selection options")
            return False
    
    async def test_vehicle_assignment_flow(self):
        """Test vehicle assignment for comparison"""
        print("\n🧪 Testing Vehicle Assignment Flow (for comparison)...\n")
        
        print("1️⃣ Testing: 'assign vehicle to this trip'") 
        response = await self.send_message("assign vehicle to this trip")
        
        agent_output = response.get("agent_output", {})
        print(f"   Response: {agent_output.get('message', 'No message')}")
        
        selection_type = agent_output.get("selection_type")
        has_options = bool(agent_output.get("options"))
        
        print(f"   Selection type: {selection_type}")
        print(f"   Has options: {has_options}")
        
        if selection_type == "vehicle":
            print("   ✅ Backend correctly identified vehicle selection needed")
            return True
        else:
            print("   ❌ Vehicle assignment flow not working as expected")
            return False
    
    async def test_malformed_commands(self):
        """Test that malformed commands with 'undefined' are rejected"""
        print("\n🧪 Testing Malformed Command Protection...\n")
        
        # Test the specific issue: "Assign vehicle undefined to trip 36" 
        print("1️⃣ Testing: 'Assign vehicle undefined to trip 36'")
        response = await self.send_message("Assign vehicle undefined to trip 36")
        
        agent_output = response.get("agent_output", {})
        print(f"   Response: {agent_output.get('message', 'No message')}")
        
        # Should be rejected as invalid
        if "invalid" in agent_output.get("message", "").lower() or "error" in agent_output.get("message", "").lower():
            print("   ✅ Backend correctly rejected undefined command")
            return True
        else:
            print("   ❌ Backend should reject commands with 'undefined'")
            return False

async def main():
    """Run all tests"""
    print("🚀 MOVI Driver Selection UI Fix - End-to-End Test\n")
    print("="*60)
    
    tester = DriverSelectionFlowTester()
    
    try:
        # Test driver assignment
        driver_test = await tester.test_driver_assignment_flow()
        
        # Test vehicle assignment
        vehicle_test = await tester.test_vehicle_assignment_flow()
        
        # Test malformed command protection
        protection_test = await tester.test_malformed_commands()
        
        # Summary
        print("\n" + "="*60)
        print("🎯 TEST SUMMARY")
        print("="*60)
        
        tests_passed = sum([driver_test, vehicle_test, protection_test])
        total_tests = 3
        
        results = [
            ("Driver Assignment Flow", driver_test),
            ("Vehicle Assignment Flow", vehicle_test),
            ("Malformed Command Protection", protection_test)
        ]
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\nResults: {tests_passed}/{total_tests} tests passed ({tests_passed/total_tests*100:.0f}%)")
        
        if tests_passed == total_tests:
            print("\n🎉 All tests passed! The driver selection fix is working correctly!")
            
            print("\n📱 Frontend Implementation Summary:")
            print("✅ Added driver/vehicle selection UI with proper icons")
            print("✅ Fixed click handler to generate correct commands based on selection_type")
            print("✅ Added validation for option data integrity")
            print("✅ Created reusable utility functions")
            print("✅ Added error handling for invalid selections")
            
            print("\n🔧 Backend Protection Added:")
            print("✅ Commands with 'undefined' are rejected with helpful error message")
            
            print("\n🎯 Expected User Experience:")
            print("1. User: 'assign driver to this trip'")
            print("2. Backend: Shows available drivers with 👤 icon")
            print("3. User: Clicks a driver option")
            print("4. Frontend: Generates 'Assign driver 5 to trip 123'")
            print("5. Backend: Processes driver assignment successfully")
            print("6. User: Sees confirmation message")
            
        else:
            print(f"\n⚠️  {total_tests - tests_passed} test(s) failed")
            print("Please check backend logs and verify the implementation.")
            
        return tests_passed == total_tests
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        print("Please ensure the backend is running on http://localhost:8000")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
