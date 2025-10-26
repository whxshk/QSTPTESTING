#!/bin/bash

# Emergency Diagnostic Script
# Run this and send me ALL the output

echo "=========================================="
echo "EMERGENCY DIAGNOSTIC REPORT"
echo "=========================================="
echo ""

echo "1. GIT STATUS"
echo "---"
git status
git log --oneline -3
echo ""

echo "2. DOCKER CONTAINERS"
echo "---"
docker-compose ps
echo ""

echo "3. BACKEND LOGS (Last 50 lines)"
echo "---"
docker-compose logs backend | tail -50
echo ""

echo "4. FRONTEND LOGS (Last 30 lines)"
echo "---"
docker-compose logs frontend | tail -30
echo ""

echo "5. ENVIRONMENT FILE"
echo "---"
if [ -f .env ]; then
    echo ".env exists"
    cat .env | sed 's/sk-ant-api03-[^[:space:]]*/sk-ant-api03-REDACTED/g'
else
    echo ".env MISSING!"
fi
echo ""

echo "6. DOCKER-COMPOSE ENVIRONMENT"
echo "---"
grep -A 5 "backend:" docker-compose.yml
grep -A 3 "env_file:" docker-compose.yml || echo "No env_file found"
echo ""

echo "7. HEALTH CHECK - BACKEND DIRECT"
echo "---"
curl -s http://localhost:5000/health || echo "BACKEND NOT RESPONDING"
echo ""

echo "8. HEALTH CHECK - VIA PROXY"
echo "---"
curl -s http://localhost:3000/api/health || echo "PROXY NOT RESPONDING"
echo ""

echo "9. BACKEND CONTAINER INSPECTION"
echo "---"
docker exec fintech-backend env | grep ANTHROPIC || echo "API KEY NOT IN CONTAINER!"
echo ""

echo "10. PYTHON VERSION IN CONTAINER"
echo "---"
docker exec fintech-backend python --version
echo ""

echo "11. ANTHROPIC LIBRARY VERSION"
echo "---"
docker exec fintech-backend pip show anthropic || echo "Library not installed!"
echo ""

echo "=========================================="
echo "END OF DIAGNOSTIC REPORT"
echo "=========================================="
echo ""
echo "Copy ALL of the above output and send it to me!"
