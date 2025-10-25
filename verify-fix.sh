#!/bin/bash

echo "=========================================="
echo "Fintech App - Upload Fix Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Step 1: Rebuilding containers with new configuration..."
echo "----------------------------------------------"
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo ""
echo "Step 2: Waiting for services to start (30s)..."
sleep 30

echo ""
echo "Step 3: Checking container health..."
echo "----------------------------------------------"
docker-compose ps

echo ""
echo "Step 4: Testing backend health endpoint..."
echo "----------------------------------------------"
BACKEND_HEALTH=$(curl -s http://localhost:5000/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend is accessible at http://localhost:5000${NC}"
    echo "Health response: $BACKEND_HEALTH"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

echo ""
echo "Step 5: Testing frontend proxy to backend..."
echo "----------------------------------------------"
PROXY_HEALTH=$(curl -s http://localhost:3000/api/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend nginx proxy is working${NC}"
    echo "Proxy response: $PROXY_HEALTH"
else
    echo -e "${RED}✗ Frontend proxy check failed${NC}"
fi

echo ""
echo "Step 6: Testing file upload with mock document..."
echo "----------------------------------------------"

# Find a mock DOCX file
MOCK_FILE=$(ls *.docx 2>/dev/null | head -1)

if [ -z "$MOCK_FILE" ]; then
    echo -e "${YELLOW}⚠ No .docx file found in root directory${NC}"
    echo "Please manually test upload from browser at: http://localhost:3000"
else
    echo "Using mock file: $MOCK_FILE"

    UPLOAD_RESPONSE=$(curl -s -X POST \
        -F "files=@$MOCK_FILE" \
        http://localhost:3000/api/upload)

    if echo "$UPLOAD_RESPONSE" | grep -q "success"; then
        echo -e "${GREEN}✓ File upload successful!${NC}"
        echo "Response: $UPLOAD_RESPONSE"
    else
        echo -e "${RED}✗ File upload failed${NC}"
        echo "Response: $UPLOAD_RESPONSE"
    fi
fi

echo ""
echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Open browser: http://localhost:3000"
echo "2. Navigate to upload page"
echo "3. Upload one of these mock files:"
ls -1 *.docx 2>/dev/null || echo "   (No .docx files found)"
echo ""
echo "4. Check browser console (F12) for any errors"
echo "5. Monitor backend logs with: docker-compose logs -f backend"
echo ""
