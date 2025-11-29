"""
Movi Backend - FastAPI Application
Main entry point for the transport management API
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager

# Load environment variables from .env file
load_dotenv()

# Import REST API routers
from app.api import routes, actions, context, audit, health, agent, agent_image, status

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
        
        # Start automatic trip status updater
        from app.core.status_updater import start_status_updater
        await start_status_updater()
        print("✅ Automatic trip status updater started")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize database pool: {e}")
        print("   Some endpoints may not work until DATABASE_URL is configured.")
    
    yield
    
    # Shutdown: Close database connection pool
    print("🛑 Shutting down Movi backend...")
    
    # Stop status updater
    from app.core.status_updater import stop_status_updater
    stop_status_updater()
    print("✅ Trip status updater stopped")
    
    await close_pool()
    print("✅ Database pool closed")


app = FastAPI(
    title="MOVI Backend API",
    description="Backend API for MOVI – the multimodal transport operations agent",
    version="1.0.0 (REST API)",
    lifespan=lifespan
)

# CORS middleware for frontend integration
# Get allowed origins from environment or use defaults
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
DEFAULT_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Common dev port
]
# Add any configured production origins
allowed_origins = DEFAULT_ORIGINS + [origin.strip() for origin in CORS_ORIGINS if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
app.include_router(status.router, prefix="/api/status", tags=["Trip Status Management"])

# Include resources router (Drivers & Vehicles with dynamic availability)
from app.api import resources
app.include_router(resources.router, prefix="/api", tags=["Resources - Drivers & Vehicles"])

# Include agent router (Day 7: LangGraph)
app.include_router(agent.router, prefix="/api/agent", tags=["AI Agent"])

# Include agent image router (Day 10: OCR)
app.include_router(agent_image.router, prefix="/api", tags=["AI Agent - Image"])

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
            "status": "/api/status",
            "agent": "/api/agent",
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

