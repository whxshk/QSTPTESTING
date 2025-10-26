#!/bin/bash
set -e

echo "🚀 Starting backend service..."

# Clean any stale lock files from /tmp cache
echo "🧹 Cleaning any stale HuggingFace lock files from /tmp..."
find /tmp/huggingface -name "*.lock" -type f -delete 2>/dev/null || true
find /tmp/huggingface -name ".lock" -type f -delete 2>/dev/null || true

# Ensure /tmp cache directory has full permissions
echo "🔒 Setting /tmp cache directory permissions..."
chmod -R 777 /tmp/huggingface 2>/dev/null || true

# Verify model is cached
echo "📦 Verifying sentence transformer model is cached in /tmp..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('✅ Model loaded from /tmp cache')" || echo "⚠️ Model load failed, will retry on first request"

# Start gunicorn with 1 worker to avoid race conditions
echo "🌐 Starting Gunicorn with 1 worker (prevents race conditions)..."
exec gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout 120 --preload app:app
