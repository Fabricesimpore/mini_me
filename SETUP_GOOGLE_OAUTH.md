# Setting Up Google OAuth for Real Integrations

To enable real Gmail and Google Calendar integrations, you need to set up OAuth2 credentials.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Gmail API
   - Google Calendar API

## Step 2: Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - Choose "External" for user type
   - Fill in app information
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.compose`
     - `https://www.googleapis.com/auth/gmail.modify`
     - `https://www.googleapis.com/auth/calendar.readonly`
   - Add test users (your email)

4. Create OAuth client ID:
   - Application type: Web application
   - Name: Digital Twin Platform
   - Authorized JavaScript origins:
     - `http://localhost:3000`
     - `http://localhost:5173`
   - Authorized redirect URIs:
     - `http://localhost:8000/api/gmail/callback`
     - `http://localhost:8000/api/calendar/callback`

5. Download the credentials JSON

## Step 3: Configure Your App

1. Add to your `.env` file:
```env
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

2. Install required packages:
```bash
cd backend
source venv/bin/activate
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Step 4: Test the Integration

1. Restart your backend
2. Go to Integrations page
3. Click "Connect Gmail"
4. Authorize in the popup window
5. Your emails will be accessible!

## Features Available with Real Integration

- **Email Analysis**: Analyze communication patterns
- **Contact Extraction**: Build a network graph
- **Priority Detection**: Identify important emails
- **Search Integration**: Search across all emails
- **Calendar Sync**: See all your events
- **Meeting Analysis**: Understand meeting patterns
- **Time Blocking**: Optimize your schedule

## Privacy & Security

- All data stays on your local machine
- OAuth tokens are stored securely
- You can revoke access anytime from Google Account settings
- No data is sent to third parties

## Troubleshooting

1. **"Invalid client" error**: Check your client ID and secret
2. **Redirect URI mismatch**: Ensure redirect URIs match exactly
3. **Scope error**: Make sure all required scopes are enabled
4. **Rate limits**: Google APIs have quotas, use pagination

## Alternative: Continue with Demo Mode

If you don't want to set up OAuth yet, the app works perfectly in demo mode with simulated data!