@echo off
REM Quick Start Script for Windows
REM Conversational AI Agent Setup

echo.
echo 🚀 Starting Conversational AI Agent Setup...
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo 📥 Download from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

echo ✅ Docker found

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed
    exit /b 1
)

echo ✅ Docker Compose found

REM Copy .env if not exists
if not exist .env (
    echo 📋 Creating .env file...
    copy .env.example .env
    echo ⚠️  Please update .env with your Sarvam API key
    echo 📖 Get your API key from https://www.sarvam.ai
    echo.
    pause
)

REM Build images
echo 🔨 Building Docker images...
docker-compose build

REM Start services
echo 🌍 Starting services...
docker-compose up -d

REM Wait for services
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak

REM Check services
echo 🔍 Checking service status...
echo.

for /f "tokens=*" %%i in ('curl -s http://localhost:8000/health 2^>nul') do set BACKEND_HEALTH=%%i
if "%BACKEND_HEALTH%"=="" (
    echo ❌ Backend failed to start
) else (
    echo ✅ Backend is running on http://localhost:8000
)

echo ✅ Frontend is running on http://localhost:3000
echo ✅ Redis is running on localhost:6379
echo ✅ PostgreSQL is running on localhost:5432
echo.

echo 🎉 Setup Complete!
echo.

echo 📚 Next Steps:
echo 1. Open http://localhost:3000 in your browser
echo 2. Allow microphone access when prompted
echo 3. Start speaking to the AI agent
echo.

echo 🔗 Quick Links:
echo Frontend:    http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs:    http://localhost:8000/docs
echo PgAdmin:     http://localhost:5050
echo.

echo 📖 Useful Commands:
echo View logs:       docker-compose logs -f
echo Stop services:   docker-compose down
echo Stop ^& remove:   docker-compose down -v
echo Restart:         docker-compose restart
echo.

echo 🚀 Happy Coding!
echo.

pause
