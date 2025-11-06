#!/bin/bash

# OneStopRadio FastAPI Backend Setup Script
echo "🎵 Setting up OneStopRadio FastAPI Backend..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "🐍 Using Python $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create upload directory
echo "📁 Creating upload directories..."
mkdir -p static/uploads/logos
mkdir -p static/uploads/covers
mkdir -p static/uploads/avatars

# Initialize database (create tables)
echo "🗄️ Initializing database..."
python3 -c "
import asyncio
import sys
import os
sys.path.append('.')
from app.database import init_db
asyncio.run(init_db())
print('✅ Database initialized successfully')
"

echo ""
echo "🚀 FastAPI Backend Setup Complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"  
echo "  python run_server.py"
echo ""
echo "Or run directly:"
echo "  ./start_server.sh"
echo ""
echo "API Documentation will be available at:"
echo "  http://localhost:8000/api/docs"