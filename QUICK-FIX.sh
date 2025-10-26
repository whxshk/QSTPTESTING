#!/bin/bash
set -e

echo "=============================================="
echo "🔧 QUICK FIX - Rebuild with Yesterday's Code"
echo "=============================================="
echo ""

cd /workspaces/QSTPTESTING 2>/dev/null || cd /home/user/QSTPTESTING || {
    echo "❌ Run this in your Codespaces terminal!"
    exit 1
}

echo "📂 Working in: $(pwd)"
echo ""

# Complete Docker cleanup
echo "🧹 Removing old Docker containers and images..."
docker-compose down -v 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker rmi qstptesting-backend qstptesting-frontend 2>/dev/null || true
docker system prune -f
echo "  ✅ Cleanup complete"
echo ""

# Rebuild from scratch - NO CACHE
echo "🔨 Rebuilding from scratch (this downloads the AI model)..."
echo "   Takes 3-5 minutes..."
docker-compose build --no-cache
echo "  ✅ Build complete!"
echo ""

# Start services
echo "🚀 Starting services..."
docker-compose up -d
echo ""

# Wait for startup
echo "⏳ Waiting 60 seconds for services to fully start..."
sleep 60
echo ""

# Verify NEW code is running
echo "🔍 Verifying NEW code is running..."
HF_HOME=$(docker-compose exec -T backend env 2>/dev/null | grep HF_HOME | cut -d= -f2 || echo "FAILED")
echo "   HF_HOME = $HF_HOME"

if [ "$HF_HOME" = "/tmp/huggingface" ]; then
    echo "  ✅ SUCCESS! Running NEW code with /tmp cache"
    echo "  ✅ Permission errors should be GONE!"
else
    echo "  ❌ WARNING: Still showing old cache path"
    echo "     Try: docker-compose down -v && docker-compose up --build -d"
fi
echo ""

# Test endpoints
echo "🧪 Testing backend..."
HEALTH=$(curl -s http://localhost:5000/health 2>/dev/null | grep -o "healthy" || echo "FAILED")
if [ "$HEALTH" = "healthy" ]; then
    echo "  ✅ Backend is healthy"
else
    echo "  ⚠️  Backend may still be starting..."
fi

DEMO=$(curl -s http://localhost:5000/demo 2>/dev/null | grep -o "success" | head -1 || echo "FAILED")
if [ "$DEMO" = "success" ]; then
    echo "  ✅ Demo endpoint working (Sample Analyzer ready!)"
else
    echo "  ⚠️  Demo endpoint not responding yet"
fi
echo ""

# Show logs
echo "📜 Recent backend logs:"
docker-compose logs backend | tail -20
echo ""

echo "=============================================="
echo "✅ REBUILD COMPLETE!"
echo "=============================================="
echo ""
echo "🌐 Access your app:"
echo "   1. Go to PORTS tab in VS Code"
echo "   2. Make ports 3000 and 5000 PUBLIC"
echo "   3. Click globe icon next to port 3000"
echo ""
echo "🧪 Test these features:"
echo "   1. 'View Sample Analysis' button → should show 60+ score"
echo "   2. Upload 4 DOCX files → NO permission errors!"
echo "   3. Analyze compliance → shows strengths + gaps"
echo ""

if [ "$HF_HOME" = "/tmp/huggingface" ]; then
    echo "🎉 Everything restored! Permission errors are GONE!"
else
    echo "⚠️  If permission errors persist, check logs above"
fi
echo ""
