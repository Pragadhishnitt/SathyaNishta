#!/usr/bin/env python3
"""Debug audio agent document retrieval"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from sqlalchemy import create_engine, text
from app.core.config import settings
import json

engine = create_engine(settings.DATABASE_URL)

print("=" * 80)
print("DEBUG: Audio Document Retrieval")
print("=" * 80)

try:
    with engine.connect() as conn:
        # Check 1: Table exists
        print("\n1. Checking if audio_transcriptions table exists...")
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM audio_transcriptions")).fetchone()
            print(f"   ✓ Table exists with {result[0]} rows")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            sys.exit(1)

        # Check 2: List all companies
        print("\n2. Companies in table:")
        companies = conn.execute(text("SELECT DISTINCT company_name FROM audio_transcriptions")).fetchall()
        for c in companies:
            print(f"   - {c[0]}")

        # Check 3: Try basic query (no vector search)
        print("\n3. Basic name search for 'State Bank of India':")
        try:
            result = conn.execute(
                text(
                    """
                SELECT id, company_name, company_code, content_chunk 
                FROM audio_transcriptions
                WHERE company_name ILIKE '%State Bank%'
                LIMIT 1
            """
                )
            ).fetchone()
            if result:
                print(f"   ✓ Found: {result[1]}")
            else:
                print(f"   ✗ No results")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # Check 4: Try vector search
        print("\n4. Testing vector search with pgvector:")
        try:
            # Create a dummy vector
            dummy_vector = "[" + ",".join(["0.1"] * 1024) + "]"
            result = conn.execute(
                text(
                    """
                SELECT id, company_name, 
                       1 - (embedding <=> CAST(:vec AS vector)) AS similarity
                FROM audio_transcriptions
                WHERE company_name ILIKE '%State Bank%'
                LIMIT 1
            """
                ),
                {"vec": dummy_vector},
            ).fetchone()

            if result:
                print(f"   ✓ Vector search works")
                print(f"     Company: {result[1]}, Similarity: {result[2]:.2%}")
            else:
                print(f"   ✓ Vector search syntax valid but no results")
        except Exception as e:
            print(f"   ✗ Vector search error: {e}")
            print(f"     This might be a pgvector extension issue")

        # Check 5: Try Cohere embedding
        print("\n5. Testing Cohere embedding generation:")
        try:
            import cohere
            import os
            from dotenv import load_dotenv

            load_dotenv()
            api_key = os.getenv("COHERE_API_KEY")
            if api_key:
                client = cohere.Client(api_key)
                resp = client.embed(
                    texts=["financial performance"], model="embed-english-v3.0", input_type="search_query"
                )
                print(f"   ✓ Cohere embedding generated ({len(resp.embeddings[0])} dimensions)")
            else:
                print(f"   ✗ COHERE_API_KEY not found")
        except Exception as e:
            print(f"   ✗ Cohere error: {e}")

except Exception as e:
    print(f"\n✗ Critical error: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
