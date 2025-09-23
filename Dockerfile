# Multi-stage Dockerfile optimized for 8GB Cloud Run limit with reliable ML/Playwright support

# Stage 1: Build dependencies (reliable Debian-slim for SciPy/Scikit-learn)
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy pyproject.toml for dependency installation
COPY pyproject.toml ./

# Install dependencies to user directory (multi-stage size optimization)
RUN pip install --no-cache-dir --user --upgrade pip && \
    pip install --no-cache-dir --user .

# Stage 2: Minimal runtime (reliable with ML/Playwright compatibility)
FROM python:3.11-slim AS runtime

# Install only essential runtime dependencies (including ML library support)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq5 \
    libffi8 \
    libssl3 \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    zlib1g \
    libfreetype6 \
    libgfortran5 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r lotteryapp && useradd -r -g lotteryapp lotteryapp

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage (multi-stage optimization)
COPY --from=builder /root/.local /home/lotteryapp/.local

# Set environment variables optimized for Cloud Run
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=8080 \
    PATH=/home/lotteryapp/.local/bin:$PATH \
    PYTHONPATH=/home/lotteryapp/.local/lib/python3.11/site-packages:$PYTHONPATH

# Copy only essential application files (avoid copying heavy directories)
COPY app.py main.py models.py ./
COPY ai_lottery_predictor.py ai_lottery_processor.py ./
COPY neural_network_predictor.py probability_estimator.py ./
COPY prediction_validation_system.py fresh_prediction_generator.py ./
COPY backtesting_system.py lottery_analysis.py cache_manager.py scheduler_fix.py ./
COPY security_utils.py ./
COPY start_server.sh ./
COPY templates/ ./templates/
COPY static/ ./static/

# Make startup script executable and change ownership  
RUN chmod +x start_server.sh && \
    chown -R lotteryapp:lotteryapp /home/lotteryapp/.local /app
USER lotteryapp

# Expose port (Cloud Run will set PORT environment variable)
EXPOSE $PORT

# Lightweight health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=2 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/health')" || exit 1

# Smart startup script handles port detection automatically
CMD ["./start_server.sh"]