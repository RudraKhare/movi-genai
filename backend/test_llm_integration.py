"""
Test LLM Integration - Day 11
Comprehensive test suite for natural language processing with Gemini
"""
import httpx
import asyncio
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_KEY = "dev-key-change-in-production"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def print_test_header(test_name: str):
    """Print a formatted test header"""
    print("\n" + "="*80)
    print(f"🧪 TEST: {test_name}")
    print("="*80)

def print_result(response_data: Dict[Any, Any]):
    """Print formatted test results"""
    agent_output = response_data.get("agent_output", {})
    
    print(f"\n✅ Action: {agent_output.get('action')}")
    print(f"📍 Trip: {agent_output.get('trip_label')} (ID: {agent_output.get('trip_id')})")
    print(f"🎯 Confidence: {agent_output.get('confidence', 0):.2f}")
    print(f"💬 LLM Explanation: {agent_output.get('llm_explanation')}")
    print(f"📊 Status: {agent_output.get('status')}")
    
    if agent_output.get('needs_confirmation'):
        print(f"⚠️  Confirmation Required: YES")
        print(f"📝 Message: {agent_output.get('message')}")
        print(f"🔑 Session ID: {response_data.get('session_id')}")
    
    if agent_output.get('clarify_options'):
        print(f"❓ Clarification Needed - Options:")
        for i, option in enumerate(agent_output.get('clarify_options', []), 1):
            print(f"   {i}. {option}")
    
    if agent_output.get('execution_result'):
        exec_result = agent_output['execution_result']
        print(f"🚀 Execution Result: {exec_result.get('message')}")

async def test_1_cancel_specific_trip():
    """Test 1: Cancel a specific trip by name"""
    print_test_header("Cancel Specific Trip - 'Cancel Bulk - 00:01'")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/agent/message",
            headers=HEADERS,
            json={"text": "Cancel Bulk - 00:01", "user_id": 1}
        )
        
        data = response.json()
        print_result(data)
        
        # Return session_id for confirmation test
        return data.get("session_id")

async def test_2_confirm_cancellation(session_id: str):
    """Test 2: Confirm the pending cancellation"""
    if not session_id:
        print("\n⚠️  Skipping confirmation test - no session_id")
        return
    
    print_test_header("Confirm Cancellation")
    print(f"Session ID: {session_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/agent/confirm",
            headers=HEADERS,
            json={"session_id": session_id, "user_id": 1}
        )
        
        data = response.json()
        print_result(data)

async def test_3_remove_vehicle():
    """Test 3: Remove vehicle from trip using natural language"""
    print_test_header("Remove Vehicle - 'Remove vehicle from Path-3 morning trip'")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/agent/message",
            headers=HEADERS,
            json={"text": "Remove vehicle from Path-3 morning trip", "user_id": 1}
        )
        
        data = response.json()
        print_result(data)

async def test_4_assign_vehicle():
    """Test 4: Assign vehicle and driver using natural language"""
    print_test_header("Assign Vehicle - 'Assign bus 5 driver 3 to Jayanagar route'")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/agent/message",
            headers=HEADERS,
            json={"text": "Assign bus 5 driver 3 to Jayanagar route", "user_id": 1}
        )
        
        data = response.json()
        print_result(data)

async def test_5_ambiguous_clarification():
    """Test 5: Ambiguous input requiring clarification"""
    print_test_header("Ambiguous Input - 'Cancel the 7:30 run'")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/agent/message",
            headers=HEADERS,
            json={"text": "Cancel the 7:30 run", "user_id": 1}
        )
        
        data = response.json()
        print_result(data)

async def test_6_ocr_bypass():
    """Test 6: OCR bypass - should skip LLM when selectedTripId provided"""
    print_test_header("OCR Bypass - selectedTripId=1 provided")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/agent/message",
            headers=HEADERS,
            json={
                "text": "Cancel trip",
                "user_id": 1,
                "selectedTripId": 1,  # OCR provided trip ID
                "currentPage": "trips"
            }
        )
        
        data = response.json()
        agent_output = data.get("agent_output", {})
        
        print(f"\n✅ Action: {agent_output.get('action')}")
        print(f"📍 Trip ID: {agent_output.get('trip_id')}")
        print(f"🎯 LLM Used: {'NO - OCR BYPASS' if agent_output.get('trip_id') == 1 else 'YES'}")
        print(f"📊 Status: {agent_output.get('status')}")

async def test_7_generic_morning_trip():
    """Test 7: Generic reference requiring clarification"""
    print_test_header("Generic Reference - 'Cancel the morning bulk trip'")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/agent/message",
            headers=HEADERS,
            json={"text": "Cancel the morning bulk trip", "user_id": 1}
        )
        
        data = response.json()
        print_result(data)

async def main():
    """Run all tests sequentially"""
    print("\n🚀 Starting LLM Integration Test Suite - Day 11")
    print(f"📡 Target: {BASE_URL}")
    print(f"🤖 LLM Provider: Gemini 2.5 Flash")
    
    try:
        # Test 1: Cancel specific trip (should require confirmation)
        session_id = await test_1_cancel_specific_trip()
        await asyncio.sleep(1)
        
        # Test 2: Confirm the cancellation
        # await test_2_confirm_cancellation(session_id)
        # await asyncio.sleep(1)
        print("\n⚠️  Skipping Test 2 (Confirm Cancellation) to avoid actual DB changes")
        
        # Test 3: Remove vehicle
        await test_3_remove_vehicle()
        await asyncio.sleep(1)
        
        # Test 4: Assign vehicle
        await test_4_assign_vehicle()
        await asyncio.sleep(1)
        
        # Test 5: Ambiguous input
        await test_5_ambiguous_clarification()
        await asyncio.sleep(1)
        
        # Test 6: OCR bypass
        await test_6_ocr_bypass()
        await asyncio.sleep(1)
        
        # Test 7: Generic morning trip
        await test_7_generic_morning_trip()
        
        print("\n" + "="*80)
        print("✅ All tests completed!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
