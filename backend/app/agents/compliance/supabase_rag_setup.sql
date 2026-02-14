-- Supabase SQL Setup for RAG Legal Query
-- Run this in Supabase SQL Editor to enable semantic search on regulatory_docs table

-- Function to search regulatory documents by vector similarity
CREATE OR REPLACE FUNCTION search_regulatory_documents(
    query_embedding vector(1024),
    match_count int DEFAULT 3,
    source_filter text[] DEFAULT NULL,
    category_filter text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    title varchar(500),
    source varchar(100),
    category varchar(100),
    doc_type varchar(50),
    content_chunk text,
    effective_date date,
    url text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        regulatory_docs.id,
        regulatory_docs.title,
        regulatory_docs.source,
        regulatory_docs.category,
        regulatory_docs.doc_type,
        regulatory_docs.content_chunk,
        regulatory_docs.effective_date,
        regulatory_docs.url,
        regulatory_docs.metadata,
        1 - (regulatory_docs.embedding <=> query_embedding) as similarity
    FROM regulatory_docs
    WHERE 
        (source_filter IS NULL OR regulatory_docs.source = ANY(source_filter))
        AND (category_filter IS NULL OR regulatory_docs.category = category_filter)
    ORDER BY regulatory_docs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
