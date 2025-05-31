# VirtuAI Office - Docker Configuration
# Multi-stage build for production deployment

# Stage 1: Frontend Build
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Backend Setup
FROM python:3.11-slim AS backend-base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production Image
FROM python:3.11-slim AS production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Create app user
RUN useradd -m -u 1000 virtuai && \
    mkdir -p /app /var/log/supervisor && \
    chown -R virtuai:virtuai /app

WORKDIR /app

# Copy Python dependencies
COPY --from=backend-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-base /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Copy configuration files
COPY manage.sh ./
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create necessary directories
RUN mkdir -p /app/data /app/models /app/logs && \
    chown -R virtuai:virtuai /app

# Environment variables
ENV PYTHONPATH=/app
ENV OLLAMA_HOST=0.0.0.0:11434
ENV OLLAMA_MODELS=/app/models
ENV DATABASE_URL=sqlite:///./data/virtuai_office.db
ENV NODE_ENV=production

# Expose ports
EXPOSE 3000 8000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/status || exit 1

# Switch to app user
USER virtuai

# Default command
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
