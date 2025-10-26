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
ENV SENTENCE_TRANSFORMERS_HOME=/home/appuser/.cache/huggingface/sentence-transformers

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Create cache directories with FULL permissions to avoid any issues
RUN mkdir -p /home/appuser/.cache/huggingface/hub \
    /home/appuser/.cache/huggingface/transformers \
    /home/appuser/.cache/huggingface/datasets \
    /home/appuser/.cache/huggingface/sentence-transformers && \
    chown -R appuser:appuser /home/appuser && \
    chmod -R 777 /home/appuser/.cache

# Pre-download the sentence-transformers model as appuser (MUST succeed)
USER appuser
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('Model cached successfully!')"

# Set ownership of app directory
USER root
RUN chown -R appuser:appuser /app && chmod -R 755 /app

# Copy and set up startup script
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh && chown appuser:appuser /app/startup.sh

USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')"

# Use startup script to clean locks and start gunicorn with 1 worker (avoid race conditions)
CMD ["/app/startup.sh"]
