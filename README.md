# 🎤 Conversational AI Agent

A production-ready, full-duplex real-time conversational voice AI system optimized for the Indian market using Sarvam AI.

## 🌟 Features (PHASE 1)

✅ FastAPI Backend with WebSocket Support
✅ React + Tailwind Frontend with Modern UI
✅ Real-time WebSocket Communication
✅ Microphone Audio Capture
✅ Language Selection (English, Hindi, Hinglish, Telugu)
✅ AI Personality System
✅ Connection Status Management
✅ Docker Compose Setup
✅ Production-ready Architecture

## 📋 Requirements

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Modern Web Browser (Chrome, Firefox, Safari, Edge)
- Microphone Access

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone/navigate to project
cd /path/to/indu\ 2.0

# Copy environment file
cp .env.example .env

# Update Sarvam API Key in .env
nano .env
# or
vim .env

# Build and start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# PgAdmin: http://localhost:5050
```

### Option 2: Local Development

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env

# Update API keys in .env

# Start Redis (required)
# Install Redis or use Docker:
docker run -d -p 6379:6379 redis:7-alpine

# Start PostgreSQL (required)
# Install PostgreSQL or use Docker:
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=conversational_ai \
  postgres:16-alpine

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Start development server
npm run dev

# Access at http://localhost:3000
```

## 📁 Project Structure

```
indu 2.0/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes (for Phase 2+)
│   │   ├── services/         # Business logic (for Phase 2+)
│   │   ├── websocket/        # WebSocket handlers
│   │   │   └── manager.py    # Connection management
│   │   ├── ai/               # AI services (for Phase 3+)
│   │   ├── memory/           # Memory management (for Phase 7+)
│   │   ├── models/
│   │   │   └── schemas.py    # Pydantic models
│   │   ├── utils/
│   │   │   └── logger.py     # Logging setup
│   │   ├── prompts/          # AI prompts (for Phase 4+)
│   │   ├── config.py         # Configuration
│   │   └── main.py           # FastAPI app
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile           # Docker image
│   └── logs/               # Application logs
│
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── App.jsx
│   │   │   ├── ControlPanel.jsx
│   │   │   ├── ConversationContainer.jsx
│   │   │   └── ConnectionStatus.jsx
│   │   ├── services/        # API & WebSocket clients
│   │   │   ├── websocket.js
│   │   │   └── audio.js
│   │   ├── store/           # Zustand state management
│   │   │   └── conversationStore.js
│   │   ├── index.css        # Global styles
│   │   └── main.jsx         # React entry point
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml      # Multi-container setup
├── .env.example           # Environment variables
└── README.md             # This file
```

## 🔧 Environment Variables

### Backend (.env)

```env
# API Configuration
API_TITLE=Conversational AI Agent
DEBUG=false
PORT=8000

# Sarvam AI (Get from https://www.sarvam.ai)
SARVAM_API_KEY=your-api-key-here
SARVAM_LLM_MODEL=Meta-Llama-3-8B-Instruct
SARVAM_STT_MODEL=sarvam-speech-recognition-en-in
SARVAM_TTS_MODEL=meera

# Redis
REDIS_URL=redis://localhost:6379/0

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/conversational_ai

# Logging
LOG_LEVEL=INFO
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 🌐 API Endpoints

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "mode": "development"
}
```

### WebSocket Connection

```
WS /ws/conversation/{session_id}
```

#### Client Events (Send)

- `start_session`: Initialize conversation session
- `audio_chunk`: Stream audio data
- `stop_audio`: Stop audio input
- `interrupt`: Interrupt AI speaking
- `ping`: Keep-alive signal

#### Server Events (Receive)

- `session_started`: Session initialization complete
- `audio_received`: Acknowledgment of audio chunk
- `audio_stopped`: Audio stream stopped
- `interrupt_acknowledged`: Interrupt processed
- `transcription`: Real-time transcription updates
- `llm_response`: AI model response (Phase 4+)
- `audio_response`: Generated speech (Phase 5+)
- `error`: Error message
- `pong`: Keep-alive response

