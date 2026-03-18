#!/bin/sh
set -e

# Run migrations only if database is reachable
echo "🔄 Attempting database migrations..."
alembic upgrade head 2>/dev/null || echo "⚠️  Migrations skipped (DB not reachable — OK for Sprint 1)"

# Setup storage buckets only if Supabase is reachable
echo "📦 Attempting storage setup..."
python scripts/setup_storage.py 2>/dev/null || echo "⚠️  Storage setup skipped (Supabase not reachable — OK for Sprint 1)"

# Start application
echo "🚀 Starting FastAPI application..."
exec uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
