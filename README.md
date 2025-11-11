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

- [Decision Log](docs/decision_log.md) - Architecture decisions and rationale
- [LangGraph Design](docs/langgraph_design.md) - Agent architecture (coming soon)
- [Database Schema](docs/schema.md) - Data model documentation (coming soon)

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

### Day 5: LangGraph Agent
- [ ] Agent state design
- [ ] Core nodes (parse_intent, check_consequences, execute_action)
- [ ] Conditional edges for "tribal knowledge" flow
- [ ] Integration with REST API endpoints

### Day 6: Multimodal Features
- [ ] Image processing (Vision API)
- [ ] Voice input (Speech-to-Text)
- [ ] Voice output (Text-to-Speech)

### Day 5: UI Polish & Integration
- [ ] Complete busDashboard UI using `/api/context/dashboard`
- [ ] Complete manageRoute UI using `/api/context/manage`
- [ ] Movi chat interface on both pages
- [ ] Context-aware agent responses

### Day 6: Testing & Demo
- [ ] End-to-end testing
- [ ] Demo video recording
- [ ] Final documentation

## 🤝 Contributing

This is an assignment project. For questions or issues, please refer to the assignment documentation.

## 📝 License

This project is created as part of a technical assignment for MoveInSync.

---

**Status**: Day 4 Complete ✅ | Backend: 18 REST endpoints operational | API Docs: http://localhost:8000/docs
