# Authentication Testing Guide

## Current Status
- Backend API: Running on http://localhost:8000
- Frontend: Running on http://localhost:5173
- Authentication: Working with URLSearchParams for form-urlencoded data

## Test Credentials
You can register a new account or use these test accounts:
- Email: demo@example.com, Password: demo123
- Email: demo2@example.com, Password: demo123

## How to Test

### 1. Registration
1. Go to http://localhost:5173/register
2. Enter:
   - Email: your-email@example.com
   - Username: yourusername
   - Password: yourpassword
   - Confirm Password: yourpassword
3. Click "Create Digital Twin"
4. You should be automatically logged in and redirected to the dashboard

### 2. Login
1. Go to http://localhost:5173/login
2. Enter:
   - Email: your-email@example.com
   - Password: yourpassword
3. Click "Sign in"
4. You should be logged in and redirected to the dashboard

## Troubleshooting

### If login fails:
1. Check browser console for errors (F12 -> Console)
2. Check network tab for the /api/auth/token request
3. Verify the request is sending as application/x-www-form-urlencoded
4. Check backend logs: `tail -f backend/backend_simple.log`

### Common Issues:
- **401 Unauthorized**: The email/password is incorrect or user doesn't exist
- **CORS errors**: Make sure both frontend and backend are running
- **Network errors**: Verify backend is running on port 8000

## API Endpoints
- Register: POST http://localhost:8000/api/auth/register
- Login: POST http://localhost:8000/api/auth/token
- Get Current User: GET http://localhost:8000/api/auth/me (requires auth token)

## Notes
- The backend uses in-memory storage, so users are lost on restart
- The frontend auto-logs in after registration using the email address
- OAuth2PasswordRequestForm expects 'username' field but we use email as username