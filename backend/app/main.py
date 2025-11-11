"""
Movi Backend - FastAPI Application
Main entry point for the transport management API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager

# Import REST API routers
from app.api import routes, actions, context, audit, health

# Import debug router (from Day 3)
from app.routers import debug

# Import middleware
from app.middleware import add_middlewares

# Import DB initialization
from app.core.supabase_client import init_db_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes DB pool on startup and closes it on shutdown.
    """
    # Startup: Initialize database connection pool
    print("🚀 Starting Movi backend API...")
    try:
        await init_db_pool(min_size=2, max_size=10)
        print("✅ Database pool initialized")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize database pool: {e}")
        print("   Some endpoints may not work until DATABASE_URL is configured.")
    
    yield
    
    # Shutdown: Close database connection pool
    print("🛑 Shutting down Movi backend...")
    await close_pool()
    print("✅ Database pool closed")


app = FastAPI(
    title="MOVI Backend API",
    description="Backend API for MOVI – the multimodal transport operations agent",
    version="1.0.0 (REST API)",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and common dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middlewares (auth, error handling)
add_middlewares(app)

# Include API routers
app.include_router(routes.router, prefix="/api/routes", tags=["Routes & Entities"])
app.include_router(actions.router, prefix="/api/actions", tags=["Trip Actions"])
app.include_router(context.router, prefix="/api/context", tags=["UI Context"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit Logs"])
app.include_router(health.router, prefix="/api/health", tags=["Health & Status"])

# Include debug router (from Day 3)
app.include_router(debug.router)


@app.get("/")
async def root():
    """
    Root endpoint.
    Provides basic API information and available endpoints.
    """
    return {
        "message": "MOVI Backend API is running successfully",
        "version": "1.0.0",
        "api_docs": "/docs",
        "endpoints": {
            "routes": "/api/routes",
            "actions": "/api/actions",
            "context": "/api/context",
            "audit": "/api/audit",
            "health": "/api/health",
            "debug": "/api/debug"
        }
    }


@app.get("/health")
async def health():
    """
    Health check endpoint (legacy from Day 1).
    For detailed health info, use /api/health/status
    """
    return {
        "status": "ok",
        "service": "movi-backend",
        "layer": "rest-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
    }


@app.get("/")
async def root():
    """
    Root endpoint.
    Provides basic API information and available endpoints.
    """
    return {
        "message": "Welcome to Movi API",
        "docs": "/docs",
        "health": "/health",
        "description": "Multimodal Transport Agent for MoveInSync Shuttle",
    }


# TODO: Include routers once implemented
# app.include_router(stops.router, prefix="/api/stops", tags=["stops"])
# app.include_router(paths.router, prefix="/api/paths", tags=["paths"])
# app.include_router(routes.router, prefix="/api/routes", tags=["routes"])
# app.include_router(trips.router, prefix="/api/trips", tags=["trips"])
# app.include_router(vehicles.router, prefix="/api/vehicles", tags=["vehicles"])
# app.include_router(drivers.router, prefix="/api/drivers", tags=["drivers"])

# TODO: Add LangGraph agent endpoints (Day 3+)
# app.include_router(agent.router, prefix="/api/agent", tags=["agent"])

