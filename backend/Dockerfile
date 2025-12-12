FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (required for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir -r requirements.txt && \
    # Remove unnecessary files to reduce image size
    find /usr/local/lib/python3.11/site-packages -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/site-packages -type d -name "test" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.11/site-packages -name "*.pyc" -delete && \
    find /usr/local/lib/python3.11/site-packages -name "*.pyo" -delete && \
    # Remove build dependencies
    apt-get purge -y --auto-remove build-essential

# Copy application
COPY app/ ./app/

# Copy data directory - contains templates and other data files
# Note: The data directory should contain templates/, tax_code/, and disputes/ subdirectories
# If building from backend/ context, ensure data/ is properly populated
# If building from root context with -f backend/Dockerfile, use data/ from root
COPY data/ ./data/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run with uvicorn
# Cloud Run sets PORT environment variable, default to 8000 for local dev
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
