# MOVI Agent - Quick Reference Card

## 🎯 16 Actions at a Glance

### 📊 View Data (6 actions)
| Command Example | Action | Output |
|----------------|--------|--------|
| "show unassigned vehicles" | get_unassigned_vehicles | Table |
| "check trip 501" | get_trip_status | Object |
| "get details for trip 501" | get_trip_details | Object |
| "list all stops" | list_all_stops | Table |
| "show stops for path 1" | list_stops_for_path | Table |
| "routes using path Downtown" | list_routes_using_path | Table |

### ✏️ Create & Modify (5 actions - Instant)
| Command Example | Action | Output |
|----------------|--------|--------|
| "create stop Library at 12.34, 56.78" | create_stop | Object |
| "create path X with stops A, B, C" | create_path | Object |
| "create route Morning using path X" | create_route | Object |
| "rename stop Library to Central Library" | rename_stop | Object |
| "duplicate route 1" | duplicate_route | Object |

### 🚌 Trip Operations (4 actions - With Confirmation)
| Command Example | Action | Confirmation |
|----------------|--------|--------------|
| "cancel trip 501" | cancel_trip | If bookings exist |
| "remove vehicle from trip 501" | remove_vehicle | If bookings exist |
| "assign vehicle 5 to trip 502" | assign_vehicle | If already assigned |
| "update trip 501 time to 9:00" | update_trip_time | If bookings exist |

### 💡 Help (1 action)
| Command Example | Action | Output |
|----------------|--------|--------|
| "how do I create a route?" | create_new_route_help | Help Card |

---

## 🎨 Output Formats

### TableCard
Used for: Lists of vehicles, stops, routes
```
┌─────────────────────────────────────┐
│ Vehicle ID │ Registration │ Status │
├─────────────────────────────────────┤
│ 5          │ KA-01-AB-1234│ avail. │
│ 7          │ KA-01-CD-5678│ avail. │
└─────────────────────────────────────┘
Showing 2 rows
```

### ListCard
Used for: Simple ordered lists
```
┌─────────────────────────────┐
│ ① Airport                   │
│ ② City Center               │
│ ③ University                │
└─────────────────────────────┘
3 items
```

### ObjectCard
Used for: Detailed entity data
```
┌─────────────────────────────┐
│ Trip ID: 501                │
│ Route Name: Morning Express │
│ Status: SCHEDULED           │
│ Bookings: 5                 │
└─────────────────────────────┘
4 fields
```

### HelpCard
Used for: Interactive guides
```
┌─────────────────────────────┐
│ 💡 How to Create a Route    │
├─────────────────────────────┤
│ ① Go to Manage Routes page  │
│ ② Create stops first        │
│ ③ Create path with stops    │
│ ④ Create route using path   │
└─────────────────────────────┘
```

---

## 🔄 Workflow Examples

### Scenario 1: View Available Resources
```
User: "show me unassigned vehicles"
→ TableCard with vehicles

User: "list all stops"
→ TableCard with stops

User: "which routes use path 1?"
→ TableCard with routes
```

### Scenario 2: Create New Route
```
User: "how do I create a route?"
→ HelpCard with guide

User: "create stop Library at 12.34, 56.78"
→ ✅ Created stop 'Library' (ObjectCard)

User: "create path School-Library with stops School, Library"
→ ✅ Created path with 2 stops (ObjectCard)

User: "create route Morning Route using School-Library"
→ ✅ Created route (ObjectCard)
```

### Scenario 3: Manage Trip (With Confirmation)
```
User: "check trip 501"
→ ObjectCard with trip details

User: "cancel trip 501"
→ ⚠️ This trip has 5 bookings. Confirm?
→ [Confirm] ✅ Trip cancelled

User: "update trip 502 time to 9:00"
→ ⚠️ Changing time will affect 3 passengers. Confirm?
→ [Confirm] ✅ Time updated
```

### Scenario 4: Duplicate Existing Route
```
User: "routes using path Downtown"
→ TableCard showing route IDs

User: "duplicate route 1"
→ ✅ Duplicated route (new ID: 13) (ObjectCard)
```

---

## ⚡ Tips & Tricks

### Natural Language
- ✅ "show me" / "list" / "get" / "find"
- ✅ "create" / "make" / "add"
- ✅ "remove" / "delete" / "cancel"
- ✅ "update" / "change" / "modify"

### Entity Resolution
- Use numeric IDs: "trip 501", "path 1", "route 3"
- Use labels: "trip Bulk - 00:01", "path Downtown"
- Use OCR (frontend): Auto-detected from selected trip

### Time Formats
- ✅ "9:00" / "09:00" / "9am" / "9 AM"
- ✅ Parsed flexibly by LLM

### Stop Creation
- Format: "create stop [NAME] at [LAT], [LON]"
- Example: "create stop Airport at 12.9716, 77.5946"

### Path Creation
- Format: "create path [NAME] with stops [STOP1], [STOP2], ..."
- Example: "create path Route-A with stops Airport, City Center, University"

---

## 🛡️ Safety Features

### Safe Actions (Instant Execution)
- All READ operations
- create_stop, create_path, create_route
- rename_stop, duplicate_route

### Risky Actions (Require Confirmation)
- cancel_trip (if bookings exist)
- remove_vehicle (if bookings exist)
- update_trip_time (if bookings exist)
- assign_vehicle (if already assigned)

### Audit Trail
All mutations logged with:
- Action type
- Entity ID
- User ID
- Old/new values
- Timestamp

---

## 🎯 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Enter | Send message |
| Esc | Close widget |

---

## 🔧 Troubleshooting

### "Trip not found"
→ Check trip ID or use more specific label

### "Path not found"
→ Verify path exists with "list all stops"

### "Route not found"
→ Use "routes using path X" to find route IDs

### "Missing parameters"
→ Check command format in examples above

---

## 📞 Support Commands

| Command | Response |
|---------|----------|
| "help" | General help message |
| "how do I create a route?" | Step-by-step guide |
| "what can you do?" | List all capabilities |

---

## 📊 Performance

- **Response Time**: < 2 seconds (with LLM)
- **Max Rows**: Handles 100+ rows smoothly
- **Confirmation**: < 500ms round-trip
- **Error Recovery**: Graceful fallback

---

*Quick Reference v1.0 - November 14, 2024*
