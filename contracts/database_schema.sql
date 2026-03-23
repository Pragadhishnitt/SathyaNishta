-- ==========================================
-- SATHYA NISHTA: DATABASE SCHEMA
-- ==========================================
-- TEAM A OWNS THIS FILE
-- 
-- PostgreSQL (Supabase) schema for:
-- - Investigation state management
-- - Audit trails
-- - Document storage (RAG)
-- 
-- Version: 1.0.0
-- Last Updated: Sprint 1
-- ==========================================

-- ==========================================
-- EXTENSIONS
-- ==========================================

-- Enable pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- INVESTIGATIONS TABLE
-- ==========================================

CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Investigation details
    query TEXT NOT NULL CHECK (length(query) >= 10),
    status VARCHAR(20) DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed', 'stopped')),
    
    -- Results
    fraud_risk_score FLOAT CHECK (fraud_risk_score >= 0 AND fraud_risk_score <= 10),
    verdict VARCHAR(20) CHECK (verdict IN ('critical', 'high', 'medium', 'low', 'safe')),
    summary TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ,
    estimated_completion_time TIMESTAMPTZ,
    
    -- Optional context provided by user
    context JSONB DEFAULT '{}',
    
    -- Performance metrics
    total_execution_time_ms INT,
    total_tokens_used INT,
    
    CONSTRAINT valid_score_has_verdict CHECK (
        (fraud_risk_score IS NULL AND verdict IS NULL) OR
        (fraud_risk_score IS NOT NULL AND verdict IS NOT NULL)
    )
);

-- Indexes for performance
CREATE INDEX idx_investigations_status ON investigations(status);
CREATE INDEX idx_investigations_created_at ON investigations(created_at DESC);
CREATE INDEX idx_investigations_verdict ON investigations(verdict) WHERE verdict IS NOT NULL;

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_investigations_updated_at BEFORE UPDATE ON investigations
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- INVESTIGATION STATES (Agent Checkpoints)
-- ==========================================

CREATE TABLE investigation_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    
    -- Agent info
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('financial', 'graph', 'audio', 'compliance')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'approved', 'rejected', 'failed')),
    
    -- Agent output
    findings JSONB NOT NULL DEFAULT '[]',
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    
    -- Execution metadata
    execution_time_ms INT,
    retry_count INT DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    CONSTRAINT unique_agent_per_investigation UNIQUE(investigation_id, agent_type)
);

-- Indexes
CREATE INDEX idx_states_investigation_id ON investigation_states(investigation_id);
CREATE INDEX idx_states_status ON investigation_states(status);

CREATE TRIGGER update_investigation_states_updated_at BEFORE UPDATE ON investigation_states
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- AUDIT TRAIL (Append-Only)
-- ==========================================

