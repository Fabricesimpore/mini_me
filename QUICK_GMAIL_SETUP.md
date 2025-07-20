# Quick Gmail Integration Setup

## Current Status
✅ Chat is now using OpenAI for intelligent responses
✅ Gmail OAuth code is ready
❌ Google OAuth credentials needed for real Gmail connection

## To Connect Real Gmail (5 minutes)

### 1. Get Google Credentials
1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search "Gmail API" and Enable it

### 2. Create OAuth Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure consent screen:
   - Choose "External"
   - Add app name: "Digital Twin Platform"
   - Add your email as test user
4. For OAuth client:
   - Type: Web application
   - Authorized redirect URIs: `http://localhost:8000/api/gmail/callback`
5. Download credentials

### 3. Add to Your App
1. Open the downloaded JSON file
2. Copy the client_id and client_secret
3. Edit `/backend/.env`:
```env
GOOGLE_CLIENT_ID=your-actual-client-id
GOOGLE_CLIENT_SECRET=your-actual-client-secret
```

### 4. Test It!
1. The backend will auto-reload
2. Go to Integrations page
3. Click "Connect Gmail"
4. Authorize in popup
5. Your real emails will be analyzed!

## What You Get
- 📊 Real email statistics
- 👥 Top sender analysis
- 📈 Communication patterns
- 🤖 AI insights about your email habits
- 🔍 All data stays local - nothing sent to third parties

## Alternative: Keep Demo Mode
If you don't want to set up OAuth yet, the app works great with simulated data!
Just click "Connect Gmail" without credentials for demo mode.