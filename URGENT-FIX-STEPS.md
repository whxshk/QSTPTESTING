# 🚨 URGENT FIX FOR API KEY ISSUE

## The Problem
The backend can't find the ANTHROPIC_API_KEY, causing uploads to work but analysis to fail.

---

## Quick Fix (2 Minutes)

### Option 1: Directly Edit docker-compose.yml (Fastest)

On **your machine** where Docker is running:

1. **Open docker-compose.yml** in an editor

2. **Find this section** (around line 11-14):
```yaml
environment:
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  - PORT=5000
  - FLASK_DEBUG=False
```

3. **Replace it with** (use the API key from .env file):
```yaml
environment:
  - ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
  - PORT=5000
  - FLASK_DEBUG=False
```
*(Replace with the actual key from your `.env` file)*

4. **Restart the backend**:
```bash
docker-compose restart backend
```

5. **Verify it worked**:
```bash
docker-compose logs backend | grep -i anthropic
```

You should see: `Anthropic client initialized successfully` ✅

---

### Option 2: Use Environment Variable (More Secure)

1. **Export the API key** in your terminal:
```bash
export ANTHROPIC_API_KEY="your-api-key-from-dot-env-file"
```
*(Use the actual key from your `.env` file)*

2. **Restart containers**:
```bash
docker-compose down
docker-compose up -d
```

3. **Verify**:
```bash
curl http://localhost:5000/health | jq '.api_key_present'
```

Should return: `true` ✅

---

### Option 3: Pull Latest Fix

I've updated docker-compose.yml to use `env_file` directive:

```bash
git pull origin claude/debug-docx-upload-error-011CUTsTebY7fdqoUHZ5ArHg
docker-compose down
docker-compose up -d
```

---

## Verify the Fix

After applying any option above:

### 1. Check backend logs:
```bash
docker-compose logs backend | tail -20
```

**Look for**:
- ✅ `Anthropic client initialized successfully`
- ❌ `ANTHROPIC_API_KEY not found` (should NOT appear)

### 2. Test health endpoint:
```bash
curl http://localhost:5000/health
```

**Should return**:
```json
{
  "status": "healthy",
  "claude_configured": true,
  "api_key_present": true  ← This should be TRUE
}
```

### 3. Test upload in browser:

1. Go to http://localhost:3000
2. Upload a DOCX file
3. You should see "Upload Successful!" ✅

---

## Why Did This Happen?

Docker Compose was trying to read `${ANTHROPIC_API_KEY}` from the environment, but:
- The `.env` file wasn't being picked up properly
- Environment variable wasn't exported in the shell

**The fix**: Either hardcode it in docker-compose.yml (fast) or use `env_file` directive (cleaner).

---

## Still Getting "Network Error"?

If upload still fails after fixing the API key:

### Check if backend is responding:
```bash
curl http://localhost:5000/health
```

### Check if frontend proxy works:
```bash
curl http://localhost:3000/api/health
```

### View logs:
```bash
# Backend logs
docker-compose logs backend

# Frontend logs
docker-compose logs frontend
```

### Common fixes:
```bash
# Full restart
docker-compose down
docker-compose up -d

# Rebuild if needed
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Expected Workflow After Fix

1. ✅ Backend starts: "Anthropic client initialized successfully"
2. ✅ Health check: `"api_key_present": true`
3. ✅ Upload DOCX: "Upload Successful!"
4. ✅ Analyze: Returns compliance score and gaps

---

**TL;DR**: Edit docker-compose.yml line 12, paste your API key, run `docker-compose restart backend`. Done! 🚀
