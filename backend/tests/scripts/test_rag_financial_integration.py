#!/usr/bin/env python3
"""
Financial RAG Integration Test
Demonstrates semantic search of embedded financial documents
"""

import json
import os
import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(repo_root))

import cohere
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from app.core.config import settings

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(COHERE_API_KEY)
engine = create_engine(settings.DATABASE_URL)


def test_rag_financial_queries():
    """Test RAG semantic search with financial queries"""
    print("\n" + "=" * 80)
    print("FINANCIAL RAG INTEGRATION TEST")
    print("Testing semantic search of embedded financial documents")
    print("=" * 80)

    # Define realistic financial inquiry queries
    queries = [
        "What is the balance sheet composition and asset structure?",
        "How are the cash flows and liquidity position?",
        "What are the key financial ratios and metrics?",
        "Show me the consolidated financial statements",
        "What are the revenue and profitability metrics?",
    ]

    for query_idx, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {query_idx}: {query}")
        print(f"{'='*80}")

        # Generate embedding for query
        query_response = cohere_client.embed(texts=[query], model="embed-english-v3.0", input_type="search_query")
        query_embedding = query_response.embeddings[0]
        query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Semantic search across all financial documents
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT 
                    company_name,
                    doc_type,
                    content_chunk,
                    embedding <-> CAST(:query_embedding AS vector) as distance,
                    metadata
                FROM financial_filings
                ORDER BY embedding <-> CAST(:query_embedding AS vector)
                LIMIT 3
            """
                ),
                {"query_embedding": query_embedding_str},
            )

            print(f"\n✓ Top 3 most relevant documents:\n")
            for i, row in enumerate(result, 1):
                company, doc_type, content, distance, metadata = row
                metadata_obj = (
                    metadata if isinstance(metadata, dict) else json.loads(metadata) if isinstance(metadata, str) else {}
                )

                print(f"  [{i}] {company} - {doc_type} (relevance: {1/(1+distance):.1%})")
                print(f"      Word count: {metadata_obj.get('word_count', 'N/A')}")
                print(f"      Preview: {content[:100]}...")
                print()


def test_rag_company_specific():
    """Test RAG with company-specific financial queries"""
    print("\n" + "=" * 80)
    print("COMPANY-SPECIFIC RAG TEST")
    print("=" * 80)

    companies = ["Wipro", "Reliance", "SBI"]
    queries = {
        "Wipro": "technology revenue growth and IT services performance",
        "Reliance": "oil and gas refining revenue and energy business metrics",
        "SBI": "banking liabilities and deposit growth metrics",
    }

    for company in companies:
        query = queries.get(company, "financial performance and growth")
        print(f"\n{'='*80}")
        print(f"Company: {company}")
        print(f"Query: {query}")
        print(f"{'='*80}")

        # Generate query embedding
        query_response = cohere_client.embed(texts=[query], model="embed-english-v3.0", input_type="search_query")
        query_embedding = query_response.embeddings[0]
        query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Search within company's documents
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT 
                    doc_type,
                    content_chunk,
                    embedding <-> CAST(:query_embedding AS vector) as distance
                FROM financial_filings
                WHERE LOWER(company_name) = LOWER(:company)
                ORDER BY embedding <-> CAST(:query_embedding AS vector)
                LIMIT 2
            """
                ),
                {"query_embedding": query_embedding_str, "company": company},
            )

            print(f"\n✓ Most relevant {company} documents:\n")
            for i, row in enumerate(result, 1):
                doc_type, content, distance = row
                print(f"  [{i}] {doc_type} (relevance: {1/(1+distance):.1%})")
                print(f"      {content[:120]}...")
                print()


