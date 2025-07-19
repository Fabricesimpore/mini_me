# Troubleshooting Guide

## Frontend CSS Error

If you see a PostCSS error about `border-border` class:

### Solution:
The CSS has been fixed to use standard Tailwind classes. If you still see the error:

1. **Clear browser cache**: Hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
2. **Restart frontend**: `docker-compose restart frontend`
3. **Check logs**: `docker logs mini_me_frontend --tail 50`

## Common Issues

### 1. Blank Page
- Check browser console for errors (F12)
- Verify all services are running: `./test_platform.sh`
- Try accessing in incognito/private mode

### 2. Cannot Connect to Backend
- Ensure backend is running: `curl http://localhost:8000/health`
- Check CORS settings in backend
- Verify ports aren't blocked by firewall

### 3. Database Connection Issues
- Check PostgreSQL is running: `docker ps | grep postgres`
- Verify credentials in `.env` file
- Check database logs: `docker logs mini_me_postgres`

### 4. Celery Workers Not Starting
This is a known issue - the celery app import needs to be fixed. For now, the platform works without background tasks.

## Quick Fixes

### Restart Everything
```bash
docker-compose down
docker-compose up -d
```

### Rebuild Frontend
```bash
docker-compose build frontend
docker-compose up -d frontend
```

### Check All Logs
```bash
docker-compose logs -f
```

## Testing the Platform

Run the test script to verify everything is working:
```bash
./test_platform.sh
```

## Next Steps

1. Open http://localhost:3000 in your browser
2. Click "Create your Digital Twin" to register
3. Start exploring the dashboard
4. Check API docs at http://localhost:8000/docs