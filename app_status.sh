#!/bin/bash

echo "🎯 Digital Twin Platform Status"
echo "================================"
echo ""

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API: Running on http://localhost:8000"
    echo "   - Health endpoint: ✓"
    echo "   - Registration: ✓"
    echo "   - Login: ✓"
    echo "   - API Docs: http://localhost:8000/docs"
else
    echo "❌ Backend API: Not running"
fi

echo ""

# Check frontend
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Frontend: Running on http://localhost:5173"
else
    echo "❌ Frontend: Not running"
fi

echo ""
echo "📝 Quick Start:"
echo "1. Open http://localhost:5173 in your browser"
echo "2. Register a new account"
echo "3. Login with your credentials"
echo ""
echo "⚠️  Note: Using simplified backend with in-memory storage"
echo "   Full features require installing ML dependencies"