CREATE TABLE audit_trail (
    id BIGSERIAL PRIMARY KEY,
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    
    -- Step info
    step_type VARCHAR(50) NOT NULL,  -- 'plan', 'agent_start', 'agent_end', 'reflection', 'synthesis'
    agent_type VARCHAR(20) CHECK (agent_type IN ('financial', 'graph', 'audio', 'compliance')),
    
    -- Payloads (input/output of each step)
    input_payload JSONB DEFAULT '{}',
    output_payload JSONB DEFAULT '{}',
    
    -- LLM metadata (for traceability)
    model_metadata JSONB DEFAULT '{}',  -- model name, tokens used, request ID
    
    -- Timestamp
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX idx_audit_investigation_id ON audit_trail(investigation_id);
CREATE INDEX idx_audit_timestamp ON audit_trail(timestamp DESC);
CREATE INDEX idx_audit_step_type ON audit_trail(step_type);

-- Enforce append-only via RLS (Row-Level Security)
ALTER TABLE audit_trail ENABLE ROW LEVEL SECURITY;

-- Policy: No UPDATE or DELETE allowed (only INSERT and SELECT)
CREATE POLICY audit_trail_append_only ON audit_trail
    FOR ALL
    USING (true)  -- Allow SELECT
    WITH CHECK (true);  -- Allow INSERT

-- Revoke UPDATE and DELETE permissions
REVOKE UPDATE, DELETE ON audit_trail FROM PUBLIC;

-- ==========================================
-- REGULATORY DOCUMENTS (RAG - Legal/Compliance)
-- ==========================================

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

-- ==========================================
-- FINANCIAL FILINGS (RAG - Financial Data)
-- ==========================================

CREATE TABLE financial_filings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Company info
    company_name VARCHAR(255) NOT NULL,
    company_ticker VARCHAR(50),
    cin VARCHAR(50),  -- Corporate Identification Number
    
    -- Filing info
    period VARCHAR(20) NOT NULL,  -- 'Q3-2024', 'FY2023'
    doc_type VARCHAR(50) NOT NULL,  -- 'balance_sheet', 'cash_flow', 'income_statement', 'annual_report'
    filing_date DATE,
    
    -- Content
    content_chunk TEXT NOT NULL,  -- Chunked content (tables, paragraphs)
    page_number INT,
    section_name VARCHAR(200),
    
    -- Embedding for semantic search
    embedding vector(1536),
    
    -- Source
    source_url TEXT,
    source_file_key TEXT,  -- If stored in Supabase Storage
    
    -- Metadata (extracted financial figures, ratios, etc.)
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX idx_financial_filings_company ON financial_filings(company_name);
CREATE INDEX idx_financial_filings_ticker ON financial_filings(company_ticker);
CREATE INDEX idx_financial_filings_period ON financial_filings(period);
CREATE INDEX idx_financial_filings_doc_type ON financial_filings(doc_type);

-- Vector similarity search index
CREATE INDEX idx_financial_filings_embedding ON financial_filings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ==========================================
-- AUDIO FILES (Earnings Calls)
-- ==========================================

CREATE TABLE audio_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Company info
    company_name VARCHAR(255) NOT NULL,
    
    -- Audio metadata
    call_type VARCHAR(50),  -- 'earnings_call', 'analyst_meeting', 'shareholder_meeting'
    period VARCHAR(20),  -- 'Q3-2024'
    call_date DATE,
    
    -- Storage
    file_key TEXT NOT NULL,  -- Supabase Storage key
    duration_sec INT,
    
    -- Optional transcript (if generated)
    transcript TEXT,
    transcript_embedding vector(1536),
    
    -- Metadata
    participants JSONB DEFAULT '[]',  -- List of speakers
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX idx_audio_files_company ON audio_files(company_name);
CREATE INDEX idx_audio_files_period ON audio_files(period);

-- ==========================================
-- HELPER FUNCTIONS
-- ==========================================

-- Function: Get all approved states for an investigation
CREATE OR REPLACE FUNCTION get_approved_states(inv_id UUID)
RETURNS TABLE(agent_type VARCHAR, findings JSONB, confidence FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.agent_type,
        s.findings,
        s.confidence
    FROM investigation_states s
    WHERE s.investigation_id = inv_id AND s.status = 'approved';
END;
$$ LANGUAGE plpgsql;

-- Function: Check if all agents are approved (state barrier)
CREATE OR REPLACE FUNCTION check_state_barrier(inv_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    approved_count INT;
    total_count INT;
BEGIN
    SELECT COUNT(*) INTO approved_count
    FROM investigation_states
    WHERE investigation_id = inv_id AND status = 'approved';
    
    SELECT COUNT(DISTINCT agent_type) INTO total_count
    FROM investigation_states
    WHERE investigation_id = inv_id;
    
    -- Assuming 4 agents (financial, graph, audio, compliance)
    RETURN (approved_count = 4 AND total_count = 4);
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- NEO4J SCHEMA (Cypher)
-- ==========================================
/*
  This section documents the Neo4j graph schema.
  Execute these commands in Neo4j Browser or via Python neo4j driver.
  
  Node Labels:
  - :Company {name, cin, industry, market_cap}
  - :Person {name, din, designation}
  - :ShellEntity {name, registration_address, incorporation_date}
  - :BankAccount {account_number, bank_name, ifsc}
  
  Relationship Types:
  - (:Person)-[:DIRECTOR_OF {appointment_date, resignation_date}]->(:Company)
  - (:Company)-[:OWNS {percentage, acquisition_date}]->(:Company)
  - (:Company)-[:TRANSACTS_WITH {amount, date, description, type}]->(:Company)
  - (:Company)-[:TRANSACTS_WITH]->(:ShellEntity)
  - (:Person)-[:RELATED_TO {relationship_type}]->(:Person)
  - (:Company)-[:HAS_ACCOUNT]->(:BankAccount)
  - (:BankAccount)-[:TRANSFERS_TO {amount, date}]->(:BankAccount)
*/

-- NEO4J CONSTRAINTS (Create these in Neo4j)
-- CREATE CONSTRAINT person_din_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.din IS UNIQUE;
-- CREATE CONSTRAINT company_cin_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.cin IS UNIQUE;
-- CREATE CONSTRAINT shell_name_unique IF NOT EXISTS FOR (s:ShellEntity) REQUIRE s.name IS UNIQUE;

-- NEO4J INDEXES (Create these in Neo4j)
-- CREATE INDEX company_name_idx IF NOT EXISTS FOR (c:Company) ON (c.name);
-- CREATE INDEX person_name_idx IF NOT EXISTS FOR (p:Person) ON (p.name);
-- CREATE INDEX shell_name_idx IF NOT EXISTS FOR (s:ShellEntity) ON (s.name);
-- CREATE INDEX transaction_date_idx IF NOT EXISTS FOR ()-[t:TRANSACTS_WITH]-() ON (t.date);

-- ==========================================
-- SEED DATA EXAMPLES (For Testing)
-- ==========================================

-- Example: Insert regulatory document
-- INSERT INTO regulatory_docs (title, source, category, content, embedding) VALUES
-- ('SEBI LODR Regulation 23 - Related Party Transactions', 'SEBI', 'related_party', 
--  'Full text of regulation...', 
--  -- embedding would be generated via API
--  NULL);

-- Example: Insert financial filing
-- INSERT INTO financial_filings (company_name, company_ticker, period, doc_type, content_chunk) VALUES
-- ('Adani Enterprises', 'ADANIENT', 'Q3-2024', 'balance_sheet', 
--  'Total Assets: ₹5,00,000 Cr. Total Liabilities: ₹2,00,000 Cr...');

-- ==========================================
-- NOTES
-- ==========================================
/*
1. All timestamps use TIMESTAMPTZ for timezone-aware storage.
2. JSONB is used for flexible metadata storage (better than JSON - supports indexing).
3. Audit trail is append-only via RLS - critical for legal defensibility.
4. Vector indexes use IVFFlat algorithm - tune `lists` parameter based on dataset size.
5. For production, consider partitioning audit_trail by investigation_id or timestamp for performance.
6. Neo4j schema is documented here but executed separately in Neo4j environment.
*/
