# RAG Legal Query Setup - Complete Guide

## What Was Implemented

The `rag_legal_query` tool in [compliance_agent.py](compliance_agent.py) now uses **semantic search** with Supabase pgvector on the `regulatory_docs` table instead of just calling the LLM.

## How It Works

1. **User query** → Converted to 1024-dimensional embedding using Cohere `embed-english-v3.0` model
2. **Vector search** → Supabase finds most similar documents using cosine similarity
3. **Source & category filtering** → Optional filter by source (SEBI, IndAS, CompaniesAct) and category
4. **Returns top_k** → Most relevant document chunks with relevance scores and full metadata

## Database Schema

The system uses the `regulatory_docs` table with the following structure:

- **id**: UUID primary key
- **title**: Document title (max 500 chars)
- **source**: Regulatory source (SEBI, IndAS, CompaniesAct)
- **category**: Document category (related_party, disclosure, insider_trading, etc.)
- **doc_type**: Type of document (regulation, circular, guideline)
- **content**: Full document text
- **content_chunk**: Chunked content for RAG (500 words)
- **embedding**: 1024-dimensional vector (Cohere embed-english-v3.0)
- **effective_date**: When the regulation became effective
- **url**: Source URL if available
- **metadata**: JSONB with additional info (chunk_number, word_count, etc.)
- **created_at**: Timestamp

## Setup Steps

### 1. Create the SQL Function in Supabase

Go to Supabase Dashboard → SQL Editor and run the contents of [supabase_rag_setup.sql](supabase_rag_setup.sql):

```sql
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
```

### 2. Create the Database Table

**Before running the script**, create the `regulatory_docs` table in Supabase:

Go to Supabase Dashboard → SQL Editor and run [create_regulatory_docs_table.sql](create_regulatory_docs_table.sql)

This creates:
- The `regulatory_docs` table with all required fields
- Indexes for source, category, and vector similarity search
- pgvector extension

### 3. Set Up Environment Variables

Ensure your `.env` file contains:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

Note: No API keys needed for embeddings - the script uses HuggingFace models locally.

### 4. Load Regulatory Documents

Run [rag_legal_database.py](rag_legal_database.py) to process all folders:

```bash
python3 backend/app/agents/compliance/rag_legal_database.py
```

The script automatically processes all three folders:
- **SEBI** documents (regulations and circulars)
- **IndAS** documents (accounting standards)
- **Companies Act** documents (statutory provisions)

What the script does:
- Extracts text from all PDF files in each folder
- Chunks content into 500-word segments
- Generates 384-dimensional embeddings using HuggingFace locally (no API needed)
- Stores in `regulatory_docs` table with full metadata

### 5. Test the RAG Query

```python
python3 backend/app/agents/compliance/compliance_agent.py
```

The test suite includes a RAG query example that searches for "disclosure requirements for related party transactions".

## Example Usage

```python
task = {
    "tool": "rag_legal_query",
    "params": {
        "query": "What are the disclosure requirements for related party transactions?",
        "source_filter": ["SEBI", "IndAS"],  # Optional: filter by source
        "category_filter": "related_party",  # Optional: filter by category
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
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "LODR_Regulations_2015",
      "source": "SEBI",
      "category": "related_party",
      "doc_type": "regulation",
      "content_chunk": "Related party transactions must be disclosed...",
      "effective_date": "2015-12-01",
      "url": "https://www.sebi.gov.in/...",
      "metadata": {
        "chunk_number": 5,
        "word_count": 487,
        "document": "LODR_Regulations_2015.pdf"
      },
      "relevance_score": 0.89
    }
  ]
}
```

## Key Features

✅ **Semantic search** - Finds relevant content by meaning, not just keywords
✅ **1024-dimensional embeddings** - Using Cohere's embed-english-v3.0 model
✅ **Processes all sources** - Automatically handles SEBI, IndAS, and Companies Act documents
✅ **Source filtering** - Filter by SEBI, IndAS, or CompaniesAct
✅ **Category filtering** - Filter by related_party, disclosure, insider_trading, etc.
✅ **Full metadata** - Complete document information including dates and URLs
✅ **Fast vector search** - Uses pgvector IVFFlat index for efficient similarity search
✅ **Schema compliant** - Matches the official regulatory_docs table structure

## Folder Structure

```
legal_docs/
├── sebi/           # SEBI regulations and circulars
├── indas/          # IndAS accounting standards
└── companies_act/  # Companies Act provisions
```

Each folder should contain PDF files that will be processed and stored in the `regulatory_docs` table.
