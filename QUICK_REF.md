# Quick Reference Guide

## 🚀 Start Development in 3 Steps

### Option A: Docker (Recommended)
```bash
cd /path/to/indu\ 2.0

# Copy and configure environment
cp .env.example .env
# Edit .env and add SARVAM_API_KEY

# Start everything
docker-compose up -d

# Access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Option B: Local Development

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Backend running on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
# Frontend running on http://localhost:3000
```

**Terminal 3 - Redis:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Terminal 4 - PostgreSQL:**
```bash
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=conversational_ai \
  postgres:16-alpine
```

---

## 📱 Testing the Application

1. Open http://localhost:3000 in Chrome/Firefox
2. Allow microphone access when prompted
3. Click the microphone button (🎤)
4. Start speaking
5. See your microphone level in real-time
6. Change language and personality settings
7. Click stop (⏹️) to stop recording

---

## 🔌 WebSocket Events

### Send to Server
```javascript
// Start session
{
  "event": "start_session",
  "language": "en",
  "personality": "assistant"
}

// Send audio
{
  "event": "audio_chunk",
  "data": "base64-encoded-audio",
  "sequence": 0
}

// Stop audio
{
  "event": "stop_audio"
}

// Interrupt AI
{
  "event": "interrupt"
}

// Keep alive
{
  "event": "ping"
}
```

### Receive from Server
```javascript
{
  "event": "session_started",
  "session_id": "session_xxx",
  "timestamp": "2026-05-11T..."
}

{
  "event": "audio_received",
  "sequence": 0
}

{
  "event": "transcription",
  "text": "Hello world",
  "is_final": false
}

{
  "event": "error",
  "message": "Error description"
}
```

---

## 🛠️ Useful Commands

### Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Single service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Backend Development
```bash
# Activate venv (Windows)
venv\Scripts\activate

# Activate venv (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn app.main:app --reload

# Run on specific port
uvicorn app.main:app --port 8001

# Generate requirements
pip freeze > requirements.txt
```

### Frontend Development
```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Install new package
npm install package-name
```

### Database
```bash
# Access PostgreSQL
psql -h localhost -U user -d conversational_ai

# Access Redis CLI
redis-cli -h localhost -p 6379

# Check Redis
redis-cli PING
# Returns: PONG

# View Redis keys
redis-cli KEYS *
```

---

## 📊 Project Structure Overview

```
indu 2.0/
├── backend/              # FastAPI + WebSocket
├── frontend/            # React + Tailwind
├── docker-compose.yml   # Orchestration
├── .env.example        # Configuration template
├── README.md           # Full documentation
├── PHASE_1_COMPLETE.md # Phase 1 summary
└── QUICK_REF.md        # This file
```

---

## 🔗 Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React app |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health Check | http://localhost:8000/health | Server status |
| PgAdmin | http://localhost:5050 | Database UI |
| Redis | localhost:6379 | Cache/queue |
| PostgreSQL | localhost:5432 | Database |

---

## 🔑 Environment Variables

### Critical for Running
```env
SARVAM_API_KEY=your-key-here
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:password@localhost:5432/conversational_ai
```

### Optional
```env
DEBUG=true              # Enable debug mode
LOG_LEVEL=INFO         # Logging level
RELOAD=true            # Auto-reload on code changes
```

---

## 🐛 Common Issues & Fixes

### Port Already in Use
```bash
# Find process using port 3000
lsof -i :3000
kill -9 <PID>

# Or use different port
npm run dev -- --port 3001
```

### WebSocket Connection Failed
```bash
# Check backend is running
curl http://localhost:8000/health

# Check logs
docker-compose logs backend
```

### Microphone Permission
- Reload page and click "Allow"
- Use HTTPS for production (some browsers require it)
- Check browser privacy settings

### Database Connection Error
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check connection
psql -h localhost -U user -d conversational_ai
```

### Redis Connection Error
```bash
# Restart Redis
docker-compose restart redis

# Test connection
redis-cli ping
```

---

## 📈 Performance Tips

1. **Frontend**
   - Enable Production builds: `npm run build`
   - Minimize re-renders using React.memo
   - Lazy load components

2. **Backend**
   - Use async functions everywhere
   - Enable WebSocket compression
   - Optimize database queries

3. **Docker**
   - Use `.dockerignore` to exclude files
   - Multi-stage builds for frontend
   - Pin dependency versions

---

## 🔐 Security Reminders

- ❌ Never commit `.env` file
- ❌ Never log sensitive data
- ❌ Never expose API keys in frontend
- ✅ Use environment variables
- ✅ Validate all inputs
- ✅ Use HTTPS in production
- ✅ Enable CORS for production domains

---

## 📚 Key Files

### Backend Entry Points
- `app/main.py` - FastAPI app
- `app/config.py` - Settings
- `app/websocket/manager.py` - WebSocket logic

### Frontend Entry Points
- `src/App.jsx` - Main component
- `src/services/websocket.js` - WebSocket client
- `src/store/conversationStore.js` - State

### Configuration
- `.env.example` - Environment template
- `docker-compose.yml` - Docker setup
- `tailwind.config.js` - Tailwind theme

---

## 🎯 Next Steps

1. ✅ **PHASE 1**: Setup complete
2. 📋 **PHASE 2**: Audio streaming (implement next)
3. 🔄 **PHASE 3-9**: Refer to README.md

---

## 💬 Quick Help

### Need to debug WebSocket?
```javascript
// In browser console
ws.addEventListener('message', (e) => console.log('WS:', e.data))
```

### Need to test API?
```bash
# Test health endpoint
curl http://localhost:8000/health

# Use Swagger UI
http://localhost:8000/docs
```

### Need to check Redis?
```bash
redis-cli
# List all keys
keys *
# Check specific key
get session_123
```

---

## 🚀 Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Set strong database password
- [ ] Update CORS origins
- [ ] Use HTTPS
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Test disaster recovery
- [ ] Set up CI/CD
- [ ] Document deployment

---

**Last Updated**: 2026-05-11
**PHASE**: 1 Complete ✅
**Status**: Ready for Development
