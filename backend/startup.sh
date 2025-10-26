#!/bin/bash
set -e

echo "🚀 Starting backend service..."

# Clean any stale lock files from previous runs
echo "🧹 Cleaning any stale HuggingFace lock files..."
find /home/appuser/.cache/huggingface -name "*.lock" -type f -delete 2>/dev/null || true
find /home/appuser/.cache/huggingface -name ".lock" -type f -delete 2>/dev/null || true

# Ensure cache directory has correct permissions
echo "🔒 Setting cache directory permissions..."
chmod -R 777 /home/appuser/.cache 2>/dev/null || true

# Pre-load the model to ensure it's cached
echo "📦 Pre-loading sentence transformer model..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('✅ Model loaded from cache')" || echo "⚠️ Model load failed, will retry on first request"

# Start gunicorn with 1 worker to avoid race conditions
echo "🌐 Starting Gunicorn with 1 worker (prevents race conditions)..."
exec gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout 120 --preload app:app
