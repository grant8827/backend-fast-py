#!/usr/bin/env python3
"""
Railway Database Reset Script
Use this to reset the database schema if there are migration conflicts
"""

import asyncio
import sys
from app.config import settings
from app.database import engine

async def reset_database():
    """Drop all tables and reset the database"""
    if not "postgresql" in settings.database_url or settings.environment != "production":
        print("❌ This script only works with PostgreSQL in production")
        return False
    
    try:
        print("⚠️ WARNING: This will DROP ALL TABLES in the database!")
        print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'Unknown'}")
        
        # In Railway, this script would be run manually if needed
        async with engine.begin() as conn:
            # Get all table names
            result = await conn.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """)
            tables = result.fetchall()
            
            if tables:
                print(f"Found {len(tables)} tables to drop:")
                for table in tables:
                    print(f"  - {table[0]}")
                
                # Drop all tables
                table_names = [table[0] for table in tables]
                if table_names:
                    drop_sql = f"DROP TABLE IF EXISTS {', '.join(table_names)} CASCADE"
                    await conn.execute(drop_sql)
                    print("✅ All tables dropped")
                
                # Drop alembic version table if it exists
                await conn.execute("DROP TABLE IF EXISTS alembic_version CASCADE")
                print("✅ Alembic version table dropped")
            else:
                print("ℹ️ No tables found to drop")
        
        print("✅ Database reset complete")
        print("💡 Now run: alembic upgrade head")
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        return False

if __name__ == "__main__":
    print("🗄️ Railway Database Reset Tool")
    success = asyncio.run(reset_database())
    sys.exit(0 if success else 1)