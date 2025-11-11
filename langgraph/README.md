# LangGraph Agent Directory

This directory will contain the LangGraph-based AI agent orchestration for Movi.

## Structure (To be implemented Day 3+)

```
langgraph/
├── agent.py              # Main LangGraph agent definition
├── nodes/                # Agent nodes (steps in the workflow)
│   ├── parse_intent.py   # Parse user intent from text/voice/image
│   ├── check_consequences.py  # Check for consequences of actions
│   ├── get_confirmation.py    # Ask user for confirmation
│   └── execute_action.py      # Execute the requested action
├── tools/                # Tools/functions the agent can call
│   ├── stops_tools.py    # CRUD operations for stops
│   ├── paths_tools.py    # CRUD operations for paths
│   ├── routes_tools.py   # CRUD operations for routes
│   ├── trips_tools.py    # CRUD operations for trips
│   ├── vehicles_tools.py # CRUD operations for vehicles
│   └── vision_tools.py   # Image processing tools
├── state.py              # Agent state definition
└── graph.py              # Graph structure and conditional edges
```

## Agent Architecture (Planned)

### State Schema
```python
class AgentState(TypedDict):
    user_input: str
    current_page: str  # 'busDashboard' or 'manageRoute'
    intent: str
    entities: dict
    action: str
    consequences: list
    confirmation_required: bool
    user_confirmed: bool
    result: dict
    error: Optional[str]
```

### Main Nodes
1. **parse_intent**: Extract user intent and entities from input
2. **check_consequences**: Query DB for potential impacts of action
3. **get_confirmation**: Ask user to confirm if consequences exist
4. **execute_action**: Perform the database operation
5. **format_response**: Format the response for the user

### Conditional Edges
- After `check_consequences`: Route to `get_confirmation` if consequences exist, else to `execute_action`
- After `get_confirmation`: Route to `execute_action` if confirmed, else to `format_response` (cancel)

## Tools (>10 Required)

### Static Asset Tools (manageRoute page)
1. `list_stops` - List all stops
2. `create_stop` - Create a new stop
3. `list_paths` - List all paths
4. `get_path_stops` - Get stops for a specific path
5. `create_path` - Create a new path
6. `list_routes` - List all routes
7. `create_route` - Create a new route

### Dynamic Operation Tools (busDashboard page)
8. `list_trips` - List daily trips
9. `get_trip_status` - Get status of a specific trip
10. `assign_vehicle` - Assign vehicle and driver to trip
11. `remove_vehicle` - Remove vehicle from trip (requires consequence check)
12. `list_unassigned_vehicles` - List vehicles not assigned to any trip

### Multimodal Tools
13. `process_image` - Extract information from uploaded screenshot
14. `transcribe_audio` - Convert voice to text (Speech-to-Text)

## Integration Points

- **Database**: Will use SQLAlchemy models from `backend/app/models/`
- **API**: Will expose agent endpoints via FastAPI in `backend/app/routers/agent.py`
- **Frontend**: Will connect via WebSocket or HTTP API for real-time chat

## Next Steps (Day 3)

1. Install LangChain and LangGraph packages
2. Define `AgentState` class
3. Implement basic nodes (parse_intent, execute_action)
4. Create graph with conditional edges
5. Implement "tribal knowledge" consequence checking
6. Test with simple text commands

---

**Status**: Placeholder (Day 1 Bootstrap)  
**Next Implementation**: Day 3
