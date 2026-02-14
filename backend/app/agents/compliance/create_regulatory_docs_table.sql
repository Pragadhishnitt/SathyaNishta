-- ==========================================
-- Create regulatory_docs table for RAG
-- Run this in Supabase SQL Editor
-- ==========================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop table if you want to recreate it (CAUTION: This deletes all data)
-- DROP TABLE IF EXISTS regulatory_docs CASCADE;

-- Create regulatory_docs table
CREATE TABLE IF NOT EXISTS regulatory_docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Document metadata
    title VARCHAR(500) NOT NULL,
    source VARCHAR(100) NOT NULL,  -- 'SEBI', 'IndAS', 'CompaniesAct'
    category VARCHAR(100),  -- 'related_party', 'disclosure', 'compliance'
    doc_type VARCHAR(50),  -- 'regulation', 'circular', 'guideline'
    
    -- Content
    content TEXT NOT NULL,  -- Full document text
    content_chunk TEXT,  -- Chunked content for RAG (500 words)
    
    -- Embedding for semantic search (1024 dimensions for Cohere embed-english-v3.0)
    embedding vector(1024),
    
    -- Metadata
    effective_date DATE,
    url TEXT,
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_source ON regulatory_docs(source);
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_category ON regulatory_docs(category);

-- Vector similarity search index (IVFFlat for performance)
-- Note: This index should be created AFTER data is loaded for better performance
CREATE INDEX IF NOT EXISTS idx_regulatory_docs_embedding ON regulatory_docs 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Verify table was created
SELECT 'regulatory_docs table created successfully!' AS status;
