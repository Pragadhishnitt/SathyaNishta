"""
RAG Legal Database - Store legal document embeddings in Supabase pgvector
Extracts text from PDFs, chunks them, generates embeddings, and stores in Supabase
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Add repo to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "backend"))

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "pdfplumber"], check=True)
    import pdfplumber

try:
    import cohere
except ImportError:
    print("Installing cohere...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "cohere"], check=True)
    import cohere

try:
    from supabase import create_client, Client
except ImportError:
    print("Installing supabase...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "supabase"], check=True)
    from supabase import create_client, Client

# Get environment variables (already set by docker-compose or .env in local dev)
# In Docker, env vars are passed via env_file directive, not loaded from .env file

# Configure Cohere
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if COHERE_API_KEY:
    cohere_client = cohere.Client(COHERE_API_KEY)
else:
    print("⚠️  Warning: COHERE_API_KEY not found in environment")
    cohere_client = None

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️  Warning: SUPABASE_URL or SUPABASE_KEY not found in environment")
    print("Using placeholder values. Set via docker-compose env_file or environment.")
    SUPABASE_URL = SUPABASE_URL or "https://your-project.supabase.co"
    SUPABASE_KEY = SUPABASE_KEY or "your-supabase-key"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Cohere embedding model info
print("Using Cohere embedding model (embed-english-v3.0)...")
print("✓ Model loaded (1024 dimensions)")


def extract_text_from_pdf(pdf_path: str, max_pages: int = None) -> str:
    """Extract text from all pages of PDF (handles tables better than PyPDF2)"""
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages) if max_pages is None else min(len(pdf.pages), max_pages)

        for page_num in range(total_pages):
            page = pdf.pages[page_num]

            # Extract tables first
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    # Convert table to readable text format
                    for row in table:
                        text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
                    text += "\n"

            # Extract regular text
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Split text into chunks of approximately chunk_size words"""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)

    return chunks


def generate_embeddings(chunks_data: List[Dict]) -> List[Dict]:
    """Generate vector embeddings for all chunks using Cohere API"""
    print("\n" + "=" * 80)
    print("Generating embeddings for all chunks using Cohere...")
    print("=" * 80)

    if not cohere_client:
        print("✗ Error: Cohere client not initialized. Check COHERE_API_KEY in .env")
        return chunks_data

    # Generate embeddings using Cohere API (1024 dimensions)
    for i, chunk_data in enumerate(chunks_data):
        try:
            response = cohere_client.embed(
                texts=[chunk_data["content"]], model="embed-english-v3.0", input_type="search_document"
            )
            chunk_data["embedding"] = response.embeddings[0]  # 1024 dimensions
            chunk_data["embedding_dim"] = len(response.embeddings[0])

            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{len(chunks_data)} embeddings generated...")
        except Exception as e:
            print(f"Error generating embedding for chunk {i}: {e}")
            continue

    successful = len([c for c in chunks_data if "embedding" in c])
    print(f"✓ Generated {successful} embeddings (dimension: 1024)")

    return chunks_data


def store_in_supabase(chunks_data: List[Dict]) -> None:
    """Store chunks with embeddings in Supabase regulatory_docs table"""
    print("\n" + "=" * 80)
    print("Storing embeddings in Supabase regulatory_docs table...")
    print("=" * 80)

    success_count = 0
    error_count = 0

    for i, chunk_data in enumerate(chunks_data, 1):
        try:
            # Map source to standardized values
            source_map = {"SEBI": "SEBI", "INDAS": "IndAS", "COMPANIES_ACT": "CompaniesAct"}

            # Prepare data for insertion into regulatory_docs table
            data = {
                "title": chunk_data.get("title", chunk_data["document"]),
                "source": source_map.get(chunk_data["source"], chunk_data["source"]),
                "category": chunk_data.get("category"),
                "doc_type": chunk_data.get("doc_type", "regulation"),
                "content": chunk_data.get("full_content", chunk_data["content"]),
                "content_chunk": chunk_data["content"],
                "embedding": chunk_data["embedding"],
                "effective_date": chunk_data.get("effective_date"),
                "url": chunk_data.get("url"),
                "metadata": chunk_data.get(
                    "metadata",
                    {
                        "chunk_number": chunk_data.get("chunk_number"),
                        "word_count": chunk_data.get("word_count"),
                        "document": chunk_data["document"],
                    },
                ),
            }

            # Insert into Supabase regulatory_docs table
            result = supabase.table("regulatory_docs").insert(data).execute()
            success_count += 1

            if i % 10 == 0:
                print(f"Progress: {i}/{len(chunks_data)} chunks stored...")

        except Exception as e:
            error_count += 1
            print(f"Error storing chunk {i}: {e}")

    print(f"\n✓ Storage complete!")
    print(f"  Success: {success_count} chunks")
    print(f"  Errors: {error_count} chunks")


