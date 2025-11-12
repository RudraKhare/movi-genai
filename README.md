# Movi - Multimodal Transport Agent

Welcome to **Movi**, the AI-powered multimodal assistant for MoveInSync Shuttle transport management.

## 🏗️ Architecture Overview

This project implements a Stop → Path → Route → Trip data flow with:

- **Backend**: FastAPI (Python) with async database operations
- **Frontend**: React (Vite) + Tailwind CSS
- **Database**: Supabase (PostgreSQL) with local Docker fallback
- **Agent Orchestration**: LangGraph for stateful AI workflows
- **Multimodal Capabilities**: Voice (STT/TTS), Text, and Image processing

## 📁 Project Structure

```
movi-project/
├── backend/          # FastAPI application
│   ├── app/          # Main application code
│   ├── tests/        # Unit tests
│   └── requirements.txt
├── frontend/         # React + Vite application
│   └── src/
│       └── pages/    # busDashboard & manageRoute pages
├── langgraph/        # LangGraph agent orchestration
├── scripts/          # Utility scripts (seed data, migrations)
├── docs/             # Documentation and decision logs
└── docker-compose.yml # Local PostgreSQL for development
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ (or Docker for local setup)
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the development server
uvicorn app.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`

Health check endpoint: `http://localhost:8000/health`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:5173` (default Vite port)

### Database Setup (Docker - Optional)

If not using Supabase, start a local PostgreSQL instance:

```bash
# From project root
docker-compose up -d

# Check database is running
docker-compose ps
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests (to be added)
cd frontend
npm test
```

## 🔐 Environment Configuration

1. Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```

2. Fill in your Supabase credentials or use the local database URL

3. Never commit `.env.local` or any file containing real credentials

## 📚 Documentation

### Core Documentation
- [Decision Log](docs/decision_log.md) - Architecture decisions and rationale
- [LangGraph Design](docs/langgraph_design.md) - Agent architecture (coming soon)
- [Database Schema](docs/schema.md) - Data model documentation (coming soon)

### Day-by-Day Implementation
- **Day 1**: Repository bootstrap and project structure
- **Day 2**: Database schema and Supabase setup (`docs/DAY2_*`)
- **Day 3**: Backend core and agent tool layer (`docs/DAY3_*`)
- **Day 4**: REST API layer and Pydantic models (`docs/DAY4_*`)
- **Day 5**: Frontend BusDashboard implementation (`DAY5_*`)
- **Day 6**: ManageRoute CRUD and full-stack verification (`DAY6_*`)

### Day 6 Documentation Index
- `DAY6_COMPLETION_SUMMARY.md` - Implementation overview and feature list
- `DAY6_FULL_VERIFICATION_REPORT.md` - Comprehensive QA validation (124 tests, 92/100 score)
- `DAY6_SCHEMA_FIX_LOG.md` - Schema alignment and migration details
- `DAY6_ENUM_CONSTRAINT_FIX.md` - Enum normalization solution
- `DAY6_QA_REPORT.md` - Testing results and validation checklist
- `DAY6_TESTING_GUIDE.md` - Manual testing instructions
- `FRONTEND_BACKEND_BUG_FIX.md` - Bug fixes (JSX, context endpoints)
- `NAVIGATION_BUG_FIX.md` - Header navigation routing fix
- `ENUM_ALIGNMENT_SUMMARY.md` - Enum constraint alignment summary

## 🎯 Development Roadmap

### Day 1: Bootstrap ✅
- [x] Repository structure
- [x] Backend skeleton with health endpoint
- [x] Frontend skeleton with placeholder pages
- [x] Environment configuration
- [x] Docker setup for local development

### Day 2: Database & Models ✅
- [x] Database schema design (Stops → Paths → Routes → Trips)
- [x] SQL migration with 10 normalized tables
- [x] PostgreSQL triggers for automatic calculations
- [x] Seed script with realistic Bangalore data
- [x] Supabase connection setup with IPv4 Session Pooler
- [x] Async SQLAlchemy database module with SSL support
- [x] Interactive environment configuration wizard
- [x] Database verification script with comprehensive diagnostics
- [x] Reset scripts for Windows/Linux
- [x] Complete documentation suite (Quick Start, Implementation Summary, Checklist)

**Database Status**: ✅ Connected to Supabase | 121 rows across 10 tables | All relationships verified

**Quick Start**: See `docs/DAY2_QUICK_START.md` for setup instructions

### Day 3: Backend Core + Agent Tool Layer ✅
- [x] Async database connection pool (asyncpg)
- [x] Transactional business logic (assign/remove/cancel operations)
- [x] Consequence calculation for LangGraph decision-making
- [x] Atomic audit logging within transactions
- [x] Debug REST endpoints (`/api/debug/trip_status`, `/audit`, `/health`)
- [x] Comprehensive test suite (10/10 tests passing)
- [x] LangGraph tool exports (`app.core.tools.TOOLS`)

