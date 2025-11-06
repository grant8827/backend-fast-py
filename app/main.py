"""
FastAPI Main Application
OneStopRadio DJ Platform API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from .config import settings
from .database import init_db
from .auth.router import router as auth_router
from .stations.router import router as stations_router
from .music.router import router as music_router

# Create FastAPI app
app = FastAPI(
    title="OneStopRadio API",
    description="DJ Platform API for authentication, station management, and streaming",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
if os.path.exists(settings.upload_dir):
    app.mount("/static", StaticFiles(directory=settings.upload_dir), name="static")

# Include routers
app.include_router(auth_router)
app.include_router(stations_router)
app.include_router(music_router)

# Health check endpoint
@app.get("/api/health/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "OneStopRadio FastAPI Backend",
        "version": settings.service_version,
        "docs": "/api/docs",
        "health": "/api/health/"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup - using Alembic migrations instead of create_all"""
    # In production, use Alembic migrations instead of create_all to avoid schema conflicts
    # await init_db()  # Disabled - use alembic upgrade head instead
    print(f"🚀 {settings.service_name} v{settings.service_version} started!")
    print(f"📚 API Documentation: http://{settings.server_host}:{settings.server_port}/api/docs")
    print("💡 Note: Make sure to run 'alembic upgrade head' to apply database migrations")

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    if settings.debug:
        import traceback
        print(f"❌ Unhandled exception: {exc}")
        traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "detail": "Internal server error",
            "error": str(exc) if settings.debug else "Something went wrong"
        }
    )