#!/usr/bin/env python3
"""
Seed Audio Data - Extract transcriptions, generate embeddings, store in database
Follows exact same pattern as financial agent RAG setup
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add repo to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

try:
    import cohere
except ImportError:
    print("ERROR: cohere not installed")
    print("Install with: pip install cohere")
    sys.exit(1)

from dotenv import load_dotenv
from app.shared.logger import setup_logger

logger = setup_logger("SeedAudioData")

# Load environment variables
load_dotenv()

# Configure Cohere (1024-dimensional embeddings)
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if COHERE_API_KEY:
    cohere_client = cohere.Client(COHERE_API_KEY)
    logger.info("✓ Cohere client initialized (embed-english-v3.0, 1024 dimensions)")
else:
    print("⚠️  Warning: COHERE_API_KEY not found in .env")
    cohere_client = None

# Initialize database connection
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Split text into chunks of approximately chunk_size words"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks


def generate_embeddings(chunks_data: List[Dict]) -> List[Dict]:
    """Generate vector embeddings for all chunks using Cohere API"""
    print("\n" + "=" * 80)
    print("Generating embeddings for all audio chunks using Cohere...")
    print("=" * 80)
    
    if not cohere_client:
        print("✗ Error: Cohere client not initialized. Check COHERE_API_KEY in .env")
        return chunks_data
    
    # Generate embeddings using Cohere API (1024 dimensions)
    for i, chunk_data in enumerate(chunks_data):
        try:
            response = cohere_client.embed(
                texts=[chunk_data['content']],
                model="embed-english-v3.0",
                input_type="search_document"
            )
            chunk_data['embedding'] = response.embeddings[0]  # 1024 dimensions
            chunk_data['embedding_dim'] = len(response.embeddings[0])
            
            if (i + 1) % 5 == 0:
                print(f"Progress: {i + 1}/{len(chunks_data)} embeddings generated...")
        except Exception as e:
            print(f"Error generating embedding for chunk {i}: {e}")
            continue
    
    successful = len([c for c in chunks_data if 'embedding' in c])
    print(f"✓ Generated {successful}/{len(chunks_data)} embeddings (dimension: 1024)")
    
    return chunks_data


def store_in_db(chunks_data: List[Dict]) -> None:
    """Store chunks with embeddings in audio_transcriptions table"""
    print("\n" + "=" * 80)
    print("Storing embeddings in audio_transcriptions table...")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    
    try:
        with engine.connect() as connection:
            print(f"✓ Database connection successful")
            
            # First, ensure table exists
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS audio_transcriptions (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                company_code VARCHAR(10) NOT NULL,
                transcript_date DATE,
                duration_minutes INTEGER,
                content_chunk TEXT NOT NULL,
                chunk_number INTEGER,
                embedding vector(1024),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT now(),
                updated_at TIMESTAMP DEFAULT now()
            );
            
            CREATE INDEX IF NOT EXISTS idx_audio_company ON audio_transcriptions(company_name);
            CREATE INDEX IF NOT EXISTS idx_audio_embedding ON audio_transcriptions USING ivfflat (embedding vector_cosine_ops);
            """
            
            try:
                connection.execute(text(create_table_sql))
                connection.commit()
                print("✓ Audio transcriptions table created/verified")
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"Note: {e}")
            
            for i, chunk_data in enumerate(chunks_data, 1):
                try:
                    # Convert embedding list to pgvector format
                    embedding_list = chunk_data['embedding']
                    embedding_str = "[" + ",".join(str(x) for x in embedding_list) + "]"
                    
                    # Convert metadata dict to JSON string for JSONB column
                    metadata_json = json.dumps(chunk_data.get('metadata', {}))
                    
                    connection.execute(text("""
                        INSERT INTO audio_transcriptions 
                        (company_name, company_code, transcript_date, duration_minutes, content_chunk, 
                         chunk_number, embedding, metadata, created_at)
                        VALUES (:company_name, :company_code, :transcript_date, :duration_minutes, :content,
                                :chunk_number, CAST(:embedding AS vector), CAST(:metadata AS jsonb), now())
                    """), {
                        "company_name": chunk_data.get('company_name'),
                        "company_code": chunk_data.get('company_code'),
                        "transcript_date": chunk_data.get('transcript_date'),
                        "duration_minutes": chunk_data.get('duration_minutes'),
                        "content": chunk_data['content'],
                        "chunk_number": chunk_data.get('chunk_number'),
                        "embedding": embedding_str,  # pgvector: "[0.1, 0.2, ...]"
                        "metadata": metadata_json  # JSON-serialized string for JSONB
                    })
                    success_count += 1
                    
                    if i % 5 == 0:
                        print(f"Progress: {i}/{len(chunks_data)} chunks stored...")
                
                except Exception as e:
                    error_count += 1
                    print(f"Error storing chunk {i}: {e}")
            
            # Commit transaction
            connection.commit()
            print(f"\n✓ Transaction committed!")
    
    except Exception as e:
        print(f"\n✗ CRITICAL DATABASE ERROR: {e}")
        print(f"   DATABASE_URL: {settings.DATABASE_URL if hasattr(settings, 'DATABASE_URL') else 'NOT SET'}")
        return
    
    print(f"\n✓ Storage complete!")
    print(f"  Success: {success_count} chunks")
    print(f"  Errors: {error_count} chunks")
    
    if success_count == 0:
        print("\n⚠️  WARNING: No chunks were inserted!")