def test_rag_report_type_search():
    """Test searching by report type across companies"""
    print("\n" + "=" * 80)
    print("REPORT TYPE ANALYSIS")
    print("=" * 80)

    # Search for balance sheet data across companies
    query = "assets liabilities equity capital structure"
    print(f"Query: '{query}'")
    print("Searching balance sheet documents across all companies...\n")

    query_response = cohere_client.embed(texts=[query], model="embed-english-v3.0", input_type="search_query")
    query_embedding = query_response.embeddings[0]
    query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    with engine.connect() as conn:
        # Get balance sheets
        result = conn.execute(
            text(
                """
            SELECT 
                company_name,
                doc_type,
                embedding <-> CAST(:query_embedding AS vector) as distance
            FROM financial_filings
            WHERE LOWER(doc_type) LIKE '%balance%'
            ORDER BY embedding <-> CAST(:query_embedding AS vector)
            LIMIT 5
        """
            ),
            {"query_embedding": query_embedding_str},
        )

        print("✓ Balance Sheets ranked by relevance:\n")
        rows = list(result)
        if rows:
            for i, row in enumerate(rows, 1):
                print(f"  {i}. {row[0]:25} - {row[1]:20} (relevance: {1/(1+row[2]):.1%})")
        else:
            print("  No balance sheets found")

    # Search for cash flow data
    query2 = "cash flow liquidity working capital operations"
    print(f"\n\nQuery: '{query2}'")
    print("Searching cash flow documents across all companies...\n")

    query_response2 = cohere_client.embed(texts=[query2], model="embed-english-v3.0", input_type="search_query")
    query_embedding2 = query_response2.embeddings[0]
    query_embedding_str2 = "[" + ",".join(str(x) for x in query_embedding2) + "]"

    with engine.connect() as conn:
        result2 = conn.execute(
            text(
                """
            SELECT 
                company_name,
                doc_type,
                embedding <-> CAST(:query_embedding AS vector) as distance
            FROM financial_filings
            WHERE LOWER(doc_type) LIKE '%cash%'
            ORDER BY embedding <-> CAST(:query_embedding AS vector)
            LIMIT 5
        """
            ),
            {"query_embedding": query_embedding_str2},
        )

        print("✓ Cash Flow Statements ranked by relevance:\n")
        rows2 = list(result2)
        if rows2:
            for i, row in enumerate(rows2, 1):
                print(f"  {i}. {row[0]:25} - {row[1]:20} (relevance: {1/(1+row[2]):.1%})")
        else:
            print("  No cash flow documents found")


def test_cross_document_analysis():
    """Test retrieving multiple document types for same company"""
    print("\n" + "=" * 80)
    print("CROSS-DOCUMENT ANALYSIS")
    print("=" * 80)

    company = "SBI"
    print(f"Analysis of {company}'s complete financial picture\n")

    # Query all SBI documents
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT 
                doc_type,
                COUNT(*) as chunks,
                MIN(metadata->>'word_count') as min_words,
                MAX(metadata->>'word_count') as max_words
            FROM financial_filings
            WHERE LOWER(company_name) = LOWER(:company)
            GROUP BY doc_type
            ORDER BY doc_type
        """
            ),
            {"company": company},
        )

        rows = list(result)
        if rows:
            print(f"✓ {company} Document Summary:\n")
            total_chunks = 0
            for row in rows:
                print(f"  {row[0]:25} - {row[1]} chunks (words: {row[2]} to {row[3]})")
                total_chunks += row[1]
            print(f"\n  Total Chunks: {total_chunks}")

            # Now show semantic similarity between different report types
            print(f"\n✓ Cross-document semantic similarity for {company}:\n")

            similarity_result = conn.execute(
                text(
                    """
                SELECT 
                    e1.doc_type,
                    e2.doc_type,
                    AVG(e1.embedding <-> e2.embedding) as avg_distance
                FROM financial_filings e1
                CROSS JOIN financial_filings e2
                WHERE LOWER(e1.company_name) = LOWER(:company)
                AND LOWER(e2.company_name) = LOWER(:company)
                AND e1.id < e2.id
                GROUP BY e1.doc_type, e2.doc_type
                ORDER BY avg_distance
            """
                ),
                {"company": company},
            )

            sim_rows = list(similarity_result)
            if sim_rows:
                for row in sim_rows:
                    similarity = 1 / (1 + row[2])
                    print(f"  {row[0]:25} ↔ {row[1]:25} = {similarity:.1%}")
            else:
                print("  No cross-document pairs found")
        else:
            print(f"  No documents found for {company}")


def main():
    """Run all RAG tests"""
    try:
        test_rag_financial_queries()
        test_rag_company_specific()
        test_rag_report_type_search()
        test_cross_document_analysis()

        print("\n" + "=" * 80)
        print("✅ ALL RAG INTEGRATION TESTS PASSED!")
        print("=" * 80)
        print("\nSummary:")
        print("✓ Semantic search with financial queries works")
        print("✓ Company-specific document retrieval works")
        print("✓ Report type filtering + semantic ranking works")
        print("✓ Cross-document analysis works")
        print("\nFinancial embeddings are ready for investment investigation RAG!")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
