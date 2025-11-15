# Quick Test Script for LLM Integration

import asyncio
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

async def test_graph_mode():
    """Check which parse mode is active"""
    from langgraph.graph_def import USE_LLM_PARSE, graph
    
    print("\n" + "="*60)
    print("🔍 LLM INTEGRATION STATUS CHECK")
    print("="*60)
    
    print(f"\n1. Feature Flag: USE_LLM_PARSE = {USE_LLM_PARSE}")
    
    print(f"\n2. Registered Nodes:")
    for node_name in graph.nodes.keys():
        print(f"   - {node_name}")
    
    print(f"\n3. Parse Intent Node Type:")
    parse_node = graph.nodes.get("parse_intent")
    if parse_node:
        print(f"   - Function: {parse_node.__name__}")
        print(f"   - Module: {parse_node.__module__}")
    
    if USE_LLM_PARSE:
        print("\n✅ LLM MODE ACTIVE")
        print("   - Natural language commands will use OpenAI")
        print("   - OCR flow will still bypass LLM")
    else:
        print("\n📝 CLASSIC MODE ACTIVE")
        print("   - Using regex pattern matching")
        print("   - LLM is disabled")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_graph_mode())
