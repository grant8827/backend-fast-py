#!/bin/bash

# OneStopRadio Database Migration Script
echo "🗄️ Setting up OneStopRadio Database Migrations"
echo "=============================================="

# Navigate to backend directory
cd "/Users/gregorygrant/Desktop/Websites/mutiple backend projects/onestopradio/backend-fast-py"

# Activate virtual environment
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    echo "✅ Activated virtual environment"
else
    echo "❌ Virtual environment not found. Please run setup_postgresql.sh first"
    exit 1
fi

# Install required packages
echo "📦 Installing required packages..."
pip install -q alembic asyncpg psycopg2-binary

# Create initial migration
echo "🔄 Creating initial database migration..."
alembic revision --autogenerate -m "Initial migration - OneStopRadio DJ Platform"

# Run the migration
echo "⬆️ Running database migration..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migration completed successfully!"
    
    # Show created tables
    echo ""
    echo "📋 Created database tables:"
    python -c "
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

async def show_tables():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        if 'postgresql' in settings.database_url:
            result = await conn.execute(\"SELECT tablename FROM pg_tables WHERE schemaname = 'public'\")
        else:
            result = await conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
        
        tables = [row[0] for row in result.fetchall()]
        for table in sorted(tables):
            print(f'  📊 {table}')
    
    await engine.dispose()

asyncio.run(show_tables())
"
    
    echo ""
    echo "🎉 Database setup completed!"
    echo "Ready to run your OneStopRadio FastAPI application!"
    
else
    echo "❌ Database migration failed. Please check the error messages above."
    exit 1
fi