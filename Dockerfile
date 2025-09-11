# Multi-stage Docker build for optimized South African Lottery Scanner

# Build stage
FROM python:3.11-slim as builder

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy minimal requirements for optimized build
COPY requirements-minimal.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Fix pyee package issue and install minimal dependencies
RUN pip install --upgrade pip && \
    pip install --force-reinstall --no-deps pyee==12.1.1 && \
    pip install --no-cache-dir -r requirements-minimal.txt

# Production stage
FROM python:3.11-slim as production

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=8080 \
    PATH="/opt/venv/bin:$PATH"

# Install minimal runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r lotteryapp && useradd -r -g lotteryapp lotteryapp

# Set working directory
WORKDIR /app

# Copy Python virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy only necessary application files (excluding assets via .dockerignore)
COPY --chown=lotteryapp:lotteryapp . .

# Switch to non-root user
USER lotteryapp

# Expose port
EXPOSE $PORT

# Health check with lightweight curl
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Optimized gunicorn configuration for Cloud Run
CMD exec gunicorn --bind 0.0.0.0:$PORT --timeout 60 --workers 1 --worker-class gthread --threads 4 --max-requests 1000 --max-requests-jitter 100 --preload --worker-tmp-dir /dev/shm main:app