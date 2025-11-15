#!/usr/bin/env python3
"""
Create database tables for OneStopRadio
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import init_db, engine
from app.auth.models import User
from app.music.models import Track, Playlist
from app.streams.models import Stream

async def create_tables():
    """Create all database tables"""
    try:
        print("🔧 Creating database tables...")
        await init_db()
        print("✅ Database tables created successfully!")
        
        # Test database connection
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("✅ Database connection test successful!")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)