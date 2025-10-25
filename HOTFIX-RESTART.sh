#!/bin/bash

# Quick hotfix restart script
# This will restart the backend with the API key fix

echo "🔧 Restarting backend with API key fix..."
echo ""

# Pull latest changes
echo "1. Pulling latest changes..."
git pull origin claude/debug-docx-upload-error-011CUTsTebY7fdqoUHZ5ArHg

# Stop containers
echo ""
echo "2. Stopping containers..."
docker-compose down

# Start containers
echo ""
echo "3. Starting containers..."
docker-compose up -d

# Wait for startup
echo ""
echo "4. Waiting 20 seconds for services to start..."
sleep 20

# Check backend logs
echo ""
echo "5. Checking backend logs for API key..."
docker-compose logs backend | grep -i "anthropic\|api" | tail -5

# Test health
echo ""
echo "6. Testing health endpoint..."
curl -s http://localhost:5000/health | jq '.'

echo ""
echo "✅ Done! Try uploading again in the browser."
echo ""
echo "If you still see 'Network Error', check:"
echo "  - Backend logs: docker-compose logs backend"
echo "  - Frontend logs: docker-compose logs frontend"
echo "  - Network test: curl http://localhost:5000/health"
echo ""
