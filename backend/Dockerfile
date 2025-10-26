FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set HuggingFace cache directory
ENV HF_HOME=/home/appuser/.cache/huggingface
ENV TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface/transformers
ENV HF_DATASETS_CACHE=/home/appuser/.cache/huggingface/datasets

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Create cache directories with proper permissions
RUN mkdir -p /home/appuser/.cache/huggingface/hub \
    /home/appuser/.cache/huggingface/transformers \
    /home/appuser/.cache/huggingface/datasets && \
    chown -R appuser:appuser /home/appuser/.cache && \
    chmod -R 755 /home/appuser/.cache

# Pre-download the sentence-transformers model as appuser to avoid runtime permission issues
USER appuser
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" || \
    echo "Model download failed, will retry at runtime"

# Set ownership of app directory
USER root
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
