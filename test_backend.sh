#!/bin/bash

echo "🧪 Testing Digital Twin Backend"

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing minimal dependencies for testing..."
    pip install fastapi uvicorn sqlalchemy asyncpg python-dotenv
    cd ..
else
    echo "✓ Virtual environment exists"
    cd backend
    source venv/bin/activate
    cd ..
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec mini_me_postgres pg_isready -U mini_me_user > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo " Ready!"

# Start backend
echo "🚀 Starting backend server..."
cd backend
python main.py