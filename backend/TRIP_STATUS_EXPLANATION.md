# 🚦 Trip Status Explained: SCHEDULED vs IN_PROGRESS

## 📋 Trip Status Lifecycle in Movi

```
SCHEDULED → IN_PROGRESS → COMPLETED
    ↓           ↓             ↓
   📅          🚛            ✅
  Planned    Happening     Finished
```

## 🔍 Status Definitions

### 📅 **SCHEDULED**
- **Meaning**: Trip is planned but hasn't started yet
- **Time**: Trip time is in the future
- **Vehicle**: May or may not be assigned
- **Driver**: May or may not be assigned  
- **Passengers**: Can still book seats
- **Operations**: Still in planning phase

**Example**: 
```
Trip: Path-1 - 18:30 (6:30 PM today)
Current Time: 2:00 PM
Status: SCHEDULED (4.5 hours until departure)
```

### 🚛 **IN_PROGRESS**
- **Meaning**: Trip is currently happening/executing
- **Time**: Trip is actively running
- **Vehicle**: Deployed and moving
- **Driver**: Actively driving the route
- **Passengers**: On board or boarding
- **Operations**: Live tracking, real-time updates

**Example**:
```  
Trip: Path-2 - 19:45 (7:45 PM today)
Current Time: 8:15 PM  
Status: IN_PROGRESS (30 minutes into journey)
```

### ✅ **COMPLETED**  
- **Meaning**: Trip finished successfully
- **Time**: Trip end time has passed
- **Vehicle**: Returned to depot/available
- **Driver**: Completed shift
- **Passengers**: All dropped off
- **Operations**: Final reports generated

## 🎯 Real Examples from Your Database

Looking at your dashboard screenshot:

### Trip Examples:
```
Path-1 - 18:30  → SCHEDULED
├─ Status: SCHEDULED
├─ Deployment: Has deployment_id (23) 
├─ Driver: Assigned (Driver #7)
├─ Vehicle: Not assigned yet
└─ Why SCHEDULED: Trip time hasn't arrived yet

Path-2 - 19:45  → IN_PROGRESS  
├─ Status: IN_PROGRESS
├─ Deployment: Complete deployment
├─ Vehicle: Active on route
├─ Driver: Currently driving
└─ Why IN_PROGRESS: Trip is currently happening

Path-3 - 20:00  → COMPLETED
├─ Status: COMPLETED  
├─ Deployment: Was complete, now finished
├─ Vehicle: Available for next trip
├─ Driver: Shift completed
└─ Why COMPLETED: Trip finished successfully
```

## 🕒 **Status Transitions**

### Automatic Transitions:
```python
# System automatically updates based on time
if current_time >= trip_start_time:
    status = "IN_PROGRESS"
    
if current_time >= trip_end_time:
    status = "COMPLETED"
```

### Manual Transitions:
```python  
# Dispatcher can manually update
- Start trip early: SCHEDULED → IN_PROGRESS
- End trip early: IN_PROGRESS → COMPLETED  
- Cancel trip: Any status → CANCELLED
```

## 🎯 **Operational Implications**

### SCHEDULED Trips:
- ✅ Can modify deployment (assign/remove vehicles)
- ✅ Can change drivers
- ✅ Passengers can cancel bookings
- ✅ Route can be adjusted
- ✅ Time can be modified

### IN_PROGRESS Trips:
- ❌ Cannot change vehicle (already deployed)
- ❌ Cannot change driver (already driving)
- ⚠️ Limited passenger changes
- ⚠️ Route changes only for safety
- ✅ Can track live location

### COMPLETED Trips:
- ❌ Cannot modify anything
- ✅ View historical data
- ✅ Generate reports
- ✅ Resources available for new trips

## 🔧 **Why This Matters for Your Testing**

### When Testing Vehicle Assignment:

**SCHEDULED Trip (Trip 2)**:
- ✅ Should allow vehicle assignment
- ✅ Should allow driver assignment  
- ✅ Should allow deployment modifications

**IN_PROGRESS Trip (Trip 4)**:
- ❌ Should block vehicle changes (disrupts live operations)
- ❌ Should block driver changes
- ⚠️ May allow emergency overrides

**COMPLETED Trip (Trip 6)**:
- ❌ Should block all modifications
- ✅ Should show historical data only

## 📱 **UI Behavior**

### Dashboard Display:
```
SCHEDULED trips:
- Show as "Pending" or "Upcoming"  
- Allow edit buttons
- Show countdown to departure

IN_PROGRESS trips:
- Show as "Live" or "Active"
- Show live tracking
- Limited edit options

COMPLETED trips:  
- Show as "Finished"
- No edit buttons
- Historical view only
```

## 🎯 **Summary**

| Status | Phase | Time | Can Edit? | Vehicle Assignment |
|--------|-------|------|-----------|-------------------|
| **SCHEDULED** | 📅 Planning | Future | ✅ Yes | ✅ Should work |
| **IN_PROGRESS** | 🚛 Active | Current | ⚠️ Limited | ❌ Should block |
| **COMPLETED** | ✅ Finished | Past | ❌ No | ❌ Should block |

**For your testing**: 
- Use **SCHEDULED** trips (like Trip 2) for vehicle assignment tests
- **IN_PROGRESS** trips should block modifications to prevent operational disruption
- **COMPLETED** trips are read-only historical records
