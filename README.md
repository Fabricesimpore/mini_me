# Digital Twin Platform

A platform that creates a true digital twin of you - an AI that thinks, acts, and behaves exactly like you do.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- Git

### Option 1: Docker Compose (Recommended)
```bash
# Clone the repository
git clone <your-repo-url>
cd Mini_me

# Start all services
docker-compose up

# Access the platform
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development
```bash
# Start database services
docker-compose up -d postgres redis

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

### Option 3: Use the start script
```bash
chmod +x start_local.sh
./start_local.sh
```

## 📁 Project Structure
```
Mini_me/
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   ├── core/               # Core functionality
│   ├── collectors/         # Data collectors
│   ├── memory/             # Memory systems
│   ├── learning/           # ML models
│   └── integrations/       # External services
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── store/          # State management
├── extension/              # Browser extension
├── ml_models/              # Trained models
└── infrastructure/         # Docker & DB configs
```

## 🧪 Testing

### Run code verification
```bash
python3 test_code.py
```

### Run setup test
```bash
python3 test_setup.py
```

## 🔧 Development

### Backend Development
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Database Access
```bash
# Connect to PostgreSQL
docker exec -it mini_me_postgres psql -U mini_me_user -d mini_me_db

# Connect to Redis
docker exec -it mini_me_redis redis-cli
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🐛 Troubleshooting

### Docker issues
```bash
# Reset everything
docker-compose down -v
docker-compose up --build
```

### Port conflicts
- Backend runs on port 8000
- Frontend runs on port 3000
- PostgreSQL runs on port 5432
- Redis runs on port 6379

### Dependencies issues
```bash
# Backend
cd backend && pip install --upgrade -r requirements.txt

# Frontend
cd frontend && rm -rf node_modules package-lock.json && npm install
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.