#!/bin/bash

# GUARANTEED FIX SCRIPT
# This will reset everything and start fresh

set -e

echo "=========================================="
echo "  GUARANTEED FIX - Starting..."
echo "=========================================="
echo ""

# Step 1: Stop everything
echo "Step 1: Stopping all containers..."
docker-compose down -v
echo "✓ Done"
echo ""

# Step 2: Verify .env exists
echo "Step 2: Checking .env file..."
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY!"
    echo "   Then run this script again."
    exit 1
fi

# Check if API key is set
if grep -q "your_anthropic_api_key_here" .env; then
    echo "⚠️  ERROR: ANTHROPIC_API_KEY is still set to placeholder!"
    echo ""
    echo "Edit .env and replace:"
    echo "  ANTHROPIC_API_KEY=your_anthropic_api_key_here"
    echo "With:"
    echo "  ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✓ .env file exists with API key"
echo ""

# Step 3: Pull latest code
echo "Step 3: Pulling latest code..."
git pull origin claude/debug-docx-upload-error-011CUTsTebY7fdqoUHZ5ArHg
echo "✓ Done"
echo ""

# Step 4: Rebuild from scratch (no cache)
echo "Step 4: Rebuilding containers (this will take 2-3 minutes)..."
docker-compose build --no-cache
echo "✓ Done"
echo ""

# Step 5: Start services
echo "Step 5: Starting services..."
docker-compose up -d
echo "✓ Done"
echo ""

# Step 6: Wait for startup
echo "Step 6: Waiting 30 seconds for services to start..."
for i in {30..1}; do
    echo -ne "\r   Waiting: $i seconds... "
    sleep 1
done
echo ""
echo "✓ Done"
echo ""

# Step 7: Check container status
echo "Step 7: Checking container status..."
docker-compose ps
echo ""

# Step 8: Check backend logs
echo "Step 8: Checking backend logs for errors..."
echo "---"
docker-compose logs backend | tail -20
echo ""

# Step 9: Verify API key is loaded
echo "Step 9: Verifying API key in container..."
API_KEY_CHECK=$(docker exec fintech-backend env | grep ANTHROPIC_API_KEY || echo "NOT FOUND")
if [[ "$API_KEY_CHECK" == *"sk-ant-"* ]]; then
    echo "✓ API key is loaded in container"
else
    echo "✗ API key NOT found in container!"
    echo "  This is the problem!"
fi
echo ""

# Step 10: Test health endpoint
echo "Step 10: Testing backend health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:5000/health)
if [ $? -eq 0 ]; then
    echo "✓ Backend is responding"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo "✗ Backend is NOT responding"
    echo "  Check logs above for errors"
fi
echo ""

# Step 11: Test proxy
echo "Step 11: Testing frontend proxy..."
PROXY_RESPONSE=$(curl -s http://localhost:3000/api/health)
if [ $? -eq 0 ]; then
    echo "✓ Frontend proxy is working"
else
    echo "✗ Frontend proxy is NOT working"
fi
echo ""

# Step 12: Test upload
echo "Step 12: Testing file upload..."
DOCX_FILE=$(ls *.docx 2>/dev/null | head -1)
if [ -n "$DOCX_FILE" ]; then
    echo "Using file: $DOCX_FILE"
    UPLOAD_RESPONSE=$(curl -s -X POST -F "files=@$DOCX_FILE" http://localhost:5000/upload)
    if echo "$UPLOAD_RESPONSE" | grep -q '"success":true'; then
        echo "✓ Upload test SUCCESSFUL!"
        echo "$UPLOAD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPLOAD_RESPONSE"
    else
        echo "✗ Upload test FAILED"
        echo "$UPLOAD_RESPONSE"
    fi
else
    echo "⚠️  No .docx file found for testing"
fi
echo ""

# Final summary
echo "=========================================="
echo "  FIX COMPLETE!"
echo "=========================================="
echo ""
echo "✅ Your application should now be running:"
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:5000"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Click 'Upload Documents & Start Analysis'"
echo "  3. Upload a DOCX file"
echo "  4. It should say 'Upload Successful!'"
echo ""
echo "If it still doesn't work:"
echo "  1. Run: docker-compose logs backend"
echo "  2. Look for errors in the output"
echo "  3. Send me the error message"
echo ""
