#!/bin/bash

# OneStopRadio FastAPI Server Startup Script
echo "🚀 Starting OneStopRadio FastAPI Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Running setup..."
    ./setup.sh
fi

# Activate virtual environment
source venv/bin/activate

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API Docs available at http://localhost:8000/api/docs"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

python run_server.py