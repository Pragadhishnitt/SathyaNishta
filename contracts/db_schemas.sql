-- Shared SQL Schemas for Supabase/Postgres

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
