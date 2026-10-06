# syntax=docker/dockerfile:1

# ---------- Build stage ----------
FROM python:3.12-slim AS builder

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ---------- Production stage ----------
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd --system app && \
    useradd --system --gid app --home ${APP_HOME} --shell /bin/bash app

# Copy application code. Copy only what the image needs rather than the whole
# context: the repo root carries .venv, tests, k8s/ and frontend/ which bloat
# the image and shadow the installed package.
COPY --chown=app:app src/ ./src/

# The application is a src-layout package; make it importable without an
# editable install.
ENV PYTHONPATH=/app/src

# Switch to non-root user
USER app

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run uvicorn. The package is a src-layout module, so the import target is
# gated_communities.main:app (there is no top-level main.py in this repo).
CMD ["uvicorn", "gated_communities.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
