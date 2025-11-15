#!/usr/bin/env python3
"""
Simple database table creation script
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def create_tables():
    """Create all database tables"""
    try:
        from app.database import init_db
        print("🔧 Creating database tables...")
        await init_db()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)