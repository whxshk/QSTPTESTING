#!/bin/bash
set -e

echo "=============================================="
echo "🔧 COMPLETE REBUILD - ALL YESTERDAY'S FIXES"
echo "=============================================="
echo ""
echo "This will restore:"
echo "  ✅ Sample Analyzer button"
echo "  ✅ Reward-based scoring (60-80 points)"
echo "  ✅ /tmp cache (no permission errors)"
echo "  ✅ Claude model fixed"
echo ""

# Navigate to project directory
cd /workspaces/QSTPTESTING || cd /home/user/QSTPTESTING || {
    echo "❌ Cannot find project directory!"
    exit 1
}

echo "📂 Working directory: $(pwd)"
echo ""

# Pull latest code
echo "📥 Pulling ALL latest code from yesterday's session..."
git fetch origin claude/debug-docx-upload-error-011CUTsTebY7fdqoUHZ5ArHg
git checkout claude/debug-docx-upload-error-011CUTsTebY7fdqoUHZ5ArHg
git pull origin claude/debug-docx-upload-error-011CUTsTebY7fdqoUHZ5ArHg
echo ""

# Verify key features are in code
echo "🔍 Verifying yesterday's features are in the code..."

if grep -q "HF_HOME=/tmp/huggingface" backend/Dockerfile; then
    echo "  ✅ /tmp cache fix is in Dockerfile"
else
    echo "  ❌ /tmp cache fix MISSING!"
fi

if grep -q "def compute_score(strengths" backend/scoring.py; then
    echo "  ✅ Reward-based scoring is in scoring.py"
else
    echo "  ❌ Reward-based scoring MISSING!"
fi

if grep -q "@app.route('/demo'" backend/app.py; then
    echo "  ✅ Demo endpoint is in app.py"
else
    echo "  ❌ Demo endpoint MISSING!"
fi

if grep -q "View Sample Analysis" frontend/src/pages/LandingPage.tsx 2>/dev/null; then
    echo "  ✅ Sample Analyzer button is in frontend"
else
    echo "  ⚠️  Sample Analyzer button might be missing"
fi

echo ""

# Create .env file
echo "📝 Checking .env file..."
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env with placeholder..."
    cat > .env << 'EOF'
ANTHROPIC_API_KEY=your-api-key-here
PORT=5000
FLASK_DEBUG=False
VITE_API_URL=/api
EOF
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your Anthropic API key!"
    echo "   (Check yesterday's messages for your API key)"
    echo ""
    read -p "Press Enter after you've updated .env with your API key..."
else
    echo "  ✅ .env file exists"
fi
echo ""

# Complete Docker cleanup
echo "🧹 COMPLETE Docker cleanup (removing everything)..."
docker-compose down -v 2>/dev/null || true
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker rmi qstptesting-backend qstptesting-frontend 2>/dev/null || true
docker system prune -f
echo "  ✅ Docker cleaned"
echo ""

# Rebuild from scratch
echo "🔨 Rebuilding from scratch (NO CACHE)..."
echo "   This will take 3-5 minutes to download model..."
docker-compose build --no-cache
echo "  ✅ Build complete!"
echo ""

# Start services
echo "🚀 Starting services..."
docker-compose up -d
echo ""

# Wait for startup
echo "⏳ Waiting 60 seconds for services to start..."
sleep 60
echo ""

# Verify services
echo "🔍 Verifying services are running..."
docker-compose ps
echo ""

# Verify backend is using /tmp cache
echo "🔍 Verifying backend is using /tmp cache (NEW code)..."
HF_HOME=$(docker-compose exec -T backend env 2>/dev/null | grep HF_HOME | cut -d= -f2 || echo "FAILED")
echo "   HF_HOME = $HF_HOME"

if [ "$HF_HOME" = "/tmp/huggingface" ]; then
    echo "  ✅ NEW CODE RUNNING! Using /tmp cache"
else
    echo "  ❌ OLD CODE! Still using /home/appuser/.cache"
    echo "     Rebuild may have failed. Check logs above."
fi
echo ""

# Test backend endpoints
echo "🧪 Testing backend endpoints..."

echo "   Testing /health endpoint..."
HEALTH=$(curl -s http://localhost:5000/health 2>/dev/null | grep -o "healthy" || echo "FAILED")
if [ "$HEALTH" = "healthy" ]; then
    echo "  ✅ Backend health check passed"
else
    echo "  ⚠️  Backend health check failed"
fi

echo "   Testing /demo endpoint..."
DEMO=$(curl -s http://localhost:5000/demo 2>/dev/null | grep -o "success" | head -1 || echo "FAILED")
if [ "$DEMO" = "success" ]; then
    echo "  ✅ Demo endpoint working!"
else
    echo "  ⚠️  Demo endpoint failed"
fi
echo ""

# Show recent logs
echo "📜 Recent backend logs:"
docker-compose logs backend | tail -30
echo ""

echo "=============================================="
echo "✅ REBUILD COMPLETE!"
echo "=============================================="
echo ""
echo "🌐 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:5000"
echo ""
echo "📱 IMPORTANT FOR CODESPACES:"
echo "   1. Go to PORTS tab in VS Code"
echo "   2. Forward ports 3000 and 5000"
echo "   3. Set visibility to PUBLIC"
echo "   4. Click globe icon next to port 3000"
echo ""
echo "🧪 Test these features:"
echo "   1. Click 'View Sample Analysis' button → should show 60+ score"
echo "   2. Upload 4 DOCX files → should work without permission error"
echo "   3. Analyze compliance → should show strengths + gaps"
echo ""

if [ "$HF_HOME" = "/tmp/huggingface" ]; then
    echo "🎉 Everything is ready! Permission errors should be GONE!"
else
    echo "⚠️  WARNING: Old code may still be running. Try:"
    echo "   docker-compose down -v && docker-compose up --build -d"
fi
echo ""
