#!/bin/bash

# Fintech Regulatory Readiness Platform - Quick Start Script

echo "=================================="
echo "Fintech Regulatory Readiness Platform"
echo "Quick Start Script"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your ANTHROPIC_API_KEY"
    echo "   Get your API key from: https://console.anthropic.com/"
    echo ""
    read -p "Press Enter once you've added your API key to .env..."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "🐳 Starting services with Docker Compose..."
echo ""

# Stop any existing containers
docker-compose down 2>/dev/null

# Build and start containers
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "fintech-backend"; then
    echo "✅ Backend is running"
else
    echo "❌ Backend failed to start. Check logs with: docker-compose logs backend"
    exit 1
fi

if docker-compose ps | grep -q "fintech-frontend"; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend failed to start. Check logs with: docker-compose logs frontend"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ Platform is ready!"
echo "=================================="
echo ""
echo "📍 Access points:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:5000"
echo "   Health:   http://localhost:5000/health"
echo ""
echo "📚 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop:"
echo "   docker-compose down"
echo ""
echo "🧪 Sample documents for testing:"
echo "   ./sample-documents/"
echo ""
