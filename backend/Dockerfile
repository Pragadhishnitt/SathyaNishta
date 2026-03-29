# ═══════════════════════════════════════════════════════════════
# STAGE 1: Builder — Install dependencies
# ═══════════════════════════════════════════════════════════════
FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency file first
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip==24.0 && \
    pip install --no-cache-dir --requirement requirements.txt

# ═══════════════════════════════════════════════════════════════
# STAGE 2: Runtime — Minimal image
# ═══════════════════════════════════════════════════════════════
FROM python:3.11-slim as production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app /app/app
# Copy alembic config
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set working directory to the app root so alembic finds app module
WORKDIR /app

# Ensure Python can find both /app (for app.*) and / (for contracts.*)
ENV PYTHONPATH="/app:/"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

# Default command
CMD ["./start.sh"]
