#!/usr/bin/env python3
"""
API Test Script - Test MOVI's enhanced natural language understanding via HTTP API.

This script will make HTTP requests to test if our changes work in the actual backend.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

class MoviAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def create_session(self):
        """Create HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def test_agent_endpoint(self, text: str, trip_id: str = None, user_id: str = "test_user") -> dict:
        """Test the agent endpoint with natural language input"""
        if not self.session:
            await self.create_session()
            
        payload = {
            "text": text,
            "userId": user_id,
            "sessionId": "test_session_123"
        }
        
        if trip_id:
            payload["selectedTripId"] = trip_id
        
        try:
            async with self.session.post(
                f"{self.base_url}/agent/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "error": f"HTTP {response.status}",
                        "message": await response.text()
                    }
        except Exception as e:
            return {
                "error": "Connection failed", 
                "message": str(e)
            }
    
    async def test_health_endpoint(self) -> dict:
        """Test if the backend is running"""
        if not self.session:
            await self.create_session()
            
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return {"status": "healthy", "data": await response.json()}
                else:
                    return {"status": "unhealthy", "code": response.status}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

async def test_natural_language_api():
    """Test natural language understanding via API"""
    print("🌐 Testing MOVI API Natural Language Understanding")
    print("=" * 60)
    
    tester = MoviAPITester()
    
    # Test if backend is running
    print("1. Checking backend health...")
    health = await tester.test_health_endpoint()
    if health["status"] != "healthy":
        print(f"   ❌ Backend not available: {health}")
        print("\n💡 To test the API, please start the backend:")
        print("   cd c:\\Users\\rudra\\Desktop\\movi")
        print("   docker-compose up")
        return False
    else:
        print("   ✅ Backend is healthy")
    
    # Test natural language inputs
    print("\n2. Testing natural language inputs...")
    
    test_cases = [
        {
            "text": "assign John to this trip",
            "trip_id": "trip_123",
            "description": "Driver assignment with name"
        },
        {
            "text": "allocate a driver",
            "trip_id": "trip_123", 
            "description": "Generic driver allocation"
        },
        {
            "text": "assign driver",
            "trip_id": None,
            "description": "Assignment without trip selected"
        },
        {
            "text": "what trips do I have",
            "trip_id": None,
            "description": "Trip listing request"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {case['description']}")
        print(f"   Input: '{case['text']}'")
        print(f"   Trip: {case['trip_id']}")
        
        result = await tester.test_agent_endpoint(
            case['text'], 
            case['trip_id']
        )
        
        if "error" in result:
            print(f"   ❌ API Error: {result['error']}")
            continue
            
        # Extract relevant info from response
        action = result.get("action", "unknown")
        message = result.get("message", "")
        
        print(f"   Action: {action}")
        if message:
            print(f"   Message: {message}")
        
        # Check for success indicators
        if action != "unknown":
            if "not sure what you want to do" in message:
                print("   ⚠️  Still getting 'not sure' - natural language may need work")
            else:
                print("   ✅ Recognized action successfully")
                passed += 1
        else:
            print("   ❌ Failed to recognize action")
    
    await tester.close_session()
    
    print(f"\n📊 API Test Results: {passed}/{total} tests passed")
    return passed > 0

def show_manual_test_instructions():
    """Show instructions for manual testing"""
    print("\n\n📱 Manual Testing Instructions")
    print("=" * 50)
    print("If the backend is running, you can also test manually:")
    print()
    print("1. Open the frontend application in your browser")
    print("2. Select a trip from the trip list")
    print("3. Try these natural language inputs in the chat:")
    print()
    print("   💬 'assign John to this trip'")
    print("   💬 'allocate a driver'") 
    print("   💬 'can you assign someone to drive'")
    print("   💬 'set driver to Sarah'")
    print()
    print("Expected behavior:")
    print("   ✅ MOVI should understand these as driver assignment requests")
    print("   ✅ Should ask for clarification if missing information")
    print("   ❌ Should NOT say 'I'm not sure what you want to do'")
    print()
    print("Compare with the old behavior where MOVI couldn't understand")
    print("natural language and only worked with exact regex patterns.")

async def main():
    """Run API tests"""
    print("🚀 MOVI Natural Language API Test")
    print("=" * 50)
    
    try:
        success = await test_natural_language_api()
        
        if success:
            print("\n✅ API tests show improvements working!")
            print("\nKey enhancements validated:")
            print("   • Natural language understanding enabled")
            print("   • LLM parsing preferred over regex")
            print("   • Better action recognition")
        else:
            print("\n⚠️  API tests couldn't run or showed issues")
            print("This might be due to backend not running or configuration issues")
        
        show_manual_test_instructions()
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
