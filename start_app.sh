#!/bin/bash

# Digital Twin Platform - Start Script

echo "🚀 Starting Digital Twin Platform..."
echo "===================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to open new terminal tab (macOS)
open_new_tab() {
    osascript -e "tell application \"Terminal\" to do script \"cd $(pwd) && $1\""
}

# Check if we're in the right directory
if [ ! -f "backend/main.py" ] || [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the Mini_me root directory"
    exit 1
fi

echo -e "\n${BLUE}Starting Backend Server...${NC}"
echo "Opening in new terminal tab..."
open_new_tab "cd backend && source venv/bin/activate && echo '🔧 Backend Server Starting...' && echo '================================' && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

# Wait a bit for backend to start
sleep 3

echo -e "\n${BLUE}Starting Frontend Server...${NC}"
echo "Opening in new terminal tab..."
open_new_tab "cd frontend && echo '🎨 Frontend Server Starting...' && echo '================================' && npm run dev"

echo -e "\n${GREEN}✅ Servers are starting!${NC}"
echo -e "\n${YELLOW}Access points:${NC}"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Chrome Extension:${NC}"
echo "1. Open chrome://extensions/"
echo "2. Enable 'Developer mode'"
echo "3. Click 'Load unpacked' and select the 'extension' folder"
echo ""
echo -e "${GREEN}🎉 Happy testing!${NC}"
echo ""
echo "To stop the servers, close the terminal tabs or press Ctrl+C in each."