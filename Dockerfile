# Cloud Run optimized Dockerfile for South African Lottery Scanner

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=8080

# Create non-root user for security
RUN groupadd -r lotteryapp && useradd -r -g lotteryapp lotteryapp

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy only the clean requirements file (no bloat/duplicates)
COPY requirements-clean.txt ./requirements.txt

# Install dependencies using optimized requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Change ownership to non-root user
RUN chown -R lotteryapp:lotteryapp /app

# Switch to non-root user
USER lotteryapp

# Expose port (Cloud Run will set the PORT environment variable)
EXPOSE $PORT

# Health check using wget (available in slim image) or python
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/health')" || exit 1

# Use gunicorn with configuration optimized for Cloud Run (single worker, more threads)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --worker-class gthread --threads 8 --timeout 120 main:app