def process_audio_transcriptions(json_file: Path) -> List[Dict]:
    """Process audio transcriptions from JSON file and return chunks"""
    
    if not json_file.exists():
        print(f"✗ ERROR: JSON file not found at {json_file}")
        print(f"   Absolute path: {json_file.absolute()}")
        return []
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            transcriptions = json.load(f)
    except Exception as e:
        print(f"✗ ERROR: Failed to load JSON file: {e}")
        return []
    
    if not isinstance(transcriptions, list):
        print(f"✗ ERROR: JSON file should contain a list of transcriptions, got {type(transcriptions)}")
        return []
    
    print(f"   Found {len(transcriptions)} audio transcriptions")
    
    all_chunks = []
    
    # Process each transcription
    for audio_idx, audio_data in enumerate(transcriptions, 1):
        company = audio_data.get('company', 'Unknown')
        company_code = audio_data.get('company_code', '???')
        transcript = audio_data.get('transcript', '')
        transcript_date = audio_data.get('audio_date')
        duration_minutes = audio_data.get('duration_minutes', 0)
        
        print(f"\n🎧 Processing: {company} ({company_code})")
        print("-" * 80)
        
        if not transcript.strip():
            print(f"  ⚠️  No transcript content for {company}")
            continue
        
        # Chunk into 500-word segments
        print("Chunking transcript into 500-word segments...")
        chunks = chunk_text(transcript, chunk_size=500)
        print(f"  Created {len(chunks)} chunks from {len(transcript.split())} words")
        
        # Store chunks with metadata
        for chunk_num, chunk in enumerate(chunks, 1):
            all_chunks.append({
                'company_name': company,
                'company_code': company_code,
                'transcript_date': transcript_date,
                'duration_minutes': duration_minutes,
                'content': chunk,
                'chunk_number': chunk_num,
                'embedding': None,  # Will be filled by generate_embeddings
                'metadata': {
                    'company': company,
                    'company_code': company_code,
                    'chunk_number': chunk_num,
                    'word_count': len(chunk.split()),
                    'total_chunks': len(chunks),
                    'duration_minutes': duration_minutes,
                    'embedding_model': 'cohere-embed-english-v3.0',
                    'embedding_dim': 1024
                }
            })
    
    print(f"\n✓ Total chunks extracted: {len(all_chunks)}")
    return all_chunks


def main():
    """Main function to process all audio transcriptions and seed database"""
    print("\n" + "=" * 80)
    print("AUDIO DATA EMBEDDING PIPELINE")
    print("Seed audio_transcriptions with Cohere embeddings (1024-dim)")
    print("=" * 80)
    
    # Path to audio transcriptions JSON
    json_file = repo_root / "data" / "audio_transcriptions.json"
    
    print(f"\n📁 Looking for JSON file: {json_file}")
    print(f"   Absolute path: {json_file.absolute()}")
    print(f"   Exists: {json_file.exists()}")
    
    # Process all transcriptions
    print("\n🔍 Loading audio transcriptions...")
    all_chunks = process_audio_transcriptions(json_file)
    
    if not all_chunks:
        print("\n✗ CRITICAL: No chunks extracted from transcriptions")
        print("   Please check:")
        print(f"   - File exists: {json_file.exists()}")
        print(f"   - File path: {json_file}")
        return
    
    print(f"\n✓ Extracted {len(all_chunks)} chunks from transcriptions")
    
    # Generate embeddings
    print("\n🤖 Generating Cohere embeddings...")
    all_chunks = generate_embeddings(all_chunks)
    
    # Filter out chunks without embeddings
    chunks_with_embeddings = [c for c in all_chunks if 'embedding' in c]
    
    if not chunks_with_embeddings:
        print("\n✗ CRITICAL: No embeddings generated")
        print("   Please check:")
        print(f"   - COHERE_API_KEY in .env: {bool(COHERE_API_KEY)}")
        print(f"   - Cohere client initialized: {bool(cohere_client)}")
        return
    
    print(f"✓ Generated {len(chunks_with_embeddings)} embeddings")
    
    # Store in database
    print("\n💾 Storing in audio_transcriptions table...")
    store_in_db(chunks_with_embeddings)
    
    print("\n" + "=" * 80)
    print("✓ AUDIO EMBEDDING PIPELINE COMPLETE")
    print("=" * 80)
    print(f"Successfully embedded and stored {len(chunks_with_embeddings)} chunks")
    print(f"from {len(set(c['company_code'] for c in chunks_with_embeddings))} companies")


if __name__ == "__main__":
    main()
