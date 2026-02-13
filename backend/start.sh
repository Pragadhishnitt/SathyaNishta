#!/bin/sh
set -e

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Setup storage buckets
echo "📦 Setting up storage buckets..."
python scripts/setup_storage.py

# Start application
echo "🚀 Starting FastAPI application..."
# Use exec to preserve signal handling
exec uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