## 🛠️ Development Workflow

### PHASE 1 ✅ (Complete)
- [x] FastAPI backend setup
- [x] WebSocket server
- [x] React + Tailwind frontend
- [x] Audio capture service
- [x] Connection management
- [x] Docker setup

### PHASE 2 (Next)
- [ ] Microphone streaming optimization
- [ ] Audio buffer management
- [ ] Chunked transmission
- [ ] Browser audio API enhancements

### PHASE 3
- [ ] Sarvam STT integration
- [ ] Real-time transcription
- [ ] Language detection

### PHASE 4
- [ ] Sarvam LLM integration
- [ ] Prompt engineering
- [ ] Context management

### PHASE 5
- [ ] Sarvam TTS integration
- [ ] Audio streaming playback
- [ ] Voice customization

### PHASE 6
- [ ] Voice interruption handling
- [ ] VAD (Voice Activity Detection)
- [ ] Duplex communication

### PHASE 7
- [ ] Redis memory system
- [ ] PostgreSQL persistence
- [ ] Conversation history

### PHASE 8
- [ ] Authentication/Authorization
- [ ] User sessions
- [ ] Usage analytics

### PHASE 9
- [ ] Production deployment
- [ ] Performance optimization
- [ ] Monitoring & logging

## 🔐 Security Considerations

- [ ] CORS properly configured for production
- [ ] API key stored securely in environment variables
- [ ] WebSocket authentication
- [ ] Rate limiting
- [ ] Input validation
- [ ] SSL/TLS for production

## 📊 Database Schema (for Phase 7+)

```sql
-- Users table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table
CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  session_id VARCHAR(255) UNIQUE,
  language VARCHAR(50),
  personality VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER REFERENCES conversations(id),
  role VARCHAR(50),
  content TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Testing

```bash
# Backend tests (to be added)
pytest backend/tests/

# Frontend tests (to be added)
npm run test
```

## 📈 Performance Optimization

- WebSocket streaming for low latency
- Redis caching for fast memory access
- Audio chunking (100ms intervals)
- Browser audio processing
- Async/await pattern throughout
- Connection pooling

## 🐛 Troubleshooting

### WebSocket Connection Fails

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check logs
docker logs conversational-ai-backend
# or
tail -f backend/logs/app.log
```

### Microphone Permission Denied

- Check browser permissions
- Use HTTPS for production (some browsers require it)
- Reload page and allow microphone access

### Redis Connection Error

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# or check existing
redis-cli ping
```

### Database Connection Error

```bash
# Check PostgreSQL
docker logs conversational-ai-postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

## 📚 API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

## 🚢 Deployment

### Using Railway.app

```bash
# Push to git
git push railway main

# Railway will auto-detect and deploy
```

### Using Render.com

1. Connect GitHub repository
2. Create web service from docker-compose.yml
3. Set environment variables
4. Deploy

### Using AWS/GCP

See deployment guide in docs/DEPLOYMENT.md (coming soon)

## 📝 License

MIT License - See LICENSE file

## 👨‍💻 Contributing

1. Create feature branch (`git checkout -b feature/amazing-feature`)
2. Commit changes (`git commit -m 'Add amazing feature'`)
3. Push to branch (`git push origin feature/amazing-feature`)
4. Open Pull Request

## 🤝 Support

For issues and questions:
- GitHub Issues
- Discord Community (coming soon)
- Documentation: docs/

## 📞 Contact

- Email: support@conversational-ai.local
- Twitter: @ConvAI_India
- LinkedIn: conversational-ai-india

## 🙏 Acknowledgments

- Sarvam AI for LLM, STT, and TTS services
- FastAPI framework
- React & Tailwind CSS
- All contributors

---

## 🎯 Next Steps

1. **Get Sarvam API Key**: Visit https://www.sarvam.ai and sign up
2. **Set Environment Variables**: Update `.env` with your API key
3. **Start Development**: Run `docker-compose up -d`
4. **Access Frontend**: Open http://localhost:3000
5. **Begin Building**: Start PHASE 2 when ready

**Happy Building! 🚀**
