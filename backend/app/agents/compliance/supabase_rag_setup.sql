-- Supabase SQL Setup for RAG Legal Query
-- Run this in Supabase SQL Editor to enable semantic search

-- Function to search legal documents by vector similarity
CREATE OR REPLACE FUNCTION search_legal_documents(
    query_embedding vector(384),
    match_count int DEFAULT 3,
    source_filter text[] DEFAULT NULL
)
RETURNS TABLE (
    id int,
    content text,
    source text,
    document text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        legal_documents.id,
        legal_documents.content,
        legal_documents.source,
        legal_documents.document,
        1 - (legal_documents.embedding <=> query_embedding) as similarity
    FROM legal_documents
    WHERE 
        CASE 
            WHEN source_filter IS NOT NULL THEN 
                legal_documents.source = ANY(source_filter)
            ELSE 
                true
        END
    ORDER BY legal_documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
