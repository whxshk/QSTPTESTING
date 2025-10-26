#!/bin/bash
set -e

echo "========================================="
echo "🔍 DIAGNOSTIC & FIX SCRIPT"
echo "========================================="
echo ""

# Check current directory
echo "📂 Current directory:"
pwd
echo ""

# Check if we're in the right place
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ ERROR: docker-compose.yml not found!"
    echo "You need to cd to /workspaces/QSTPTESTING first"
    exit 1
fi

echo "✅ In correct directory"
echo ""

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin claude/debug-docx-upload-error-011CUTsTebY7fdqoUHZ5ArHg
echo ""

# Check if Dockerfile has /tmp (new version)
echo "🔍 Checking if Dockerfile uses /tmp (new version)..."
if grep -q "ENV HF_HOME=/tmp/huggingface" backend/Dockerfile; then
    echo "✅ Dockerfile has NEW code (using /tmp)"
else
    echo "❌ Dockerfile has OLD code!"
    echo "Git pull may have failed. Check git status."
    exit 1
fi
echo ""

# Stop everything
echo "🛑 Stopping ALL containers..."
docker-compose down -v
docker stop $(docker ps -aq) 2>/dev/null || true
echo ""

# Remove old images
echo "🗑️  Removing old backend images..."
docker rmi qstptesting-backend 2>/dev/null || true
docker rmi $(docker images -q qstptesting-backend) 2>/dev/null || true
echo ""

# Clean Docker
echo "🧹 Cleaning Docker system..."
docker system prune -f
echo ""

# Build from scratch with NO CACHE
echo "🔨 Building backend from scratch (NO CACHE)..."
echo "This will take 2-3 minutes to download the model..."
docker-compose build --no-cache backend
echo ""

# Verify build succeeded
if [ $? -eq 0 ]; then
    echo "✅ Build succeeded!"
else
    echo "❌ Build failed!"
    exit 1
fi
echo ""

# Start services
echo "🚀 Starting services..."
docker-compose up -d
echo ""

# Wait for startup
echo "⏳ Waiting 60 seconds for services to start..."
sleep 60
echo ""

# Check container status
echo "📊 Container status:"
docker-compose ps
echo ""

# Verify NEW code is running by checking env vars
echo "🔍 Verifying NEW code is running (checking HF_HOME)..."
HF_HOME=$(docker-compose exec -T backend env | grep HF_HOME | cut -d= -f2)
echo "HF_HOME = $HF_HOME"

if [ "$HF_HOME" = "/tmp/huggingface" ]; then
    echo "✅ NEW CODE IS RUNNING! Using /tmp cache."
else
    echo "❌ OLD CODE STILL RUNNING! HF_HOME should be /tmp/huggingface"
    echo "This means the rebuild didn't work properly."
    exit 1
fi
echo ""

# Check if model is in /tmp
echo "🔍 Checking if model is cached in /tmp..."
docker-compose exec -T backend ls -la /tmp/huggingface/ || echo "⚠️ /tmp/huggingface doesn't exist - this is bad"
echo ""

# Show logs
echo "📜 Backend logs (last 30 lines):"
docker-compose logs backend | tail -30
echo ""

echo "========================================="
echo "✅ VERIFICATION COMPLETE!"
echo "========================================="
echo ""
echo "If you saw '✅ NEW CODE IS RUNNING!' above, the permission error should be fixed."
echo "If you still see OLD CODE, there's a caching issue with Docker."
echo ""
echo "🌐 Try uploading files now at http://localhost:3000"
echo ""
