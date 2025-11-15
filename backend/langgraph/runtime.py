"""
LangGraph Runtime Executor
Executes the graph flow with state management
"""
from typing import Dict
import logging
from .graph_def import graph

logger = logging.getLogger(__name__)


class GraphRuntime:
    """
    Runtime executor for the agent graph.
    Manages state transitions and node execution.
    """
    
    def __init__(self, graph_instance):
        self.graph = graph_instance
        self.max_iterations = 20  # Safety limit to prevent infinite loops
        
    async def run(self, input_state: Dict) -> Dict:
        """
        Execute the graph from start to finish.
        
        Args:
            input_state: Initial state (must contain 'text' at minimum)
            
        Returns:
            Final state after all nodes have executed
        """
        state = input_state.copy()
        current = "parse_intent"
        iteration = 0
        
        logger.info(f"Starting graph execution with input: {input_state.get('text', '')[:100]}")
        
        while current and iteration < self.max_iterations:
            iteration += 1
            
            # Get the node function
            node_func = self.graph.nodes.get(current)
            if not node_func:
                logger.error(f"Node '{current}' not found in graph")
                break
            
            logger.info(f"[Iteration {iteration}] Executing node: {current}")
            
            try:
                # Execute the node
                state = await node_func(state)
                
                # Check if we've reached a terminal state
                if current in ["report_result", "fallback"]:
                    logger.info(f"Reached terminal node: {current}")
                    break
                
                # Determine next node
                next_node = self.graph.get_next_node(current, state)
                
                if not next_node:
                    logger.warning(f"No next node found from '{current}', ending execution")
                    # If no next node but haven't reported, go to report_result
                    if "final_output" not in state:
                        state = await self.graph.nodes["report_result"](state)
                    break
                
                logger.info(f"Transitioning from '{current}' to '{next_node}'")
                current = next_node
                
            except Exception as e:
                logger.error(f"Error executing node '{current}': {e}", exc_info=True)
                state["error"] = "node_execution_error"
                state["message"] = f"Internal error: {str(e)}"
                # Go to fallback on error
                state = await self.graph.nodes["fallback"](state)
                break
        
        if iteration >= self.max_iterations:
            logger.error(f"Max iterations ({self.max_iterations}) reached, forcing termination")
            state["error"] = "max_iterations_exceeded"
            state["message"] = "Agent execution exceeded maximum iterations"
            state = await self.graph.nodes["fallback"](state)
        
        logger.info(
            f"Graph execution completed in {iteration} iterations. "
            f"Final status: {state.get('status', 'unknown')}"
        )
        
        return state


# Create runtime instance
runtime = GraphRuntime(graph)
