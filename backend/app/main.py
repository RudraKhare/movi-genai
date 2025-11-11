"""
Movi Backend - FastAPI Application
Main entry point for the transport management API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager

# Import routers
from app.routers import debug

# Import DB initialization
from app.core.supabase_client import init_db_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes DB pool on startup and closes it on shutdown.
    """
    # Startup: Initialize database connection pool
    print("🚀 Starting Movi backend...")
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
    title="Movi - Multimodal Transport Agent API",
    description="Backend API for MoveInSync Shuttle transport management",
    version="0.2.0 (core-tools)",
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

# Include routers
app.include_router(debug.router)


@app.get("/health")
async def health():
    """
    Health check endpoint.
    Returns service status and basic metadata.
    """
    return {
        "status": "ok",
        "service": "movi-backend",
        "layer": "core-tools",
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
