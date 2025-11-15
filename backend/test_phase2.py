"""
Phase 2 Test - Debug LLM parsing and trip resolution
"""
import asyncio
import sys
import json
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

from langgraph.runtime import runtime
from pprint import pprint

async def test_phase2():
    """Test basic LLM parse functionality"""
    print("="*70)
    print("PHASE 2 - BASIC LLM PARSE FUNCTIONALITY TEST")
    print("="*70)
    
    # Test input
    test_input = {
        "text": "cancel the Bulk - 00:01 trip",
        "currentPage": "busDashboard",
        "user_id": 1
    }
    
    print("\n📥 INPUT:")
    print(json.dumps(test_input, indent=2))
    
    print("\n🔄 Running agent graph...")
    print("-"*70)
    
    # Run the graph using runtime
    result = await runtime.run(test_input)
    
    print("\n📤 OUTPUT:")
    print("-"*70)
    pprint(result, width=70)
    
    # Check expectations
    print("\n✅ VALIDATION:")
    print("-"*70)
    
    checks = [
        ("LLM identified action", result.get("action") == "cancel_trip"),
        ("trip_id resolved", "trip_id" in result and result.get("trip_id") is not None),
        ("trip_label found", "trip_label" in result and result.get("trip_label") is not None),
        ("confidence score present", "confidence" in result),
        ("needs_confirmation set", "needs_confirmation" in result),
    ]
    
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
        
        if check_name == "LLM identified action" and check_result:
            print(f"    → Action: {result.get('action')}")
        if check_name == "trip_id resolved" and check_result:
            print(f"    → Trip ID: {result.get('trip_id')}")
            print(f"    → Trip Label: {result.get('trip_label')}")
        if check_name == "confidence score present" and check_result:
            print(f"    → Confidence: {result.get('confidence')}")
    
    # Show any errors
    if result.get("error"):
        print(f"\n❌ ERROR: {result.get('error')}")
        print(f"   Message: {result.get('message')}")
    
    # Show parsed params from LLM
    if result.get("parsed_params"):
        print(f"\n🧠 LLM PARSED PARAMS:")
        print(json.dumps(result.get("parsed_params"), indent=2))
    
    # Show LLM explanation
    if result.get("llm_explanation"):
        print(f"\n💭 LLM EXPLANATION: {result.get('llm_explanation')}")
    
    print("\n" + "="*70)
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test_phase2())
