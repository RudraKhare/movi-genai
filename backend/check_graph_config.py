"""Check what USE_LLM_PARSE is set to"""
import sys
sys.path.insert(0, 'C:/Users/rudra/Desktop/movi/backend')

import os
print(f"USE_LLM_PARSE from os.getenv: {os.getenv('USE_LLM_PARSE')}")

from langgraph.graph_def import USE_LLM_PARSE, graph
print(f"USE_LLM_PARSE in graph_def: {USE_LLM_PARSE}")
print(f"Graph has {len(graph.nodes)} nodes:")
for node_name in graph.nodes.keys():
    print(f"  - {node_name}")

# Check which parse_intent node is registered
print(f"\nparse_intent node function: {graph.nodes['parse_intent'].__name__}")
