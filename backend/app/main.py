"""
Movi Backend - FastAPI Application
Main entry point for the transport management API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# TODO: Import routers once created (Day 2+)
# from app.routers import stops, paths, routes, trips, vehicles, drivers

app = FastAPI(
    title="Movi - Multimodal Transport Agent API",
    description="Backend API for MoveInSync Shuttle transport management",
    version="0.1.0 (bootstrap)",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and common dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """
    Health check endpoint.
    Returns service status and basic metadata.
    """
    return {
        "status": "ok",
        "service": "movi-backend",
        "layer": "bootstrap",
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
