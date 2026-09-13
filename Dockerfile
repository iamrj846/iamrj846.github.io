# ==============================================================================
# CorporateGuild - Production Multi-Architecture Dockerfile
# Python 3.11 Slim on Debian Bookworm (Compatible with x86_64 and ARM64 / Ampere)
# ==============================================================================

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

# Install required system runtime dependencies:
# - curl: required for container healthcheck pings
# - sqlite3: required for safe online SQLite database backups and integrity verification
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set IST timezone inside container
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install Python dependencies first (leverage Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create runtime persistent storage directories
RUN mkdir -p /app/data /app/logs /app/resources /app/backups

# Copy application source code and assets
COPY app/ /app/app/
COPY frontend/ /app/frontend/
COPY resources/ /app/resources/
COPY scripts/ /app/scripts/
COPY application.yml /app/application.yml

# Ensure helper scripts have executable permissions
RUN chmod +x /app/scripts/*.sh

# Expose FastAPI HTTP port
EXPOSE 8000

# Health check to ensure Uvicorn is serving requests
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/auth/me || exit 1

# Launch production server with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
