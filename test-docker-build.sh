#!/bin/bash

# Test Docker Build Script
# Validates that Docker Compose builds successfully in a clean environment

echo "=================================="
echo "Docker Build Test Script"
echo "=================================="
echo ""

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "   Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    echo "   Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker Compose is available"
echo ""

# Validate docker-compose.yml
echo "📋 Validating docker-compose.yml..."
if docker compose config > /dev/null 2>&1 || docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has errors"
    exit 1
fi
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found"
    echo "   Creating from .env.example..."
    cp .env.example .env
    echo "   ⚠️  Please edit .env and add your ANTHROPIC_API_KEY"
    echo ""
fi

# Test backend Dockerfile
echo "🔨 Testing backend Dockerfile build..."
if docker build -t fintech-backend-test ./backend; then
    echo "✅ Backend builds successfully"
    docker rmi fintech-backend-test 2>/dev/null
else
    echo "❌ Backend build failed"
    exit 1
fi
echo ""

# Test frontend Dockerfile
echo "🔨 Testing frontend Dockerfile build..."
if docker build -t fintech-frontend-test ./frontend; then
    echo "✅ Frontend builds successfully (even without package-lock.json)"
    docker rmi fintech-frontend-test 2>/dev/null
else
    echo "❌ Frontend build failed"
    exit 1
fi
echo ""

# Full docker-compose build test
echo "🔨 Testing full docker-compose build..."
if docker compose build || docker-compose build; then
    echo "✅ Docker Compose builds successfully"
else
    echo "❌ Docker Compose build failed"
    exit 1
fi
echo ""

echo "=================================="
echo "✅ All Docker build tests passed!"
echo "=================================="
echo ""
echo "To start the platform:"
echo "  ./start.sh"
echo ""
echo "Or manually:"
echo "  docker-compose up -d"
echo ""
