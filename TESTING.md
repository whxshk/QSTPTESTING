# Testing Guide - Fintech Regulatory Readiness Platform

## Quick Validation Steps

### 1. Backend API Tests

```bash
# Health check
curl http://localhost:5000/health

# Expected response:
# {
#   "status": "healthy",
#   "claude_configured": true,
#   "index_stats": {...}
# }

# Get rules
curl http://localhost:5000/rules

# Get resources
curl http://localhost:5000/resources
```

### 2. Document Upload Test

```bash
# Upload sample documents
curl -X POST http://localhost:5000/upload \
  -F "files=@./sample-documents/SAMPLE-BUSINESS-PLAN.txt" \
  -F "files=@./sample-documents/SAMPLE-COMPLIANCE-POLICY.txt"

# Expected response:
# {
#   "success": true,
#   "message": "Successfully indexed 2 files",
#   "chunks_indexed": <number>,
#   "files_processed": 2
# }
```

### 3. Analysis Test

```bash
# Analyze compliance
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "P2P lending platform with QAR 5M paid-up capital. Data hosted in AWS Ireland and Singapore. No dedicated Compliance Officer yet. AML policy drafted but not board-approved. Transaction limit QAR 45,000. Manual customer verification process."
  }'

# Expected response includes:
# - score (0-100)
# - gaps array with compliance issues
# - recommendations with programs and experts
```

### 4. Frontend Test Flow

1. **Navigate to http://localhost:3000**
   - Landing page should load
   - Check "Upload Documents & Start Analysis" button

2. **Upload Page**
   - Drag and drop files or click to select
   - Upload the sample documents from `./sample-documents/`
   - Verify "X chunks indexed" success message

3. **Summary Page**
   - Click "Use Example" to populate summary
   - Or enter custom startup description
   - Click "Analyze Compliance"
   - Wait 10-30 seconds for AI analysis

4. **Results Dashboard**
   - Verify score is displayed (e.g., 45/100)
   - Check gaps table with severity badges
   - Review recommendations section
   - Test "Download Report" button

### 5. Expected Test Results

For the sample documents provided, you should see:

**Identified Gaps:**
- ❌ **Data Residency** (High Severity) - Data hosted outside Qatar
- ❌ **Compliance Officer** (High Severity) - No dedicated officer
- ⚠️ **AML/CFT Policy** (Medium Severity) - Draft but not board-approved
- ⚠️ **Cybersecurity** (Medium Severity) - No ISO 27001 certification
- ℹ️ **Transaction Monitoring** (Low Severity) - Manual processes

**Expected Score Range:** 30-55/100

**Recommendations Should Include:**
- QDB_INCUBATOR_001 (Fintech Regulatory Accelerator)
- QDB_EXPERT_002 (AML Compliance Workshop)
- Expert: Dr. Aisha Al-Mansoori (Data Residency)
- Expert: Mr. Karim Hassan (AML/CFT)

### 6. Error Testing

Test error handling:

```bash
# Upload without files
curl -X POST http://localhost:5000/upload

# Analyze without upload
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"summary": "test"}'

# Analyze with empty summary
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"summary": ""}'
```

### 7. Performance Test

```bash
# Time the analysis
time curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"summary": "P2P lending, QAR 5M capital, data in Ireland"}'

# Should complete in 10-30 seconds
```

### 8. Docker Health Checks

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend

# Check health endpoints
docker-compose exec backend python -c "import requests; print(requests.get('http://localhost:5000/health').json())"
```

## Troubleshooting Test Failures

### Backend doesn't respond
```bash
docker-compose logs backend
# Check for API key errors or missing dependencies
```

### Analysis returns errors
- Verify ANTHROPIC_API_KEY is set correctly
- Check API key has credits available
- Review backend logs for detailed error messages

### Frontend can't reach backend
- Verify both containers are running: `docker-compose ps`
- Check network connectivity: `docker network ls`
- Test backend directly: `curl http://localhost:5000/health`

### No gaps identified
- This can happen if documents show good compliance
- Try the example summary which has known gaps
- Verify Claude is returning structured JSON

## Manual Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:3000
- [ ] Health endpoint returns healthy status
- [ ] Rules and resources load successfully
- [ ] File upload accepts DOCX/PDF files
- [ ] Upload returns chunks_indexed > 0
- [ ] Analysis completes in < 30 seconds
- [ ] Analysis returns valid JSON with gaps
- [ ] Score is calculated correctly
- [ ] Recommendations match gap types
- [ ] Download report works
- [ ] "New Analysis" resets the app
- [ ] Error messages display properly
- [ ] UI is responsive on mobile

## Automated Test Script

```bash
#!/bin/bash
# test-platform.sh

echo "Running platform tests..."

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s http://localhost:5000/health | grep -q "healthy" && echo "✅ Health check passed" || echo "❌ Health check failed"

# Test 2: Rules endpoint
echo "2. Testing rules endpoint..."
curl -s http://localhost:5000/rules | grep -q "QCB" && echo "✅ Rules endpoint passed" || echo "❌ Rules endpoint failed"

# Test 3: Upload
echo "3. Testing upload..."
UPLOAD_RESULT=$(curl -s -X POST http://localhost:5000/upload \
  -F "files=@./sample-documents/SAMPLE-BUSINESS-PLAN.txt")
echo "$UPLOAD_RESULT" | grep -q "success" && echo "✅ Upload passed" || echo "❌ Upload failed"

# Test 4: Analysis
echo "4. Testing analysis..."
ANALYSIS_RESULT=$(curl -s -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"summary": "P2P lending, data in Ireland"}')
echo "$ANALYSIS_RESULT" | grep -q "score" && echo "✅ Analysis passed" || echo "❌ Analysis failed"

echo ""
echo "All tests completed!"
```

Save as `test-platform.sh`, make executable with `chmod +x test-platform.sh`, and run with `./test-platform.sh`.

## Load Testing (Optional)

For production readiness, test with multiple concurrent requests:

```bash
# Install apache bench
# apt-get install apache2-utils

# Test health endpoint
ab -n 100 -c 10 http://localhost:5000/health

# Test with larger load
ab -n 1000 -c 50 http://localhost:5000/rules
```

## Test Coverage Summary

| Component | Test Type | Status |
|-----------|-----------|--------|
| Backend API | Manual | ✅ |
| Frontend UI | Manual | ✅ |
| Document Upload | Functional | ✅ |
| AI Analysis | Integration | ✅ |
| Error Handling | Edge Cases | ✅ |
| Docker Deploy | Container | ✅ |
| Performance | Load | ⏳ Optional |

---

**Note**: These tests verify core functionality. For production deployment, implement comprehensive unit tests, integration tests, and security testing.
