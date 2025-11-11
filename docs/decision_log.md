# Decision Log

This document tracks key architectural and implementation decisions for the Movi project.

## Day 1: Bootstrap Phase

### Backend Framework: FastAPI
**Decision**: Use FastAPI (Python) for the backend API  
**Rationale**:
- Native async/await support for database and I/O operations
- Excellent integration with Python ML/AI ecosystem (LangGraph, LangChain)
- Automatic OpenAPI documentation
- Type hints and Pydantic validation out of the box
- Lightweight and fast for prototyping

**Alternatives Considered**:
- Django REST Framework (too heavy for this prototype)
- Express.js (would require bridging to Python for LangGraph)

---

### Database: Supabase (PostgreSQL)
**Decision**: Use Supabase as primary database with Docker PostgreSQL fallback  
**Rationale**:
- PostgreSQL is robust for relational data (Stop → Path → Route → Trip)
- Supabase provides instant API, authentication, and real-time subscriptions
- Easy to switch to self-hosted PostgreSQL if needed
- Good support for geospatial data (latitude/longitude for stops)

**Fallback**: Docker Compose with PostgreSQL 15 for local development without internet dependency

---

### Frontend: React (Vite) + Tailwind CSS
**Decision**: Use Vite as build tool with React and Tailwind CSS  
**Rationale**:
- Vite offers extremely fast hot module replacement (HMR)
- React is widely known and has rich ecosystem
- Tailwind CSS enables rapid UI development matching screenshots
- Assignment encourages use of AI coding assistants, which work well with this stack

**Alternatives Considered**:
- Next.js (overkill for 2-page prototype)
- Vue.js (team preference for React)

---

### Agent Orchestration: LangGraph
**Decision**: Use LangGraph (Python) for AI agent state management  
**Rationale**:
- **Core requirement** of the assignment
- Purpose-built for stateful, multi-step agent workflows
- Explicit graph structure makes "tribal knowledge" consequence checking tractable
- Built on top of LangChain, providing access to vast tool ecosystem

---

### Voice/Speech: Web Speech API + Optional Whisper
**Decision**: Start with browser Web Speech API, add Whisper server if needed  
**Rationale**:
- Web Speech API (STT/TTS) is zero-setup for prototype
- Browser support is good in Chrome/Edge
- Can upgrade to OpenAI Whisper API or self-hosted Whisper for production
- Keeps initial setup simple

---

### Image Processing: Vision API (GPT-4 Vision or similar)
**Decision**: Use OpenAI GPT-4 Vision API for image understanding  
**Rationale**:
- Assignment requires image input (screenshot analysis)
- GPT-4V can identify UI elements from screenshots
- Can extract trip names, routes, or other data from images
- Alternative: Google Cloud Vision API or local OCR (Tesseract) as fallback

---

### ORM: SQLAlchemy (async)
**Decision**: Use SQLAlchemy 2.0 with async support  
**Rationale**:
- De facto standard Python ORM
- Excellent async support with asyncpg driver
- Type-safe with Python type hints
- Works well with Alembic for migrations

---

### Testing: pytest + TestClient
**Decision**: Use pytest with Starlette TestClient  
**Rationale**:
- pytest is the Python standard for testing
- TestClient allows testing FastAPI endpoints without running server
- Easy to add fixtures for database, mocks, etc.

---

### Version Control & Branching
**Decision**: Git with feature branches, PRs to `develop` or `main`  
**Rationale**:
- Standard industry practice
- Allows incremental review and validation
- Branch naming: `chore/bootstrap`, `feat/db-schema`, `feat/langgraph-agent`, etc.

---

## Deferred Decisions (To be made in later phases)

### Authentication Strategy
- Options: Supabase Auth, JWT tokens, OAuth
- Decision deferred until UI integration phase

### Deployment Target
- Options: Vercel (frontend), Railway/Render (backend), Docker containers
- Decision deferred until prototype is functional

### Monitoring & Logging
- Options: Sentry, LogRocket, custom logging
- Decision deferred until production readiness

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Supabase account setup delayed | High | Use Docker Compose local PostgreSQL fallback |
| LangGraph API changes | Medium | Pin specific version in requirements.txt |
| Tesseract OCR not installed in CI | Low | Document system dependency, add to Dockerfile |
| Web Speech API browser compatibility | Medium | Provide text fallback, document browser requirements |
| OpenAI API rate limits | Medium | Implement retry logic, use local models as fallback |

---

## Next Steps (Day 2)

1. Design and implement database schema (Stops, Paths, Routes, Vehicles, Trips, Deployments)
2. Set up Alembic for migrations
3. Create seed script with realistic dummy data matching assignment screenshots
4. Add SQLAlchemy async models
5. Create database connection pool and session management

---

**Last Updated**: Day 1 - Bootstrap Phase  
**Status**: Foundation complete, ready for data layer implementation
