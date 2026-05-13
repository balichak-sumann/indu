#!/bin/bash

# Quick Start Script for Conversational AI Agent
# This script sets up and starts the entire project

set -e

echo "🚀 Starting Conversational AI Agent Setup..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker found${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose found${NC}"

# Copy .env file if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}📋 Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please update .env with your Sarvam API key${NC}"
    echo -e "${YELLOW}📖 Get your API key from https://www.sarvam.ai${NC}"
fi

# Build images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
docker-compose build

# Start services
echo -e "${YELLOW}🌍 Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check services
echo -e "${YELLOW}🔍 Checking service status...${NC}"

BACKEND_HEALTH=$(curl -s http://localhost:8000/health || echo "failed")
if [ "$BACKEND_HEALTH" != "failed" ]; then
    echo -e "${GREEN}✅ Backend is running on http://localhost:8000${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
fi

if [ $(docker ps -q -f "name=conversational-ai-frontend" | wc -l) -gt 0 ]; then
    echo -e "${GREEN}✅ Frontend is running on http://localhost:3000${NC}"
else
    echo -e "${RED}❌ Frontend failed to start${NC}"
fi

if [ $(docker ps -q -f "name=conversational-ai-redis" | wc -l) -gt 0 ]; then
    echo -e "${GREEN}✅ Redis is running on localhost:6379${NC}"
else
    echo -e "${RED}❌ Redis failed to start${NC}"
fi

if [ $(docker ps -q -f "name=conversational-ai-postgres" | wc -l) -gt 0 ]; then
    echo -e "${GREEN}✅ PostgreSQL is running on localhost:5432${NC}"
else
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""
echo -e "${YELLOW}📚 Next Steps:${NC}"
echo -e "1. Open http://localhost:3000 in your browser"
echo -e "2. Allow microphone access when prompted"
echo -e "3. Start speaking to the AI agent"
echo ""
echo -e "${YELLOW}🔗 Quick Links:${NC}"
echo -e "Frontend:    http://localhost:3000"
echo -e "Backend API: http://localhost:8000"
echo -e "API Docs:    http://localhost:8000/docs"
echo -e "PgAdmin:     http://localhost:5050"
echo -e "Redis:       localhost:6379"
echo -e "PostgreSQL:  localhost:5432"
echo ""
echo -e "${YELLOW}📖 Useful Commands:${NC}"
echo -e "View logs:       docker-compose logs -f"
echo -e "Stop services:   docker-compose down"
echo -e "Stop & remove:   docker-compose down -v"
echo -e "Restart:         docker-compose restart"
echo ""
echo -e "${GREEN}Happy Coding! 🚀${NC}"
