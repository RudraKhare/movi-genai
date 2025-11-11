# Day 2: Database Schema & Seed Data - Implementation Guide

## 🎯 Objective
Create a production-grade relational database schema in Supabase/PostgreSQL that models the complete Stop → Path → Route → Trip hierarchy, and populate it with realistic dummy data.

---

## 📁 Files Created

### 1. Database Migration
**File**: `migrations/001_init.sql`
- Complete DDL for all 10 tables
- Foreign key constraints with cascade rules
- Check constraints for data validation
- Indexes for query performance
- Trigger function for automatic booking percentage calculation
- Denormalized view (`trips_with_deployments`) for dashboard queries

**Tables Created:**
- **Static Assets** (manageRoute page):
  - `stops` - Physical locations
  - `paths` - Named sequences of stops
  - `path_stops` - Many-to-many mapping with order
  - `routes` - Path + Time + Direction

- **Dynamic Assets** (busDashboard page):
  - `vehicles` - Transport assets (buses/cabs)
  - `drivers` - Personnel
  - `daily_trips` - Daily trip instances
  - `deployments` - Vehicle+Driver assignments
  - `bookings` - Employee bookings (for consequence checking)
  - `audit_logs` - Agent action history

### 2. Seed Script
**File**: `scripts/seed_db.py`
- Supports both Supabase and direct PostgreSQL connections
- Clears existing data for idempotent re-runs
- Inserts realistic Bangalore location data
- Creates 12 stops, 4 paths, 8 routes, 10 vehicles, 8 drivers
- Generates 10+ daily trips with deployments and bookings
- Automatically calculates booking percentages

**Data Seeded:**
- ✅ 12 realistic Bangalore stops (Gavipuram, Peenya, Electronic City, etc.)
- ✅ 4 paths with ordered stop sequences
- ✅ 8 routes (morning/evening shifts)
- ✅ 10 vehicles (buses and cabs with realistic capacity)
- ✅ 8 drivers with license numbers
- ✅ 10 daily trips with varied booking percentages
- ✅ 7 vehicle deployments
- ✅ 40+ employee bookings (75% confirmed, 25% cancelled)

### 3. Reset Scripts
**Files**:
- `scripts/reset_db.sh` - Bash script for Linux/Mac
- `scripts/reset_db.ps1` - PowerShell script for Windows

Both scripts:
- Drop all tables
- Run migration
- Seed fresh data
- Include safety confirmation prompt

### 4. Documentation
**File**: `docs/SUPABASE_SETUP.md`
- Step-by-step Supabase account creation
- How to get API keys and database URL
- Environment variable configuration
- Migration and seeding instructions
- Troubleshooting guide
- SQL verification queries

---

## 🗄️ Database Schema Design

### Entity Relationship Diagram

```
stops (12)
  ↓
path_stops (20+)  ←→  paths (4)
                        ↓
                      routes (8)
                        ↓
                    daily_trips (10+)
                        ↓
                   deployments (7+)  →  vehicles (10)
                        ↓                    ↓
                    bookings (40+)      drivers (8)
```

### Key Design Decisions

1. **Normalized Schema**: Separate tables for each entity to maintain data integrity
2. **Cascade Deletes**: Remove a path → automatically removes related routes and trips
3. **Check Constraints**: Enforce valid statuses, percentages, and vehicle types
4. **Automatic Triggers**: Booking percentage recalculates on insert/update/delete
5. **Denormalized View**: `trips_with_deployments` for efficient dashboard queries
6. **Audit Logging**: Track all agent actions for accountability

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+ with virtual environment activated
- Supabase account OR local PostgreSQL instance

### Option 1: Supabase (Recommended)

1. **Create Supabase Project**:
   ```
   Go to: https://app.supabase.com
   Create new project: movi-transport
   Choose region: Singapore/closest to you
   ```

2. **Get Credentials** (Project Settings → API & Database):
   ```
   SUPABASE_URL=https://[project-id].supabase.co
   SUPABASE_ANON_KEY=eyJhbGc...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
   DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
   ```

3. **Configure Environment**:
   ```powershell
   # Edit .env.local (copy from .env.example)
   # Add the 4 credentials above
   ```

4. **Run Migration** (Supabase SQL Editor):
   ```sql
   -- Copy contents of migrations/001_init.sql
   -- Paste into SQL Editor
   -- Click "Run"
   ```

