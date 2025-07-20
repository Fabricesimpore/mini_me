#!/bin/bash

# Digital Twin Platform - Quick Setup Script for Testing

echo "🚀 Digital Twin Platform - Test Environment Setup"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if PostgreSQL is installed
echo -e "\n${YELLOW}Checking PostgreSQL...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is installed${NC}"
    
    # Check if PostgreSQL is running
    if pg_isready &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL is running${NC}"
    else
        echo -e "${RED}✗ PostgreSQL is not running. Please start it:${NC}"
        echo "  macOS: brew services start postgresql"
        echo "  Linux: sudo service postgresql start"
        exit 1
    fi
else
    echo -e "${RED}✗ PostgreSQL is not installed${NC}"
    echo "Please install PostgreSQL first:"
    echo "  macOS: brew install postgresql"
    echo "  Linux: sudo apt-get install postgresql"
    exit 1
fi

# Check Python version
echo -e "\n${YELLOW}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION is installed${NC}"
else
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

# Check Node.js
echo -e "\n${YELLOW}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION is installed${NC}"
else
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

# Backend setup
echo -e "\n${YELLOW}Setting up Backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit backend/.env with your credentials${NC}"
fi

# Create database
echo -e "\n${YELLOW}Setting up Database...${NC}"
createdb mini_me_db 2>/dev/null || echo "Database already exists"

# Run migrations
echo "Running database migrations..."
python -m alembic upgrade head

echo -e "${GREEN}✓ Backend setup complete${NC}"

# Frontend setup
echo -e "\n${YELLOW}Setting up Frontend...${NC}"
cd ../frontend

# Install npm dependencies
echo "Installing npm dependencies..."
npm install

echo -e "${GREEN}✓ Frontend setup complete${NC}"

# Extension setup reminder
echo -e "\n${YELLOW}Chrome Extension Setup:${NC}"
echo "1. Open Chrome and go to chrome://extensions/"
echo "2. Enable 'Developer mode'"
echo "3. Click 'Load unpacked'"
echo "4. Select the 'extension' directory"

# Final instructions
echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo -e "\n${YELLOW}To start testing:${NC}"
echo "1. Terminal 1 - Start Backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn main:app --reload"
echo ""
echo "2. Terminal 2 - Start Frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open http://localhost:5173 in your browser"
echo ""
echo -e "${YELLOW}⚠️  Don't forget to:${NC}"
echo "- Edit backend/.env with your API credentials"
echo "- Set up OAuth credentials for Google services"
echo "- Install Tesseract for screen capture OCR (optional)"
echo "  macOS: brew install tesseract"
echo "  Linux: sudo apt-get install tesseract-ocr"