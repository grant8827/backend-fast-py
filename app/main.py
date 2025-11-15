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
from .audio.router import router as audio_router
from .streams.routes import router as streams_router
from .stream_provisioning.routes import router as stream_provisioning_router

# Import models to register them with SQLAlchemy
from .auth.models import User
from .music.models import Track, Playlist
from .streams.models import Stream
from .stream_provisioning_models import DedicatedStream, StreamCredentials

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
app.include_router(audio_router)
app.include_router(streams_router)
app.include_router(stream_provisioning_router)

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
    """Initialize database on startup"""
    try:
        await init_db()
        print(f"✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
    
    print(f"🚀 {settings.service_name} v{settings.service_version} started!")
    print(f"📚 API Documentation: http://{settings.server_host}:{settings.server_port}/api/docs")

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