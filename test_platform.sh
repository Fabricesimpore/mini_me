#!/bin/bash

echo "🧪 Testing Digital Twin Platform"
echo "================================"

# Test Backend
echo -n "✓ Backend API: "
BACKEND_STATUS=$(curl -s http://localhost:8000/health 2>/dev/null)
if [[ $BACKEND_STATUS == *"healthy"* ]]; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

# Test Frontend
echo -n "✓ Frontend: "
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
if [[ $FRONTEND_STATUS == "200" ]]; then
    echo "✅ Running"
else
    echo "❌ Not responding (Status: $FRONTEND_STATUS)"
fi

# Test Database
echo -n "✓ PostgreSQL: "
PG_STATUS=$(docker exec mini_me_postgres pg_isready -U mini_me_user 2>/dev/null)
if [[ $PG_STATUS == *"accepting connections"* ]]; then
    echo "✅ Running"
else
    echo "❌ Not ready"
fi

# Test Redis
echo -n "✓ Redis: "
REDIS_STATUS=$(docker exec mini_me_redis redis-cli ping 2>/dev/null)
if [[ $REDIS_STATUS == "PONG" ]]; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

echo ""
echo "📍 Access Points:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo ""
echo "🚀 Your Digital Twin Platform is ready!"
echo "Open http://localhost:3000 in your browser to get started."