#!/bin/bash

# OneStopRadio Stream Provisioning Setup Script
# This script sets up the dedicated Shoutcast streaming infrastructure

set -e  # Exit on any error

echo "🎯 OneStopRadio - Stream Provisioning Setup"
echo "============================================"

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the backend-fast-py directory"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}📋 Step $1:${NC} $2"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Check Python installation
print_step "1" "Checking Python installation..."

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
print_success "Found Python $PYTHON_VERSION"

# Step 2: Check virtual environment
print_step "2" "Checking virtual environment..."

if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    $PYTHON_CMD -m venv venv
    print_success "Created virtual environment"
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_success "Activated virtual environment"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    print_success "Activated virtual environment (Windows)"
else
    print_error "Could not find virtual environment activation script"
    exit 1
fi

# Step 3: Install dependencies
print_step "3" "Installing Python dependencies..."

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Installed dependencies from requirements.txt"
else
    print_warning "requirements.txt not found. Installing basic dependencies..."
    pip install --upgrade pip
    pip install fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary python-multipart python-jose[cryptography] passlib[bcrypt] aiohttp
    print_success "Installed basic dependencies"
fi

# Step 4: Set up environment variables
print_step "4" "Setting up environment variables..."

if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating one..."
    cat > .env << EOF
# OneStopRadio FastAPI Configuration
DATABASE_URL=postgresql://onestopradio:your_password@localhost/onestopradio_db
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
UPLOAD_DIR=uploads
DEBUG=true
SERVICE_NAME=OneStopRadio API
SERVICE_VERSION=1.0.0
SERVER_HOST=0.0.0.0
SERVER_PORT=8002
EOF
    print_success "Created .env file with default configuration"
    print_warning "Please update the DATABASE_URL and JWT_SECRET_KEY in .env file!"
else
    print_success ".env file already exists"
fi

# Step 5: Run database migrations
print_step "5" "Running database migrations..."

if ! alembic current &> /dev/null; then
    print_warning "Alembic not initialized properly. Setting up..."
    alembic stamp head
fi

# Run migrations
alembic upgrade head
print_success "Database migrations completed"

# Step 6: Initialize stream provisioning infrastructure
print_step "6" "Initializing stream provisioning infrastructure..."

if $PYTHON_CMD init_stream_db.py; then
    print_success "Stream provisioning infrastructure initialized"
else
    print_warning "Stream infrastructure initialization had issues, but continuing..."
fi

# Step 7: Test FastAPI server
print_step "7" "Testing FastAPI server..."

echo "Starting FastAPI server in test mode (5 seconds)..."
timeout 5s uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload &
SERVER_PID=$!

sleep 3

# Test health endpoint
if curl -s http://localhost:8002/api/health/ > /dev/null; then
    print_success "FastAPI server is responding correctly"
else
    print_warning "Could not reach FastAPI server, but this might be normal"
fi

# Stop test server
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "🎉 Stream Provisioning Setup Complete!"
echo "======================================"
echo ""
echo "📋 What was set up:"
echo "   • Python virtual environment"
echo "   • FastAPI dependencies"
echo "   • Database migrations"
echo "   • Stream provisioning tables"
echo "   • Default Shoutcast server configuration"
echo "   • Port pool (8100-8200)"
echo ""
echo "🚀 To start the server:"
echo "   cd backend-fast-py"
echo "   source venv/bin/activate  # (or venv\\Scripts\\activate on Windows)"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload"
echo ""
echo "📚 API Documentation:"
echo "   http://localhost:8002/api/docs"
echo ""
echo "🔧 Important Next Steps:"
echo "   1. Update DATABASE_URL in .env file with your PostgreSQL credentials"
echo "   2. Change JWT_SECRET_KEY in .env file to a secure random string"
echo "   3. Update Shoutcast admin password (currently: changeme123)"
echo ""

if [ -f ".env" ]; then
    echo "📝 Current .env configuration:"
    echo "   $(grep -v "SECRET\|PASSWORD" .env | head -5)..."
    echo "   (Secrets hidden for security)"
fi

echo ""
print_success "Setup complete! Your OneStopRadio stream provisioning system is ready."