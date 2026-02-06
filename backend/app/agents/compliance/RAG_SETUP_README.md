# RAG Legal Query Setup - Complete Guide

## What Was Implemented

The `rag_legal_query` tool in [compliance_agent2.py](compliance_agent2.py) now uses **semantic search** with Supabase pgvector instead of just calling the LLM.

## How It Works

1. **User query** → Converted to 384-dimensional embedding using `all-MiniLM-L6-v2`
2. **Vector search** → Supabase finds most similar documents using cosine similarity
3. **Source filtering** → Optional filter by SEBI, IndAS, or Companies_Act
4. **Returns top_k** → Most relevant document chunks with relevance scores

## Setup Steps

### 1. Create the SQL Function in Supabase

Go to Supabase Dashboard → SQL Editor and run the contents of [supabase_rag_setup.sql](supabase_rag_setup.sql):

```sql
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
```

### 2. Ensure Your Data is Loaded

Run [rag_legal_database.py](rag_legal_database.py) for each source:
- SEBI documents
- IndAS documents  
- Companies Act documents

### 3. Test the RAG Query

```python
python3 backend/app/agents/compliance/compliance_agent2.py
```

The test suite includes a RAG query example that searches for "disclosure requirements for related party transactions".

## Example Usage

```python
task = {
    "tool": "rag_legal_query",
    "params": {
        "query": "What are the disclosure requirements for related party transactions?",
        "source_filter": ["SEBI", "INDAS"],  # Optional: filter by source
        "top_k": 3  # Number of results
    }
}

result = agent.process(task)
```

## Output Format

```json
{
  "results": [
    {
      "document_id": "123",
      "title": "LODR_Regulations_2015.pdf",
      "source": "SEBI",
      "relevance_score": 0.89,
      "excerpt": "Related party transactions must be disclosed..."
    },
    ...
  ]
}
```

## Key Features

✅ **Semantic search** - Finds relevant content by meaning, not just keywords
✅ **Source filtering** - Filter by SEBI, IndAS, or Companies_Act
✅ **Fast vector search** - Uses pgvector index for efficient similarity search
✅ **Contract compliant** - Returns exact format specified in agent_tools.md
