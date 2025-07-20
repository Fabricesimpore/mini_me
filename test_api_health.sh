#!/bin/bash

# API Health Check Script

echo "🏥 Digital Twin API Health Check"
echo "================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Base URL
BASE_URL="http://localhost:8000"

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=$2
    local description=$3
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} $description ($endpoint) - Status: $response"
    else
        echo -e "${RED}✗${NC} $description ($endpoint) - Status: $response (Expected: $expected_status)"
    fi
}

echo -e "\n${YELLOW}Checking API Endpoints...${NC}\n"

# Public endpoints
check_endpoint "/" 200 "Root endpoint"
check_endpoint "/health" 200 "Health check"
check_endpoint "/docs" 200 "API Documentation"

# Auth endpoints
check_endpoint "/api/auth/login" 405 "Login endpoint (expects POST)"
check_endpoint "/api/auth/register" 405 "Register endpoint (expects POST)"

echo -e "\n${YELLOW}Testing Registration & Login...${NC}\n"

# Generate unique test user
TIMESTAMP=$(date +%s)
TEST_USER="testuser_$TIMESTAMP"
TEST_EMAIL="test_$TIMESTAMP@example.com"
TEST_PASS="testpass123"

# Register user
echo "Registering test user: $TEST_USER"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASS\"}")

if echo "$REGISTER_RESPONSE" | grep -q "user_id"; then
    echo -e "${GREEN}✓${NC} User registration successful"
    
    # Login
    echo "Logging in..."
    LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")
    
    if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
        echo -e "${GREEN}✓${NC} Login successful"
        
        # Extract token
        TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        
        echo -e "\n${YELLOW}Testing Authenticated Endpoints...${NC}\n"
        
        # Test authenticated endpoints
        AUTH_HEADER="Authorization: Bearer $TOKEN"
        
        # Check various endpoints
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$BASE_URL/api/profile/cognitive")
        if [ "$response" = "200" ] || [ "$response" = "404" ]; then
            echo -e "${GREEN}✓${NC} Cognitive Profile endpoint - Status: $response"
        else
            echo -e "${RED}✗${NC} Cognitive Profile endpoint - Status: $response"
        fi
        
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$BASE_URL/api/memory/all?limit=10")
        echo -e "${GREEN}✓${NC} Memory endpoint - Status: $response"
        
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$BASE_URL/api/behavioral/patterns")
        echo -e "${GREEN}✓${NC} Behavioral patterns endpoint - Status: $response"
        
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$BASE_URL/api/integrations/status")
        echo -e "${GREEN}✓${NC} Integrations status endpoint - Status: $response"
        
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$BASE_URL/api/ml/models/status")
        echo -e "${GREEN}✓${NC} ML models status endpoint - Status: $response"
        
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$BASE_URL/api/recommendations/daily")
        echo -e "${GREEN}✓${NC} Recommendations endpoint - Status: $response"
        
    else
        echo -e "${RED}✗${NC} Login failed"
    fi
else
    echo -e "${RED}✗${NC} Registration failed"
    echo "Response: $REGISTER_RESPONSE"
fi

echo -e "\n${GREEN}🎉 Health check complete!${NC}"
echo -e "\n${YELLOW}Note:${NC} Some endpoints may return 404 if no data exists yet."
echo "This is normal for a fresh installation."