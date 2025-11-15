# backend/app/middleware.py
"""
Middleware for authentication, error handling, and request logging.
"""
import os
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment
API_KEY = os.getenv("MOVI_API_KEY", "dev-key-change-in-production")


async def verify_api_key(request: Request, call_next):
    """
    Verify API key for all /api endpoints (except health and docs).
    
    Exempt paths:
    - /docs, /redoc, /openapi.json (Swagger)
    - / (root)
    - Any path not starting with /api
    - OPTIONS requests (CORS preflight)
    """
    # Exempt OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Exempt paths
    exempt_paths = ["/", "/docs", "/redoc", "/openapi.json"]
    
    if request.url.path in exempt_paths or not request.url.path.startswith("/api"):
        return await call_next(request)
    
    # Check API key
    provided_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    
    if provided_key != API_KEY:
        logger.warning(f"Unauthorized access attempt to {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"ok": False, "error": "Unauthorized. Valid API key required."}
        )
    
    # Log request
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} duration={duration:.3f}s"
    )
    
    return response


def add_middlewares(app):
    """
    Add all middleware to the FastAPI app.
    """
    # API key verification middleware
    app.middleware("http")(verify_api_key)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_error_handler(request: Request, exc: Exception):
        """
        Catch all unhandled exceptions and return JSON error response.
        """
        logger.error(f"Unhandled exception in {request.url.path}: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "ok": False,
                "error": str(exc),
                "path": request.url.path
            }
        )
    
    # HTTP exception handler
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Handle FastAPI HTTPException with consistent JSON format.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "ok": False,
                "error": exc.detail,
                "path": request.url.path
            }
        )
