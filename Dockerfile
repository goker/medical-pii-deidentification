# Medical PII De-identification - Docker Image
# Supports both API and UI modes

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set work directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download model at build time (faster cold starts)
RUN python -c "from transformers import AutoTokenizer, AutoModelForTokenClassification; \
    AutoTokenizer.from_pretrained('OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1'); \
    AutoModelForTokenClassification.from_pretrained('OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1')"

# Copy application code
COPY src/ ./src/
COPY api/ ./api/
COPY ui/ ./ui/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose ports (API: 8000, UI: 7860)
EXPOSE 8000 7860

# Default to API mode
ENV MODE=api
ENV PORT=8000
ENV PRELOAD_MODEL=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || curl -f http://localhost:${PORT}/ || exit 1

# Start command (configurable via MODE env var)
CMD if [ "$MODE" = "ui" ]; then \
        python -m ui.app; \
    else \
        uvicorn api.main:app --host 0.0.0.0 --port ${PORT}; \
    fi
