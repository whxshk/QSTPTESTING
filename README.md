# Fintech Regulatory Readiness Platform

A comprehensive AI-powered platform for analyzing fintech startup compliance against Qatar Central Bank (QCB) regulatory requirements. Built for the AIX Hackathon.

![Platform Overview](https://img.shields.io/badge/Status-Production%20Ready-green) ![Python](https://img.shields.io/badge/Python-3.11-blue) ![React](https://img.shields.io/badge/React-18-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

> **📋 Template Platform**: This is a generic, reusable platform designed to work with **any fintech startup or financial services company**. Simply upload your own business plan, legal structure, compliance policies, and regulatory documents to get a customized compliance analysis. No company-specific configuration required.

## 🎯 Overview

This platform enables fintech startups to:

- **Upload** business documents (DOCX/PDF) including business plans, compliance policies, legal structures
- **Analyze** compliance automatically using Claude AI and RAG (Retrieval-Augmented Generation)
- **Identify** regulatory gaps between startup materials and QCB licensing rules
- **Receive** a readiness score (0-100) with detailed gap analysis
- **Get matched** with QDB programs and compliance experts to close gaps

## 🏗️ Architecture

### Backend
- **Framework**: Flask with CORS support
- **AI**: Claude 3.5 Sonnet API for intelligent gap analysis
- **Vector Search**: FAISS with sentence-transformers (all-MiniLM-L6-v2)
- **Document Processing**: docx2txt (DOCX) and pypdf (PDF) with intelligent chunking
- **Scoring**: Transparent algorithm (100 base - 35/high - 20/medium - 10/low)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite for fast development
- **Styling**: TailwindCSS with custom design system
- **Icons**: Lucide React
- **File Upload**: react-dropzone with drag-and-drop

### Deployment
- **Containerization**: Docker + Docker Compose
- **Backend Server**: Gunicorn with 2 workers
- **Frontend Server**: Nginx with optimized caching and proxy

## 📁 Project Structure

```
fintech-regulatory-readiness/
├── backend/
│   ├── app.py                 # Flask API endpoints
│   ├── rag.py                 # Document processing & vector search
│   ├── rules.py               # QCB regulatory rules management
│   ├── scoring.py             # Compliance scoring algorithm
│   ├── recommender.py         # Recommendation engine
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Backend container config
│   ├── .env.example          # Environment variables template
│   └── data/
│       ├── rules.json        # QCB regulatory requirements
│       └── resources.json    # QDB programs & experts
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx    # Home page
│   │   │   ├── UploadPage.tsx     # Document upload
│   │   │   ├── SummaryPage.tsx    # Startup description
│   │   │   └── ResultsPage.tsx    # Analysis dashboard
│   │   ├── App.tsx           # Main application component
│   │   ├── api.ts            # API client with TypeScript types
│   │   ├── main.tsx          # React entry point
│   │   └── index.css         # TailwindCSS styles
│   ├── package.json          # Node dependencies
│   ├── Dockerfile            # Frontend container config
│   ├── nginx.conf            # Nginx configuration
│   └── tailwind.config.js    # TailwindCSS configuration
├── sample-documents/         # Example documents for testing (fictional company)
│   ├── SAMPLE-BUSINESS-PLAN.txt
│   └── SAMPLE-COMPLIANCE-POLICY.txt
├── docker-compose.yml        # Multi-container orchestration
├── .env.example              # Root environment template
└── README.md                 # This file
```

**Note**: The `sample-documents/` folder contains fictional example documents for testing purposes. The platform works with any company's actual documents - simply upload your own files.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional, for containerized deployment)
- Anthropic API Key ([Get one here](https://console.anthropic.com/))

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fintech-regulatory-readiness
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   **Edit `.env` and set your ANTHROPIC_API_KEY**:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here...
   PORT=5000
   FLASK_DEBUG=False
   VITE_API_URL=/api
   ```

   > **Important**: The ANTHROPIC_API_KEY is **required** for the `/analyze` endpoint. Get your API key from [Anthropic Console](https://console.anthropic.com/). The `/upload` endpoint will work without it.

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the platform**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000 (direct) or http://localhost:3000/api (via nginx proxy)
   - Health Check: http://localhost:5000/health or http://localhost:3000/api/health

5. **Run automated tests** (optional)
   ```bash
   ./test-api.sh
   ```

### Option 2: Manual Development Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

5. **Run the server**
   ```bash
   python app.py
   # Or with Flask CLI:
   flask run --port 5000
   ```

   The backend will be available at http://localhost:5000

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Verify VITE_API_URL=http://localhost:5000
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

   The frontend will be available at http://localhost:3000

## 📚 API Documentation

### Endpoints

#### `POST /upload`
Upload and index documents for analysis.

**Request**: `multipart/form-data` with files
**Response**:
```json
{
  "success": true,
  "message": "Successfully indexed 4 files",
  "chunks_indexed": 142,
  "files_processed": 4,
  "embedding_dimension": 384
}
```

#### `POST /analyze`
Analyze startup compliance against QCB regulations.

**Request**:
```json
{
  "summary": "P2P lending platform, QAR 5M capital, data in Ireland..."
}
```

**Response**:
```json
{
  "success": true,
  "score": 45,
  "grade": "F",
  "category": "Limited Readiness",
  "needs_expert_review": true,
  "gaps": [
    {
      "title": "Data Residency Non-Compliance",
      "rule_ref": "QCB 2.1.1",
      "evidence": "Data hosted in Ireland and Singapore",
      "explanation": "QCB requires data to be stored in Qatar",
      "severity": "high"
    }
  ],
  "recommendations": [
    {
      "gap_title": "Data Residency Non-Compliance",
      "programs": [...],
      "experts": [...]
    }
  ]
}
```

#### `GET /health`
Health check endpoint.

#### `GET /rules`
Get all QCB regulatory rules.

#### `GET /resources`
Get all QDB programs and compliance experts.

#### `POST /clear`
Clear indexed documents.

## 🧪 Testing the Platform

### Test Flow

1. **Start the application** (either Docker or manual setup)

2. **Navigate to the landing page** (http://localhost:3000)

3. **Click "Upload Documents & Start Analysis"**

4. **Upload test documents**:
   - Upload 2-4 DOCX or PDF files
   - These should represent: business plan, compliance policy, legal structure, etc.
   - Or use the provided mock documents in the repository

5. **Click "Upload & Process"**
   - Wait for success message
   - Should show "X chunks indexed"

6. **Click "Continue to Summary"**

7. **Enter startup description** or click "Use Example":
   ```
   P2P lending platform, paid-up capital QAR 5,000,000,
   data hosted in Ireland and Singapore, no dedicated
   Compliance Officer, AML policy drafted but not board-approved
   ```

8. **Click "Analyze Compliance"**
   - Wait 10-30 seconds for AI analysis

9. **Review results**:
   - Readiness score (e.g., 45/100)
   - Compliance gaps with severity levels
   - Recommended QDB programs
   - Matched compliance experts

10. **Download report** for offline review

### Automated Testing with test-api.sh

Run the comprehensive test suite:
```bash
./test-api.sh
```

This script tests:
- Backend health check
- Frontend nginx proxy
- File upload (direct and via proxy)
- Compliance analysis
- File size limits
- CORS headers

### Manual Testing with cURL

**Health check (backend direct)**:
```bash
curl -i http://localhost:5000/health
```

**Health check (via frontend proxy)**:
```bash
curl -i http://localhost:3000/api/health
```

**Upload documents (direct to backend)**:
```bash
curl -i -X POST http://localhost:5000/upload \
  -F "files=@2. Mock Startup Business Plan (Input Document).docx" \
  -F "files=@4. Mock Startup Internal Compliance Policy.docx"
```

**Upload documents (via frontend proxy)**:
```bash
curl -i -X POST http://localhost:3000/api/upload \
  -F "files=@6. Mock Startup Legal Structure Document.docx"
```

**Analyze compliance**:
```bash
curl -i -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "P2P lending platform, paid-up capital QAR 5,000,000, data hosted in Ireland and Singapore, no dedicated Compliance Officer, AML policy drafted but not board-approved"
  }'
```

### Expected Responses

**Health Check (200 OK)**:
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

**Upload Success (200 OK)**:
```json
{
  "success": true,
  "message": "Successfully indexed 1 files",
  "chunks_indexed": 45,
  "files_processed": 1,
  "embedding_dimension": 384
}
```

**File Too Large (413 Payload Too Large)**:
```json
{
  "error": "File too large. Maximum size is 50MB per file.",
  "code": "FILE_TOO_LARGE",
  "max_size_mb": 50
}
```

**Missing API Key (503 Service Unavailable)**:
```json
{
  "error": "AI analysis not configured. Please set ANTHROPIC_API_KEY environment variable.",
  "requires_api_key": true,
  "code": "MISSING_API_KEY"
}
```

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ANTHROPIC_API_KEY` | API key for Claude AI (get from [Anthropic Console](https://console.anthropic.com/)) | None | **Yes** (for `/analyze` endpoint) |
| `PORT` | Backend server port | `5000` | No |
| `FLASK_DEBUG` | Enable Flask debug mode | `False` | No |
| `VITE_API_URL` | Frontend API base URL | `/api` | No |

### Environment Configuration Files

- **Root `.env`**: Used by Docker Compose to pass variables to containers
- **`backend/.env`**: Used for local backend development
- **`frontend/.env`**: Used for local frontend development

### Docker Deployment

When using Docker Compose, only the root `.env` file is needed:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...your-key...
PORT=5000
FLASK_DEBUG=False
VITE_API_URL=/api
```

Docker Compose will automatically:
- Pass `ANTHROPIC_API_KEY` to the backend container
- Set `PORT=5000` for the backend
- Set `VITE_API_URL=/api` for the frontend (uses nginx proxy)

### Local Development

For local development without Docker:

**Backend** (`backend/.env`):
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...your-key...
PORT=5000
FLASK_DEBUG=True
MAX_UPLOAD_SIZE_MB=50
```

**Frontend** (`frontend/.env`):
```bash
VITE_API_URL=http://localhost:5000
```

## 🌐 Network Architecture

### Docker Network Flow

```
User Browser
    ↓
http://localhost:3000 (Frontend Container - nginx)
    ↓
/api/* requests → nginx proxy
    ↓
http://backend:5000 (Backend Container - Flask)
    ↓
Docker Bridge Network
```

### Port Mapping

| Service | Container Port | Host Port | Access |
|---------|---------------|-----------|---------|
| Frontend (nginx) | 80 | 3000 | http://localhost:3000 |
| Backend (Flask) | 5000 | 5000 | http://localhost:5000 |

### API Access Methods

1. **Via Frontend Proxy** (Recommended for browser):
   - `http://localhost:3000/api/health`
   - `http://localhost:3000/api/upload`
   - `http://localhost:3000/api/analyze`

2. **Direct Backend** (For testing/debugging):
   - `http://localhost:5000/health`
   - `http://localhost:5000/upload`
   - `http://localhost:5000/analyze`

### CORS Configuration

The backend is configured with CORS to allow all origins:
```python
CORS(app, resources={r"/*": {"origins": "*"}})
```

For production, restrict origins:
```python
CORS(app, resources={r"/*": {"origins": "https://yourdomain.com"}})
```

## 🔧 Troubleshooting

### Upload Issues

**Problem**: "Upload Failed – Network Error"
- **Cause**: Frontend cannot reach backend server
- **Diagnosis**:
  ```bash
  # Test backend health directly
  curl http://localhost:5000/health

  # Test via frontend proxy
  curl http://localhost:3000/api/health
  ```
- **Solutions**:
  1. Ensure backend is running: `docker ps` or check backend logs
  2. Verify `.env` has correct API base URL: `VITE_API_URL=/api`
  3. Check frontend `src/api.ts` uses correct base URL
  4. Rebuild frontend if env changed: `docker-compose up --build frontend`

**Problem**: Files upload but show 0 chunks indexed
- **Cause**: Files may be image-based PDFs without text
- **Solution**: Use text-based documents or implement OCR (pytesseract)

**Problem**: "No text could be extracted" error
- **Cause**: Unsupported file format or corrupted files
- **Solution**: Verify files are valid DOCX/PDF, try different files

**Problem**: "File too large" error (413)
- **Cause**: File exceeds 50MB limit
- **Solution**: Split large files or increase `MAX_CONTENT_LENGTH` in `backend/app.py`

### Analysis Issues

**Problem**: "AI analysis not configured" error
- **Cause**: Missing ANTHROPIC_API_KEY
- **Solution**: Check `.env` file and ensure key is set correctly

**Problem**: Analysis times out
- **Cause**: Large documents or slow API response
- **Solution**: Increase timeout in `app.py` or reduce document size

**Problem**: Analysis returns empty gaps
- **Cause**: Documents show full compliance or AI couldn't find issues
- **Solution**: Try example summary with known gaps

### CORS Issues

**Problem**: Frontend can't reach backend (CORS errors)
- **Cause**: CORS not enabled or wrong origin
- **Solution**: Verify `flask-cors` is installed and configured in `app.py`

### Docker Issues

**Problem**: Container fails to start
- **Cause**: Port already in use or missing dependencies
- **Solution**:
  ```bash
  docker-compose down
  docker-compose up --build --force-recreate
  ```

**Problem**: Backend shows "unhealthy" status
- **Cause**: Claude API key not set or unreachable
- **Solution**: Check logs with `docker-compose logs backend`

## 🎨 Customization

### Adding New Rules

Edit `backend/data/rules.json`:
```json
{
  "ref": "QCB X.X.X",
  "title": "New Requirement",
  "text": "Description of the requirement..."
}
```

### Adding Programs/Experts

Edit `backend/data/resources.json` to add new QDB programs or experts.

### Modifying Scoring

Edit `backend/scoring.py` to adjust severity weights:
```python
SEVERITY_WEIGHTS = {
    "high": 35,    # Modify these values
    "medium": 20,
    "low": 10
}
```

### Customizing UI

- Colors: Edit `frontend/tailwind.config.js`
- Components: Modify files in `frontend/src/pages/` and `frontend/src/components/`
- Styling: Update `frontend/src/index.css`

## 📊 System Requirements

### Development
- **CPU**: 2+ cores
- **RAM**: 4GB minimum
- **Storage**: 2GB free space
- **Network**: Stable internet for API calls

### Production
- **CPU**: 4+ cores recommended
- **RAM**: 8GB recommended
- **Storage**: 5GB free space
- **Network**: 10Mbps+ for concurrent users

## 🔐 Security Considerations

- Documents are processed **in-memory only** and not stored permanently
- API keys should be kept in `.env` and never committed
- CORS is enabled for development; configure properly for production
- Consider adding authentication/authorization for production deployments
- Use HTTPS in production environments

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for the **AIX Hackathon** - Qatar's Fintech Ecosystem
- Powered by **Anthropic Claude** AI
- QCB regulatory framework (simulated for demo purposes)
- QDB programs and expert database (mock data for demonstration)

## 📞 Support

For issues, questions, or feedback:
- Open an issue on GitHub
- Contact the development team
- Review the troubleshooting section above

---

**Note**: This platform is for informational purposes only. For official regulatory guidance, consult with legal and compliance professionals and refer to official QCB documentation.
