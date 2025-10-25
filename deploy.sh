#!/bin/bash

# Deployment Script for Fintech Regulatory Compliance AI App
# This script deploys and tests the fixed application

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo "  🚀 Deploying Fintech App"
echo "=========================================="
echo ""

# Step 1: Verify we're in the right directory
echo -e "${BLUE}Step 1: Verifying directory...${NC}"
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi
echo -e "${GREEN}✓ In correct directory${NC}"
echo ""

# Step 2: Check for .env file
echo -e "${BLUE}Step 2: Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠ IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY${NC}"
    echo ""
    read -p "Press Enter after you've set your API key in .env, or Ctrl+C to cancel..."
fi

# Verify API key is set
if grep -q "your_anthropic_api_key_here" .env; then
    echo -e "${RED}Error: ANTHROPIC_API_KEY is still set to placeholder!${NC}"
    echo "Please edit .env and set your actual API key."
    exit 1
fi

echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Step 3: Stop existing containers
echo -e "${BLUE}Step 3: Stopping existing containers...${NC}"
docker-compose down || true
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Step 4: Build containers
echo -e "${BLUE}Step 4: Building containers (this may take a few minutes)...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✓ Containers built${NC}"
echo ""

# Step 5: Start services
echo -e "${BLUE}Step 5: Starting services...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Step 6: Wait for services to be ready
echo -e "${BLUE}Step 6: Waiting for services to be ready (30 seconds)...${NC}"
sleep 30
echo -e "${GREEN}✓ Services should be ready${NC}"
echo ""

# Step 7: Check container status
echo -e "${BLUE}Step 7: Checking container status...${NC}"
docker-compose ps
echo ""

# Step 8: Check backend logs for API key
echo -e "${BLUE}Step 8: Checking backend logs...${NC}"
docker-compose logs backend | tail -n 20
echo ""

# Step 9: Run health checks
echo -e "${BLUE}Step 9: Running health checks...${NC}"

echo "Testing backend health..."
BACKEND_HEALTH=$(curl -s http://localhost:5000/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend is responding${NC}"
    echo "$BACKEND_HEALTH" | jq '.' || echo "$BACKEND_HEALTH"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    echo "Check logs with: docker-compose logs backend"
fi
echo ""

echo "Testing frontend proxy..."
PROXY_HEALTH=$(curl -s http://localhost:3000/api/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend proxy is working${NC}"
    echo "$PROXY_HEALTH" | jq '.' || echo "$PROXY_HEALTH"
else
    echo -e "${RED}✗ Frontend proxy check failed${NC}"
    echo "Check logs with: docker-compose logs frontend"
fi
echo ""

# Step 10: Run automated tests
echo -e "${BLUE}Step 10: Running automated test suite...${NC}"
if [ -f "./test-api.sh" ]; then
    chmod +x test-api.sh
    ./test-api.sh
else
    echo -e "${YELLOW}⚠ test-api.sh not found, skipping automated tests${NC}"
fi
echo ""

# Final summary
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}Your application is now running:${NC}"
echo ""
echo "  🌐 Frontend:  http://localhost:3000"
echo "  🔧 Backend:   http://localhost:5000"
echo "  ❤️  Health:    http://localhost:5000/health"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Click 'Upload Documents & Start Analysis'"
echo "  3. Upload mock DOCX files from the project root:"
echo "     - 2. Mock Startup Business Plan (Input Document).docx"
echo "     - 4. Mock Startup Internal Compliance Policy.docx"
echo "     - 6. Mock Startup Legal Structure Document.docx"
echo "  4. Verify 'Upload Successful!' message appears"
echo "  5. Continue to summary and run analysis"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs:     docker-compose logs -f"
echo "  Stop app:      docker-compose down"
echo "  Restart:       docker-compose restart"
echo ""
echo -e "${GREEN}Happy testing! 🎉${NC}"
echo ""