5. **Seed Database**:
   ```powershell
   cd c:\Users\rudra\Desktop\movi
   cd backend
   .\.venv\Scripts\Activate.ps1
   cd ..
   python scripts\seed_db.py
   ```

### Option 2: Local PostgreSQL

1. **Start Database**:
   ```powershell
   docker-compose up -d
   ```

2. **Set DATABASE_URL** in `.env.local`:
   ```
   DATABASE_URL=postgresql://movi:movi_pwd@localhost:5432/movi_dev
   ```

3. **Run Migration**:
   ```powershell
   psql $env:DATABASE_URL -f migrations\001_init.sql
   ```

4. **Seed Database**:
   ```powershell
   python scripts\seed_db.py
   ```

---

## ✅ Validation & Testing

### 1. Verify Tables Created

**Supabase**: Table Editor → should show 10 tables

**SQL Query**:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

**Expected Output**: 10 tables (audit_logs, bookings, daily_trips, deployments, drivers, paths, path_stops, routes, stops, vehicles)

### 2. Verify Seeded Data

```sql
-- Check daily trips
SELECT * FROM daily_trips LIMIT 5;

-- Expected: 10+ rows with varied booking percentages

-- Check bookings
SELECT COUNT(*) FROM bookings WHERE status = 'CONFIRMED';

-- Expected: 30+ confirmed bookings

-- Check trips with high bookings (for consequence testing)
SELECT 
  display_name, 
  booking_status_percentage, 
  live_status 
FROM daily_trips 
WHERE booking_status_percentage > 50
ORDER BY booking_status_percentage DESC;

-- Expected: At least 3 trips with >50% bookings

-- Check deployed trips
SELECT * FROM trips_with_deployments;

-- Expected: 7+ rows with vehicle and driver assignments
```

### 3. Test Relationships

```sql
-- Verify path-stop relationships
SELECT 
  p.name as path_name,
  s.name as stop_name,
  ps.stop_order
FROM paths p
JOIN path_stops ps ON p.path_id = ps.path_id
JOIN stops s ON ps.stop_id = s.stop_id
ORDER BY p.name, ps.stop_order;

-- Expected: 20+ rows showing ordered stops for each path

-- Verify trip-route-path linkage
SELECT 
  dt.display_name,
  r.route_display_name,
  r.shift_time,
  p.name as path_name
FROM daily_trips dt
JOIN routes r ON dt.route_id = r.route_id
JOIN paths p ON r.path_id = p.path_id
LIMIT 10;

-- Expected: Complete join without NULL values
```

### 4. Test Automatic Booking Percentage Calculation

```sql
-- Add a booking and verify percentage updates
INSERT INTO bookings (trip_id, user_id, user_name, seats, status)
VALUES (1, 9999, 'Test User', 2, 'CONFIRMED');

-- Check if booking_status_percentage updated
SELECT trip_id, display_name, booking_status_percentage 
FROM daily_trips 
WHERE trip_id = 1;

-- Expected: Percentage should reflect the new booking
```

---

## 📊 Data Statistics

After successful seeding:

| Entity | Count | Notes |
|--------|-------|-------|
| Stops | 12 | Realistic Bangalore locations |
| Paths | 4 | Named route sequences |
| Path-Stop Links | 20+ | Ordered stop sequences |
| Routes | 8 | Morning & evening shifts |
| Vehicles | 10 | Mix of buses (40-50 capacity) and cabs (4-6) |
| Drivers | 8 | With license numbers and phone |
| Daily Trips | 10+ | Today's date, varied statuses |
| Deployments | 7+ | Vehicle + driver assignments |
| Bookings | 40+ | 75% confirmed, 25% cancelled |

---

## 🧪 Acceptance Criteria - Verification

### ✅ All tables created successfully
```sql
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = 'public';
-- Expected: 10
```

### ✅ SELECT * FROM daily_trips returns ≥10 rows
```sql
SELECT COUNT(*) FROM daily_trips;
-- Expected: ≥10
```

### ✅ At least 3 trips have bookings >50%
```sql
SELECT COUNT(*) FROM daily_trips 
WHERE booking_status_percentage > 50;
-- Expected: ≥3
```

### ✅ CONFIRMED bookings exist
```sql
SELECT COUNT(*) FROM bookings 
WHERE status = 'CONFIRMED';
-- Expected: >30
```