def process_legal_folder(folder_name: str = "sebi") -> List[Dict]:
    """Process all PDFs in a legal documents folder"""
    # Path to legal docs folder
    legal_folder = Path(__file__).parent / "legal_docs" / folder_name

    if not legal_folder.exists():
        print(f"Error: Folder not found at {legal_folder}")
        return []

    # Find all PDF files
    pdf_files = list(legal_folder.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {legal_folder}")
        return []

    print(f"Found {len(pdf_files)} PDF file(s) in {folder_name.upper()} folder")
    print("=" * 80)

    # Category mapping based on folder
    category_map = {"sebi": "disclosure", "indas": "related_party", "companies_act": "compliance"}

    all_chunks = []

    # Process each PDF
    for pdf_path in pdf_files:
        print(f"\n📄 Processing: {pdf_path.name}")
        print("-" * 80)

        # Extract text from all pages
        print("Extracting text from all pages...")
        text = extract_text_from_pdf(str(pdf_path))
        word_count = len(text.split())
        print(f"Extracted {word_count} words")

        # Chunk into 500-word segments
        print("Chunking text into 500-word segments...")
        chunks = chunk_text(text, chunk_size=500)
        print(f"Created {len(chunks)} chunks")

        # Store chunks with metadata matching regulatory_docs schema
        for i, chunk in enumerate(chunks, 1):
            all_chunks.append(
                {
                    "source": folder_name.upper(),  # SEBI, INDAS, COMPANIES_ACT
                    "document": pdf_path.name,
                    "title": pdf_path.stem,  # Filename without extension
                    "category": category_map.get(folder_name.lower()),
                    "doc_type": "regulation",
                    "full_content": text,  # Store full document content
                    "chunk_number": i,
                    "content": chunk,
                    "word_count": len(chunk.split()),
                    "metadata": {"total_chunks": len(chunks), "source_folder": folder_name},
                }
            )

    return all_chunks


def main():
    """Main function to process PDFs and store in Supabase"""
    print("=" * 80)
    print("RAG Legal Database - Supabase pgvector Setup")
    print("=" * 80)

    all_chunks = []

    # Process all three folders
    folders = ["sebi", "indas", "companies_act"]

    for folder in folders:
        print(f"\n📂 Processing {folder.upper()} documents...")
        chunks = process_legal_folder(folder)

        if chunks:
            print(f"✓ Extracted {len(chunks)} chunks from {folder}")
            all_chunks.extend(chunks)
        else:
            print(f"⚠️  No chunks extracted from {folder}")

    if not all_chunks:
        print("\n❌ No chunks to process from any folder. Exiting.")
        return

    print(f"\n📊 Total chunks from all sources: {len(all_chunks)}")

    # Generate embeddings for all chunks
    all_chunks = generate_embeddings(all_chunks)

    # Store in Supabase
    store_in_supabase(all_chunks)

    print("\n" + "=" * 80)
    print("✓ All done! Legal documents stored in Supabase pgvector")
    print("=" * 80)

    # Summary
    print(f"\nSummary:")
    print(f"  Total chunks: {len(all_chunks)}")
    if all_chunks:
        print(f"  Embedding dimension: {all_chunks[0]['embedding_dim']}")
        print(f"  Sources: {set(c['source'] for c in all_chunks)}")
        print(f"  Documents: {set(c['document'] for c in all_chunks)}")
    else:
        print("  No embeddings were generated.")


if __name__ == "__main__":
    main()
