# 🎯 Port Architecture Explained

## Why Two Ports?

Your app uses **2 ports** for good architectural reasons:

---

## **Port 3000: Frontend (What Users See)**

**What it is**: Nginx web server hosting your React application

**What it serves**:
- HTML, CSS, JavaScript files
- The user interface (forms, buttons, dashboards)
- Static assets (images, fonts, etc.)

**What you see in browser**:
- ✅ Beautiful web interface
- ✅ Upload forms
- ✅ Analysis results dashboard
- ✅ Visual compliance scores

**Technology**: Nginx + React (Vite build)

---

## **Port 5000: Backend API (The Brain)**

**What it is**: Flask API server (Python)

**What it does**:
- 🔧 Processes uploaded DOCX/PDF files
- 🧠 Analyzes compliance using Claude AI
- 📊 Calculates scores and gaps
- 💾 Manages vector database (FAISS)
- 🔍 Searches regulations

**What you see in browser when you visit directly**:
- ❌ **Nothing useful!** (or 404/error)
- It's an **API server**, not a website
- Meant to receive **JSON requests**, not browser visits

**Technology**: Flask + Gunicorn + Python

---

## 🔄 How They Work Together

```
┌─────────────────────────────────────────────────┐
│  User's Browser                                 │
│  http://localhost:3000                          │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  Port 3000          │
        │  Frontend (Nginx)   │  ← You see this
        │  • Serves HTML/CSS  │
        │  • Shows UI         │
        └─────────┬───────────┘
                  │
                  │ When you upload a file...
                  │
                  ▼
        ┌─────────────────────┐
        │  Nginx Proxy        │
        │  /api/* requests    │
        └─────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │  Port 5000          │
        │  Backend (Flask)    │  ← You DON'T see this
        │  • Processes files  │
        │  • Runs AI analysis │
        │  • Returns JSON     │
        └─────────────────────┘
```

---

## 📋 Real Example

### What Happens When You Upload a DOCX:

1. **You visit**: `http://localhost:3000`
   - Frontend (port 3000) shows you the upload form

2. **You click upload**:
   - JavaScript sends request to: `/api/upload`
   - Nginx proxy forwards to: `http://backend:5000/upload`

3. **Backend (port 5000)**:
   - Receives the file
   - Extracts text
   - Creates embeddings
   - Stores in FAISS
   - Returns JSON: `{"success": true, "chunks": 45}`

4. **Frontend (port 3000)**:
   - Receives the JSON response
   - Shows you: "Upload Successful! 45 chunks indexed"

---

## 🧪 Testing Each Port

### Test Frontend (Port 3000):
```bash
curl http://localhost:3000
```
**Returns**: HTML page (the React app)

### Test Backend (Port 5000):
```bash
curl http://localhost:5000/health
```
**Returns**:
```json
{
  "status": "healthy",
  "api_key_present": true
}
```

---

## ❓ FAQ

### "Why not just use one port?"

**Separation of Concerns**:
- Frontend: User interface (React, HTML, CSS)
- Backend: Business logic (AI, database, file processing)

**Benefits**:
- ✅ Frontend can be rebuilt without touching backend
- ✅ Backend can be upgraded without changing UI
- ✅ Can scale independently (more backend servers if needed)
- ✅ Different technologies (React vs Python)

### "What if I only open port 3000?"

That's correct! You **only need port 3000**:
- Frontend handles all browser requests
- Nginx proxy forwards `/api/*` to backend internally
- Backend port 5000 is only needed for direct API testing

### "Can I use port 5000 directly?"

**For testing/debugging**: Yes!
```bash
# Upload directly to backend
curl -X POST -F "files=@file.docx" http://localhost:5000/upload

# Check health
curl http://localhost:5000/health
```

**For normal use**: No! Use the frontend at port 3000

---

## 🎯 Summary

| Port | Purpose | What You See | Technology |
|------|---------|--------------|------------|
| **3000** | Website | Beautiful UI | Nginx + React |
| **5000** | API Brain | JSON responses | Flask + Python |

**For users**: Just use http://localhost:3000 ✅

**Port 5000**: Only for developers/testing (API calls, not browser) 🔧

---

## 🔍 Why Port 5000 Shows Nothing in Browser

When you visit `http://localhost:5000` in a browser, you might see:
- **404 Not Found** - Because there's no route for `/`
- **Empty page** - Because it returns JSON, not HTML
- **Error** - If the backend is crashed

**This is normal!** The backend is an **API server**, not a website.

**To test it properly**, use curl or access through the frontend:
```bash
# ✅ Correct way to test backend
curl http://localhost:5000/health

# ❌ Wrong way
# Opening http://localhost:5000 in Chrome
```

---

**TL;DR**:
- **Port 3000** = Your website (use this)
- **Port 5000** = API brain (used by port 3000, not for browsers)
