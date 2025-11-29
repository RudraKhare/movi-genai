#!/usr/bin/env python3
"""
Test script to validate MOVI's enhanced natural language understanding and assign_driver functionality.

This script tests:
1. Natural language parsing for various driver assignment phrases
2. End-to-end assign_driver workflow
3. Error handling and missing parameter detection
"""

import asyncio
import sys
import os
import uuid
from typing import Dict, Any

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from langgraph.nodes.parse_intent_llm import parse_intent_llm
from langgraph.nodes.resolve_target import resolve_target
from langgraph.nodes.execute_action import execute_action
from langgraph.tools import tool_find_driver_by_name, tool_assign_driver
from langgraph.llm_client import llm_client

class AgentTester:
    def __init__(self):
        self.test_session_id = str(uuid.uuid4())
        self.test_user_id = "test_user_123"
        
    async def test_natural_language_parsing(self):
        """Test various natural language inputs for driver assignment"""
        print("🧪 Testing Natural Language Understanding...")
        print("=" * 50)
        
        test_cases = [
            "assign a driver to this trip",
            "allocate a driver", 
            "can you assign someone to drive",
            "I need a driver for this",
            "please assign John to this trip",
            "set driver to Sarah",
            "allocate John Smith as driver",
            "assign driver John to trip",
            "please assign a driver",
            "get a driver for this trip"
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: '{text}'")
            
            # Create state for testing
            state = {
                "text": text,
                "sessionId": self.test_session_id,
                "userId": self.test_user_id,
                "selectedTripId": "trip_123",
                "selectedEntityId": None
            }
            
            try:
                # Parse with LLM
                result = await parse_intent_llm(state)
                
                action = result.get("action", "unknown")
                entity_name = result.get("entityName", "")
                confidence = result.get("confidence", 0)
                
                print(f"   Action: {action}")
                print(f"   Entity: {entity_name}")
                print(f"   Confidence: {confidence:.2f}")
                
                if action == "assign_driver":
                    print("   ✅ PASS - Correctly identified as assign_driver")
                elif action == "need_clarification":
                    print("   ⚠️  CLARIFICATION - Asking for more details")
                    print(f"   Message: {result.get('message', '')}")
                else:
                    print(f"   ❌ FAIL - Expected assign_driver, got {action}")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
        
        return True
    
    async def test_driver_lookup(self):
        """Test driver lookup functionality"""
        print("\n\n🔍 Testing Driver Lookup...")
        print("=" * 50)
        
        test_names = ["John", "Sarah", "Mike Johnson", "nonexistent_driver"]
        
        for name in test_names:
            print(f"\nLooking up driver: '{name}'")
            try:
                result = await tool_find_driver_by_name(name)
                if result.get("success"):
                    driver = result.get("driver")
                    print(f"   ✅ Found: {driver.get('name')} (ID: {driver.get('id')})")
                else:
                    print(f"   ❌ Not found: {result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
    
    async def test_complete_workflow(self):
        """Test end-to-end workflow: parse -> resolve -> execute"""
        print("\n\n🔄 Testing Complete Workflow...")
        print("=" * 50)
        
        # Test case: "assign John to this trip"
        print("\nWorkflow Test: 'assign John to this trip'")
        
        # Step 1: Parse intent
        state = {
            "text": "assign John to this trip",
            "sessionId": self.test_session_id,
            "userId": self.test_user_id,
            "selectedTripId": "trip_123",
            "selectedEntityId": None
        }
        
        print("\n1. Parsing intent...")
        try:
            state = await parse_intent_llm(state)
            print(f"   Action: {state.get('action')}")
            print(f"   Entity: {state.get('entityName')}")
            print(f"   Confidence: {state.get('confidence', 0):.2f}")
        except Exception as e:
            print(f"   ❌ Parse error: {str(e)}")
            return False
        
        # Step 2: Resolve target (if needed)
        if state.get("action") == "assign_driver" and state.get("entityName"):
            print("\n2. Resolving driver...")
            try:
                state = await resolve_target(state)
                print(f"   Resolved ID: {state.get('selectedEntityId')}")
                print(f"   Resolution success: {state.get('resolution_success', False)}")
            except Exception as e:
                print(f"   ❌ Resolution error: {str(e)}")
                return False
        
        # Step 3: Execute action (simulation only)
        if state.get("action") == "assign_driver" and state.get("selectedEntityId"):
            print("\n3. Would execute assignment...")
            print(f"   Trip: {state.get('selectedTripId')}")
            print(f"   Driver: {state.get('selectedEntityId')}")
            print("   ✅ Workflow complete!")
        else:
            print("\n3. ❌ Cannot execute - missing requirements")
            print(f"   Action: {state.get('action')}")
            print(f"   Trip ID: {state.get('selectedTripId')}")  
            print(f"   Driver ID: {state.get('selectedEntityId')}")
        
        return True
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n\n⚠️  Testing Error Handling...")
        print("=" * 50)
        
        # Test missing trip ID
        print("\n1. Testing without trip ID...")
        state = {
            "text": "assign John as driver",
            "sessionId": self.test_session_id,
            "userId": self.test_user_id,
            "selectedTripId": None,  # Missing trip
            "selectedEntityId": None
        }
        
        try:
            result = await parse_intent_llm(state)
            if result.get("action") == "need_clarification":
                print("   ✅ Correctly asks for clarification")
            else:
                print(f"   ❓ Got action: {result.get('action')}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Test empty input
        print("\n2. Testing empty input...")
        state = {
            "text": "",
            "sessionId": self.test_session_id,
            "userId": self.test_user_id,
            "selectedTripId": "trip_123"
        }
        
        try:
            result = await parse_intent_llm(state)
            action = result.get("action", "unknown")
            print(f"   Action: {action}")
            if action == "unknown":
                print("   ✅ Correctly handles empty input")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

async def main():
    """Run all tests"""
    print("🚀 MOVI Enhanced Agent Test Suite")
    print("=" * 60)
    print("Testing natural language understanding and assign_driver functionality")
    print("=" * 60)
    
    tester = AgentTester()
    
    try:
        # Run all test suites
        await tester.test_natural_language_parsing()
        await tester.test_driver_lookup()
        await tester.test_complete_workflow()
        await tester.test_error_handling()
        
        print("\n\n✅ Test Suite Complete!")
        print("Check the results above to verify MOVI's enhanced capabilities.")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
