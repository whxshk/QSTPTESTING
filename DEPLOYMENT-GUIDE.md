# 🚀 Quick Deployment Guide

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- Your ANTHROPIC_API_KEY ready

---

## 🎯 Deploy in 3 Steps

### Step 1: Pull the Latest Code

If you haven't already cloned the repo:
```bash
git clone https://github.com/whxshk/QSTPTESTING.git
cd QSTPTESTING
```

If you already have it, pull the latest changes:
```bash
cd QSTPTESTING
git pull origin claude/debug-docx-upload-error-011CUTsTebY7fdqoUHZ5ArHg
```

---

### Step 2: Configure Environment

The `.env` file is already created with the API key. Verify it:

```bash
cat .env
```

Should show:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
PORT=5000
FLASK_DEBUG=False
VITE_API_URL=/api
```

✅ **The API key is already configured!**

---

### Step 3: Deploy and Test

**Option A: Automated Deployment (Recommended)**
```bash
./deploy.sh
```

This script will:
- ✅ Stop existing containers
- ✅ Rebuild with latest code
- ✅ Start services
- ✅ Run health checks
- ✅ Execute automated tests
- ✅ Show you the URLs to access

**Option B: Manual Deployment**
```bash
# Stop existing containers
docker-compose down

# Rebuild (no cache to ensure fresh build)
docker-compose build --no-cache

# Start services
docker-compose up -d

# Wait 30 seconds for startup
sleep 30

# Check status
docker-compose ps

# Run tests
./test-api.sh
```

---

## 🧪 Verify It's Working

### 1. Check Health Endpoints

```bash
# Backend direct
curl http://localhost:5000/health

# Frontend proxy
curl http://localhost:3000/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "claude_configured": true,
  "api_key_present": true,
  "index_stats": {
    "indexed": false,
    "total_chunks": 0,
    "index_size": 0
  }
}
```

---

### 2. Test File Upload

```bash
curl -i -X POST \
  -F "files=@2. Mock Startup Business Plan (Input Document).docx" \
  http://localhost:5000/upload
```

**Expected response:**
```
HTTP/1.1 200 OK

{
  "success": true,
  "message": "Successfully indexed 1 files",
  "chunks_indexed": 45,
  "files_processed": 1,
  "embedding_dimension": 384
}
```

---

### 3. Test in Browser

1. **Open**: http://localhost:3000

2. **Click**: "Upload Documents & Start Analysis"

3. **Upload** mock DOCX files (from project root):
   - `2. Mock Startup Business Plan (Input Document).docx`
   - `4. Mock Startup Internal Compliance Policy.docx`
   - `6. Mock Startup Legal Structure Document.docx`

4. **Click**: "Upload & Process"

5. **Verify**: You see "Upload Successful!" with chunk count

6. **Click**: "Continue to Summary"

7. **Enter** startup description or click "Use Example"

8. **Click**: "Analyze Compliance"

9. **Verify**: Compliance score and gaps appear

---

## 🔍 Troubleshooting

### Problem: Backend not responding

**Check logs:**
```bash
docker-compose logs backend
```

**Look for:**
- `Anthropic client initialized successfully` ✅
- `Starting Flask server on port 5000` ✅

**If you see "ANTHROPIC_API_KEY not found":**
```bash
# Verify .env file
cat .env | grep ANTHROPIC_API_KEY

# Restart backend
docker-compose restart backend
```

---

### Problem: Upload shows "Network Error"

**Test connectivity:**
```bash
# Test backend directly
curl http://localhost:5000/health

# Test via proxy
curl http://localhost:3000/api/health
```

**If backend works but proxy doesn't:**
```bash
# Check frontend logs
docker-compose logs frontend

# Restart frontend
docker-compose restart frontend
```

---

### Problem: Containers won't start

**Check container status:**
```bash
docker-compose ps
docker-compose logs
```

**Restart everything:**
```bash
docker-compose down
docker-compose up -d
```

---

## 📊 What Was Fixed

All these issues have been resolved:

✅ **Backend Error Handling**
- Returns proper HTTP status codes (200, 413, 503, 500)
- Structured JSON errors with error codes
- API key status in health check

✅ **Frontend Error Display**
- Specific messages for file size limits
- Clear guidance for missing API key
- Network error with troubleshooting steps

✅ **Environment Configuration**
- ANTHROPIC_API_KEY configured in .env
- Documentation in .env.example
- Network architecture documented

✅ **Testing**
- Automated test suite (test-api.sh)
- Deployment script (deploy.sh)
- curl examples in README

✅ **Documentation**
- Environment variables section
- Network architecture diagram
- Troubleshooting guide
- Expected API responses

---

## 📞 Need Help?

**View logs:**
```bash
docker-compose logs -f
```

**Run tests:**
```bash
./test-api.sh
```

**Check containers:**
```bash
docker-compose ps
docker stats
```

**Restart everything:**
```bash
docker-compose down
docker-compose up --build
```

---

## 🎉 Success Criteria

Your deployment is successful when:

✅ Health check returns `"status": "healthy"`
✅ Health check shows `"api_key_present": true`
✅ File upload returns `"success": true`
✅ Browser upload shows "Upload Successful!"
✅ Analysis returns compliance score and gaps

---

**All fixes are live! The upload should now work perfectly.** 🚀
