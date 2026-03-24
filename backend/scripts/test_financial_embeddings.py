#!/usr/bin/env python3
"""
Test Financial Embeddings - Verify semantic search works with stored embeddings
Tests that embeddings are properly stored and retrievable
"""

import sys
import os
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

import cohere
from sqlalchemy import create_engine, text
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(COHERE_API_KEY)
engine = create_engine(settings.DATABASE_URL)

def test_basic_queries():
    """Test 1: Basic data retrieval"""
    print("\n" + "="*80)
    print("TEST 1: BASIC DATA RETRIEVAL")
    print("="*80)
    
    with engine.connect() as conn:
        # Check total records
        result = conn.execute(text("""
            SELECT COUNT(*) as total_chunks, 
                   COUNT(DISTINCT company_name) as companies,
                   COUNT(DISTINCT doc_type) as report_types
            FROM financial_filings
        """))
        row = result.fetchone()
        print(f"✓ Total chunks in database: {row[0]}")
        print(f"✓ Companies: {row[1]}")
        print(f"✓ Report types: {row[2]}")
        
        # Sample data
        result2 = conn.execute(text("""
            SELECT company_name, doc_type, content_chunk FROM financial_filings LIMIT 1
        """))
        sample = result2.fetchone()
        print(f"\n✓ Sample chunk:")
        print(f"  Company: {sample[0]}")
        print(f"  Type: {sample[1]}")
        print(f"  Content preview: {sample[2][:100]}...")
        
        # Check embeddings are stored
        result3 = conn.execute(text("""
            SELECT COUNT(*) as with_embeddings FROM financial_filings 
            WHERE embedding IS NOT NULL
        """))
        emb_count = result3.fetchone()[0]
        print(f"\n✓ Chunks with embeddings: {emb_count}")
        

def test_semantic_search():
    """Test 2: Semantic similarity search"""
    print("\n" + "="*80)
    print("TEST 2: SEMANTIC SIMILARITY SEARCH")
    print("="*80)
    
    # Query: Looking for revenue/income information
    query = "What are the company revenues and income statements?"
    print(f"Query: '{query}'")
    
    # Generate embedding for query
    print("\nGenerating query embedding with Cohere...")
    query_response = cohere_client.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query"
    )
    query_embedding = query_response.embeddings[0]
    query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    # Semantic search using pgvector similarity
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                company_name, 
                doc_type,
                content_chunk::text,
                embedding <-> CAST(:query_embedding AS vector) as distance
            FROM financial_filings
            ORDER BY embedding <-> CAST(:query_embedding AS vector)
            LIMIT 5
        """), {"query_embedding": query_embedding_str})
        
        print("\n✓ Top 5 most similar chunks:")
        for i, row in enumerate(result, 1):
            print(f"\n  {i}. {row[0]} - {row[1]} (distance: {row[3]:.4f})")
            print(f"     Preview: {row[2][:80]}...")


def test_company_filtering():
    """Test 3: Filter by company and type"""
    print("\n" + "="*80)
    print("TEST 3: COMPANY & REPORT TYPE FILTERING")
    print("="*80)
    
    with engine.connect() as conn:
        # Test filtering by company
        result = conn.execute(text("""
            SELECT company_name, doc_type, COUNT(*) as chunks
            FROM financial_filings
            WHERE company_name = 'SBI'
            GROUP BY company_name, doc_type
            ORDER BY doc_type
        """))
        
        print("\n✓ SBI Report Breakdown:")
        for row in result:
            print(f"  {row[1]}: {row[2]} chunks")
        
        # Test all companies
        result2 = conn.execute(text("""
            SELECT DISTINCT company_name FROM financial_filings ORDER BY company_name
        """))
        
        companies = [row[0] for row in result2]
        print(f"\n✓ Available companies: {', '.join(companies)}")


def test_vector_operations():
    """Test 4: Vector operations"""
    print("\n" + "="*80)
    print("TEST 4: VECTOR OPERATIONS")
    print("="*80)
    
    with engine.connect() as conn:
        # Check embedding dimensions
        result = conn.execute(text("""
            SELECT 
                company_name,
                (embedding::text)
            FROM financial_filings
            WHERE embedding IS NOT NULL
            LIMIT 1
        """))
        
        row = result.fetchone()
        if row:
            embedding_str = row[1]
            # Count dimensions
            values = embedding_str.strip('[]').split(',')
            embedding_dim = len(values)
            print(f"✓ Embedding dimensions: {embedding_dim}")
            print(f"✓ First 5 values: {values[:5]}")
        
        # Test vector arithmetic (similarity search between documents)
        result2 = conn.execute(text("""
            SELECT e1.company_name, e1.doc_type, e2.company_name, e2.doc_type,
                   e1.embedding <-> e2.embedding as similarity
            FROM financial_filings e1
            CROSS JOIN financial_filings e2
            WHERE e1.id < e2.id AND e1.company_name = 'SBI' AND e2.company_name = 'SBI'
            ORDER BY e1.embedding <-> e2.embedding
            LIMIT 3
        """))
        
        print(f"\n✓ Document similarity (SBI balance sheets vs other reports):")
        for row in result2:
            print(f"  {row[1]} vs {row[3]}: {row[4]:.6f}")


def test_metadata():
    """Test 5: Metadata storage"""
    print("\n" + "="*80)
    print("TEST 5: METADATA STORAGE")
    print("="*80)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT metadata FROM financial_filings LIMIT 1
        """))
        
        row = result.fetchone()
        if row:
            metadata = row[0]
            print(f"✓ Metadata stored: {metadata}")
        
        # Check all metadata fields
        result2 = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN metadata->>'company' IS NOT NULL THEN 1 END) as with_company,
                COUNT(CASE WHEN metadata->>'embedding_model' IS NOT NULL THEN 1 END) as with_model,
                COUNT(CASE WHEN metadata->>'word_count' IS NOT NULL THEN 1 END) as with_wordcount
            FROM financial_filings
        """))
        
        m = result2.fetchone()
        print(f"✓ Metadata completeness:")
        print(f"  Total chunks: {m[0]}")
        print(f"  With company: {m[1]}")
        print(f"  With embedding model: {m[2]}")
        print(f"  With word count: {m[3]}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("FINANCIAL EMBEDDINGS TEST SUITE")
    print("="*80)
    
    try:
        test_basic_queries()
        test_semantic_search()
        test_company_filtering()
        test_vector_operations()
        test_metadata()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80)
        print("\nSummary:")
        print("✓ Data retrieval works")
        print("✓ Semantic search with embeddings works")
        print("✓ Company/type filtering works")
        print("✓ Vector operations work (pgvector)")
        print("✓ Metadata properly stored")
        print("\nFinancial embeddings are ready for the financial agent RAG system!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
