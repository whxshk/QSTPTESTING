#!/bin/bash
set -e

echo "FIXING THE APP - NO MORE BS"
echo "================================"
echo ""

# Stop everything
echo "1. Stopping containers..."
docker-compose down

# Rebuild backend with NEW anthropic library
echo "2. Rebuilding backend with updated library..."
docker-compose build --no-cache backend

# Start
echo "3. Starting containers..."
docker-compose up -d

# Wait
echo "4. Waiting 30 seconds..."
sleep 30

# Test the ACTUAL workflow
echo ""
echo "5. TESTING ACTUAL WORKFLOW:"
echo "================================"
echo ""

# Test 1: Upload a DOCX
echo "TEST 1: Upload DOCX file"
DOCX=$(ls *.docx 2>/dev/null | head -1)
if [ -z "$DOCX" ]; then
    echo "ERROR: No .docx file found!"
    exit 1
fi

echo "Uploading: $DOCX"
UPLOAD=$(curl -s -X POST -F "files=@$DOCX" http://localhost:5000/upload)
echo "$UPLOAD"

if echo "$UPLOAD" | grep -q '"success":true'; then
    echo "✅ UPLOAD WORKS"
else
    echo "❌ UPLOAD FAILED"
    echo "Backend logs:"
    docker-compose logs backend | tail -20
    exit 1
fi
echo ""

# Test 2: Analyze
echo "TEST 2: Run analysis"
ANALYSIS=$(curl -s -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"summary": "Fintech startup providing payment processing. We have a business plan and basic AML policies. Data hosted in Ireland. No compliance officer yet."}')

echo "$ANALYSIS"

if echo "$ANALYSIS" | grep -q '"score"'; then
    SCORE=$(echo "$ANALYSIS" | grep -o '"score":[0-9]*' | cut -d: -f2)
    GAP_COUNT=$(echo "$ANALYSIS" | grep -o '"gap_count":[0-9]*' | cut -d: -f2)
    echo ""
    echo "✅ ANALYSIS WORKS"
    echo "   Score: $SCORE"
    echo "   Gaps found: $GAP_COUNT"
else
    echo "❌ ANALYSIS FAILED"
    echo "Backend logs:"
    docker-compose logs backend | tail -20
    exit 1
fi

echo ""
echo "================================"
echo "✅ THE APP WORKS!"
echo "================================"
echo ""
echo "Open http://localhost:3000 and:"
echo "1. Upload your DOCX files"
echo "2. Enter company description"
echo "3. Get your scorecard and gap analysis"
echo ""