### ✅ Foreign key relationships work
```sql
-- This should work without errors
SELECT 
  dt.display_name,
  v.license_plate,
  d.name as driver_name
FROM daily_trips dt
JOIN deployments dep ON dt.trip_id = dep.trip_id
JOIN vehicles v ON dep.vehicle_id = v.vehicle_id
JOIN drivers d ON dep.driver_id = d.driver_id;
-- Expected: 7+ rows
```

---

## 🌳 Git Workflow

### Branch & Commit

```powershell
# Create feature branch
git checkout -b feat/db-schema-seed

# Stage files
git add migrations/ scripts/ docs/

# Commit
git commit -m "feat(db): add Supabase schema and realistic seed data

- Create 10-table normalized schema (Stop→Path→Route→Trip hierarchy)
- Implement automatic booking percentage calculation via triggers
- Add seed script with 12 stops, 8 routes, 10 vehicles, 40+ bookings
- Include reset scripts for Windows (PowerShell) and Linux (Bash)
- Add comprehensive Supabase setup guide

Tables: stops, paths, path_stops, routes, vehicles, drivers, daily_trips, deployments, bookings, audit_logs
"

# Push to GitHub
git push -u origin feat/db-schema-seed
```

### Pull Request

**Title**: "Database schema and seed data for MOVI (Stops–Routes–Trips–Bookings)"

**Description**:
```markdown
## 🎯 What's New

This PR implements the complete database layer for the MOVI transport management system.

### Database Schema
- ✅ 10 normalized tables with foreign key constraints
- ✅ Automatic booking percentage calculation via PostgreSQL triggers
- ✅ Denormalized view for efficient dashboard queries
- ✅ Indexes on frequently queried columns

### Seed Data
- ✅ 12 realistic Bangalore stops
- ✅ 4 paths with ordered stop sequences
- ✅ 8 routes (morning/evening shifts)
- ✅ 10 vehicles with realistic capacities
- ✅ 40+ bookings (for consequence checking)

### Scripts
- ✅ Migration SQL (migrations/001_init.sql)
- ✅ Python seed script (supports Supabase & PostgreSQL)
- ✅ Reset scripts for Windows & Linux

### Documentation
- ✅ Supabase setup guide
- ✅ Verification queries
- ✅ Troubleshooting tips

## 🧪 Testing

All acceptance criteria met:
- [x] All 10 tables created
- [x] 10+ daily trips seeded
- [x] 3+ trips with >50% bookings
- [x] Foreign keys enforce referential integrity
- [x] Triggers automatically recalculate percentages

## 📸 Screenshots

[Add screenshot of Supabase Table Editor showing all 10 tables]
[Add screenshot of daily_trips table with data]

## 🔗 Related

- Assignment requirement: Stop → Path → Route → Trip hierarchy
- Foundation for Day 3: FastAPI CRUD endpoints
- Enables Day 4: LangGraph consequence checking
```

---

## ⚠️ Known Issues & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Running seed twice creates duplicates | Medium | Seed script clears data first (`TRUNCATE CASCADE`) |
| Supabase service role key exposure | High | Added to `.gitignore`, documented in setup guide |
| Booking percentage doesn't update | Medium | PostgreSQL trigger automatically recalculates |
| Foreign key errors on manual data entry | Low | Schema enforces integrity with helpful error messages |

---

## 🔮 Next Steps (Day 3)

With the database layer complete, Day 3 will focus on:

1. **SQLAlchemy Models**: Python ORM models for all 10 tables
2. **FastAPI CRUD Endpoints**: 
   - `/api/stops` (GET, POST, PUT, DELETE)
   - `/api/paths`
   - `/api/routes`
   - `/api/daily_trips`
   - `/api/vehicles`
   - `/api/drivers`
   - `/api/deployments`
   - `/api/bookings`
3. **Database Connection Pool**: Async connection management
4. **Alembic Setup**: For future schema migrations
5. **Integration Tests**: Test CRUD operations against seeded data

---

## 📚 References

- **Assignment**: "Building Movi - The Multimodal Transport Agent"
- **Database**: PostgreSQL 15 via Supabase
- **Migration File**: `migrations/001_init.sql`
- **Seed Script**: `scripts/seed_db.py`
- **Setup Guide**: `docs/SUPABASE_SETUP.md`

---

**Status**: Day 2 Complete ✅  
**Next**: Day 3 - FastAPI CRUD Endpoints & SQLAlchemy Models
