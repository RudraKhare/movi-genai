"""
Test LLM Intent Parsing
Quick validation of OpenAI integration
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_llm_parse():
    """Test LLM parsing with various inputs"""
    from langgraph.tools.llm_client import parse_intent_with_llm
    
    test_cases = [
        "Cancel Path-3 - 07:30",
        "Remove vehicle from the morning trip",
        "Assign vehicle 5 and driver 3 to Jayanagar 08:00",
        "Cancel trip",
        "Remove vehicle",
    ]
    
    print("🧪 Testing LLM Intent Parsing\n")
    print(f"Model: {os.getenv('LLM_MODEL', 'gpt-4o-mini')}")
    print(f"LLM Enabled: {os.getenv('USE_LLM_PARSE', 'false')}\n")
    
    for i, text in enumerate(test_cases, 1):
        print(f"Test {i}: \"{text}\"")
        result = await parse_intent_with_llm(text)
        
        print(f"  Action: {result.get('action')}")
        print(f"  Target: {result.get('target_label')}")
        print(f"  Confidence: {result.get('confidence', 0):.2f}")
        print(f"  Clarify: {result.get('clarify', False)}")
        print(f"  Explanation: {result.get('explanation', 'N/A')}")
        print()

if __name__ == "__main__":
    try:
        asyncio.run(test_llm_parse())
        print("✅ All tests completed!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
