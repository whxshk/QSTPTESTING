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

# Use /tmp for HuggingFace cache - ALWAYS writable, no permission issues
ENV HF_HOME=/tmp/huggingface
ENV TRANSFORMERS_CACHE=/tmp/huggingface/transformers
ENV HF_DATASETS_CACHE=/tmp/huggingface/datasets
ENV SENTENCE_TRANSFORMERS_HOME=/tmp/huggingface/sentence-transformers

# Create non-root user
RUN useradd -m -u 1000 appuser

# Create cache in /tmp with full permissions (anyone can write)
RUN mkdir -p /tmp/huggingface/hub \
    /tmp/huggingface/transformers \
    /tmp/huggingface/datasets \
    /tmp/huggingface/sentence-transformers && \
    chmod -R 777 /tmp/huggingface

# Copy application code
COPY . .

# Copy startup script and set executable permissions BEFORE switching user
RUN chmod +x /app/startup.sh

# Pre-download model to /tmp as appuser
USER appuser
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('✅ Model cached to /tmp successfully!')"

USER root
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Use startup script with bash explicitly
CMD ["bash", "/app/startup.sh"]
