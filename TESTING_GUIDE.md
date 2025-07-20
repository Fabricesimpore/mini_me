# Digital Twin Platform - Testing Guide

## Prerequisites

1. **Backend Setup**
   ```bash
   cd backend
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your actual credentials:
   # - Database credentials
   # - JWT secret key
   # - Google OAuth credentials (for Gmail/Calendar)
   # - Todoist OAuth credentials
   # - OpenAI API key (optional)
   
   # Start PostgreSQL (if not running)
   # Make sure PostgreSQL is installed and running
   
   # Run migrations (database will be auto-created)
   python -m alembic upgrade head
   
   # Start backend server
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   ```

3. **Chrome Extension Setup**
   ```bash
   cd extension
   
   # Load in Chrome:
   # 1. Open chrome://extensions/
   # 2. Enable "Developer mode"
   # 3. Click "Load unpacked"
   # 4. Select the extension directory
   ```

## Testing Order

### 1. **Authentication & Basic Setup**
   - [ ] Register a new user account
   - [ ] Login with the created account
   - [ ] Verify dashboard loads correctly
   - [ ] Check that all navigation links work

### 2. **Cognitive Profile**
   - [ ] Navigate to Profile page
   - [ ] Complete the personality assessment
   - [ ] Verify cognitive profile is created
   - [ ] Check that traits are displayed correctly

### 3. **Memory System**
   - [ ] Navigate to Memory page
   - [ ] Create memories of different types (episodic, semantic, procedural, social)
   - [ ] Test memory search functionality
   - [ ] Verify semantic search works (search by meaning, not just keywords)

### 4. **Chat Interface**
   - [ ] Navigate to Chat page
   - [ ] Send various messages to your Digital Twin
   - [ ] Verify responses are contextual and personalized
   - [ ] Check that conversations are stored as memories

### 5. **Chrome Extension**
   - [ ] Click on the extension icon
   - [ ] Login through the extension popup
   - [ ] Enable tracking
   - [ ] Browse several websites
   - [ ] Check Behavioral Data page for tracked activities

### 6. **Gmail Integration**
   - [ ] Navigate to Integrations page
   - [ ] Click "Connect" on Gmail integration
   - [ ] Complete OAuth flow
   - [ ] Click "Analyze Emails"
   - [ ] Verify communication patterns are displayed

### 7. **Calendar Integration**
   - [ ] Click "Connect" on Google Calendar integration
   - [ ] Complete OAuth flow
   - [ ] Click "Analyze Calendar"
   - [ ] Verify calendar patterns are displayed
   - [ ] Check "Upcoming Events" functionality

### 8. **Todoist Integration**
   - [ ] Click "Connect" on Todoist integration
   - [ ] Complete OAuth flow
   - [ ] Click "Analyze Tasks"
   - [ ] Verify task patterns are displayed
   - [ ] Check "Today's Tasks" view

### 9. **Screen Observer**
   - [ ] Find Screen Activity Observer in Integrations
   - [ ] Click "Start" to begin capture
   - [ ] Work normally for a few minutes
   - [ ] Click "Analyze Now" to see current activity
   - [ ] Check activity breakdown and recommendations

### 10. **ML Models Training**
   - [ ] Navigate to Dashboard
   - [ ] Find ML Insights section
   - [ ] Click "Train All Models"
   - [ ] Wait for training to complete
   - [ ] Verify model status shows as trained
   - [ ] Click "Analyze Now" to see current behavior prediction

### 11. **Recommendations Engine**
   - [ ] Navigate to Recommendations page
   - [ ] Check "Daily" recommendations
   - [ ] Switch between different categories (Productivity, Communication, Wellness)
   - [ ] Click "Get Decision Support"
   - [ ] Fill in a decision type and description
   - [ ] Verify personalized decision framework is generated
   - [ ] Rate some recommendations using the star system

## Common Issues & Solutions

### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo service postgresql status  # Linux
brew services list  # macOS with Homebrew

# Create database manually if needed
createdb mini_me_db

# Check connection string in .env
DATABASE_URL=postgresql://username:password@localhost:5432/mini_me_db
```

### OAuth Issues
- Ensure redirect URLs match exactly in Google Console and code
- For Gmail/Calendar: http://localhost:8000/api/gmail/oauth-callback
- For Calendar: http://localhost:8000/api/calendar/oauth-callback
- For Todoist: http://localhost:8000/api/todoist/oauth-callback

### Chrome Extension Issues
- Check that backend URL in extension is correct (http://localhost:8000)
- Ensure you're logged in through the extension popup
- Check Chrome DevTools for any errors

### ML Model Training Issues
- Ensure you have sufficient data (100+ behaviors for behavioral model)
- Check Python dependencies, especially torch and transformers
- Monitor backend logs for training progress

### Screen Observer Issues
- On macOS: May need screen recording permissions
- On Windows: May need to run as administrator
- Linux: Ensure python3-tk is installed for GUI operations

## Testing Checklist

### Data Flow Verification
- [ ] Behavioral data from Chrome Extension appears in Behavioral Data page
- [ ] Chat messages create memories
- [ ] Gmail analysis updates communication style in cognitive profile
- [ ] Calendar analysis affects productivity recommendations
- [ ] Screen activity influences ML predictions
- [ ] Recommendations reflect actual user patterns

### Integration Tests
- [ ] All OAuth flows complete successfully
- [ ] Data from integrations appears in relevant sections
- [ ] Cognitive profile updates based on analyzed data
- [ ] ML models can be trained with collected data
- [ ] Recommendations are personalized based on profile

### Performance Tests
- [ ] Dashboard loads within 2 seconds
- [ ] Search returns results quickly
- [ ] Chat responses are generated promptly
- [ ] ML predictions complete in under 1 second
- [ ] Recommendations load without delay

## Backend API Testing

You can also test APIs directly using curl or Postman:

```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Use the returned token for authenticated requests
TOKEN="your-jwt-token-here"

# Get cognitive profile
curl http://localhost:8000/api/profile/cognitive \
  -H "Authorization: Bearer $TOKEN"

# Get recommendations
curl http://localhost:8000/api/recommendations/daily \
  -H "Authorization: Bearer $TOKEN"
```

## Monitoring Logs

Watch backend logs for any errors:
```bash
# Backend logs will show in the terminal where you ran uvicorn

# For more detailed logs, you can set logging level
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug
```

## Success Criteria

The system is working correctly when:
1. ✅ User can register, login, and navigate all pages
2. ✅ Cognitive profile reflects personality assessment
3. ✅ Memories are stored and searchable
4. ✅ Chat provides contextual responses
5. ✅ Behavioral data is tracked from browser
6. ✅ All integrations connect and analyze data
7. ✅ ML models train successfully
8. ✅ Recommendations are personalized and relevant
9. ✅ Decision support provides actionable frameworks
10. ✅ System learns and adapts from user feedback

## Next Steps After Testing

Once all components are verified:
1. Fine-tune ML model parameters
2. Adjust recommendation algorithms
3. Optimize performance bottlenecks
4. Add more integration options
5. Enhance UI/UX based on usage patterns