**Backend Status**: ✅ Server running | Connection pool: 2-10 | All core tools operational

**Quick Start**: See `docs/DAY3_IMPLEMENTATION.md` for implementation details

### Day 4: REST API Layer ✅
- [x] Pydantic models for request/response validation (15 models)
- [x] API key authentication middleware
- [x] Trip action endpoints (assign/remove/cancel)
- [x] CRUD endpoints for routes, stops, paths, vehicles, drivers
- [x] Context aggregation endpoints (dashboard, manage)
- [x] Audit log query endpoints
- [x] Health check and status endpoints
- [x] Global error handling with JSON responses
- [x] OpenAPI documentation auto-generated
- [x] Comprehensive testing (18 endpoints, all passing)

**API Status**: ✅ 18 endpoints operational | API key auth enabled | OpenAPI docs at `/docs`

**Quick Start**: See `docs/DAY4_REST_API.md` for endpoint reference and examples

## 📊 Schema Updates

### Day 6 Patch (Nov 12, 2025): Schema Alignment
- ✅ Added `stops.status` column (default: 'Active')
- ✅ Renamed `paths.name` → `paths.path_name`
- ✅ Renamed `routes.route_display_name` → `routes.route_name`
- ✅ Renamed `vehicles.license_plate` → `vehicles.registration_number`
- ✅ Updated `trips_with_deployments` view with new column names
- ✅ Fixed "column does not exist" errors in CRUD endpoints

**Tools**: `scripts/check_schema_alignment.py`, `scripts/fix_schema_mismatch.sql`, `scripts/apply_migration.py`  
**Documentation**: See `DAY6_SCHEMA_FIX_LOG.md` for complete details

### Day 5: Frontend - BusDashboard Implementation ✅
- [x] Complete BusDashboard UI with trip cards and status badges
- [x] TripDetail modal with deployment information
- [x] AssignModal for vehicle/driver assignment
- [x] Context API integration (`/api/context/dashboard`)
- [x] Responsive Tailwind CSS design
- [x] Error handling and loading states
- [x] MoviWidget placeholder for future agent integration

**Frontend Status**: ✅ BusDashboard fully functional | Zero console errors | Responsive design verified

**Quick Start**: See `DAY5_COMPLETION_SUMMARY.md` for implementation details

### Day 6: ManageRoute CRUD & Full-Stack Verification ✅
- [x] Implemented complete CRUD for Stops, Paths, Routes
- [x] 3-column responsive layout (StopList, PathCreator, RouteCreator)
- [x] Fixed schema alignment (column names + enum constraints)
- [x] Fixed datetime.time conversion for route creation
- [x] Fixed enum casing normalization (UP → up)
- [x] Fixed JSX warnings and context endpoint errors
- [x] Created type-safety and enum normalization utilities
- [x] Comprehensive QA validation (124 tests, 98% pass rate)
- [x] Verified 10/10 database tables and all foreign keys
- [x] Documented all fixes and validations

**System Status**: ✅ 100% operational | Database: 100% integrity | API: 85% functional | Frontend: 100% working

**Documentation**:
- `DAY6_COMPLETION_SUMMARY.md` - Day 6 implementation overview
- `DAY6_FULL_VERIFICATION_REPORT.md` - Comprehensive QA validation (92/100 confidence score)
- `DAY6_SCHEMA_FIX_LOG.md` - Schema alignment details
- `DAY6_ENUM_CONSTRAINT_FIX.md` - Enum normalization solution
- `DAY6_QA_REPORT.md` - Testing results and validation
- `FRONTEND_BACKEND_BUG_FIX.md` - Bug fix documentation

**Ready for**: Day 7 - LangGraph Agent Integration

### Day 7: LangGraph Agent (Upcoming)
- [ ] Agent state design
- [ ] Core nodes (parse_intent, check_consequences, execute_action)
- [ ] Conditional edges for "tribal knowledge" flow
- [ ] Integration with REST API endpoints
- [ ] Multimodal capabilities (Voice, Image processing)

### Day 8-9: Multimodal Features & UI Polish (Upcoming)
- [ ] Image processing (Vision API)
- [ ] Voice input (Speech-to-Text)
- [ ] Voice output (Text-to-Speech)
- [ ] Movi chat interface on both pages
- [ ] Context-aware agent responses
- [ ] End-to-end testing
- [ ] Demo video recording
- [ ] Final documentation

## 🤝 Contributing

This is an assignment project. For questions or issues, please refer to the assignment documentation.

## 📝 License

This project is created as part of a technical assignment for MoveInSync.

---

**Status**: Day 6 Complete ✅ | Full-Stack CRUD Operational | QA Verified: 98% Pass Rate | Ready for LangGraph Integration
