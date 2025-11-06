#!/usr/bin/env python3
"""
Railway-optimized startup script for OneStopRadio FastAPI
"""

import os
import sys
import asyncio
import subprocess
import uvicorn
from app.config import settings

async def run_migrations():
    """Run database migrations on startup (Railway production only)"""
    if settings.environment == "production" and "postgresql" in settings.database_url:
        try:
            print("🗄️ Running database migrations...")
            
            # First, check if we need to reset the database
            result = subprocess.run(["alembic", "current"], 
                                 capture_output=True, text=True)
            
            # Try to run upgrade
            result = subprocess.run(["alembic", "upgrade", "head"], 
                                 capture_output=True, text=True, check=True)
            print("✅ Database migrations completed")
            print(f"Migration output: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Migration failed: {e}")
            print(f"Output: {e.stdout}")
            print(f"Error: {e.stderr}")
            
            # If migration fails due to schema conflicts, suggest manual intervention
            if "cannot be implemented" in e.stderr or "incompatible types" in e.stderr:
                print("💡 Schema conflict detected. This may require database reset.")
                print("💡 In Railway dashboard, you can reset the database and redeploy.")
            
            return False
        except FileNotFoundError:
            print("⚠️ Alembic not found, skipping migrations")
            return True
    else:
        print("ℹ️ Skipping migrations (development or SQLite)")
        return True

async def verify_database_connection():
    """Verify database connection without creating tables"""
    try:
        from app.database import engine
        async with engine.begin() as conn:
            # Simple connection test
            await conn.execute("SELECT 1")
        print("✅ Database connection verified")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # Railway sets PORT environment variable
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting OneStopRadio FastAPI on port {port}")
    print(f"🌍 Environment: {settings.environment}")
    print(f"🗄️ Database: {'PostgreSQL' if 'postgresql' in settings.database_url else 'SQLite'}")
    
    # Run startup tasks
    startup_success = True
    
    # Run migrations (production only)
    if not asyncio.run(run_migrations()):
        print("❌ Failed to run migrations")
        startup_success = False
    
    # Verify database connection
    if not asyncio.run(verify_database_connection()):
        print("❌ Failed to connect to database")
        startup_success = False
    
    if not startup_success:
        print("❌ Startup failed - exiting")
        sys.exit(1)
    
    # Production-optimized Uvicorn settings
    uvicorn_config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": port,
        "workers": int(os.getenv("WEB_CONCURRENCY", "1")),
        "log_level": os.getenv("LOG_LEVEL", "info"),
        "access_log": True,
        "use_colors": True,
        "reload": settings.debug
    }
    
    print(f"� Workers: {uvicorn_config['workers']}")
    print("� All systems ready - starting server...")
    
    uvicorn.run(**uvicorn_config)