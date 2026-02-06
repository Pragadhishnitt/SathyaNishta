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
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Installing sentence-transformers...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "sentence-transformers"], check=True)
    from sentence_transformers import SentenceTransformer

try:
    from supabase import create_client, Client
except ImportError:
    print("Installing supabase...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "supabase"], check=True)
    from supabase import create_client, Client

from dotenv import load_dotenv

# Load environment variables
load_dotenv(repo_root / ".env.example")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️  Warning: SUPABASE_URL or SUPABASE_KEY not found in .env.example")
    print("Using placeholder values. Update .env.example with real credentials.")
    SUPABASE_URL = SUPABASE_URL or "https://your-project.supabase.co"
    SUPABASE_KEY = SUPABASE_KEY or "your-supabase-key"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
print("✓ Model loaded")


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
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    return chunks


def generate_embeddings(chunks_data: List[Dict]) -> List[Dict]:
    """Generate vector embeddings for all chunks using HuggingFace model"""
    print("\n" + "=" * 80)
    print("Generating embeddings for all chunks...")
    print("=" * 80)
    
    # Extract just the content for embedding
    texts = [chunk['content'] for chunk in chunks_data]
    
    # Generate embeddings in batch (much faster than one by one)
    embeddings = embedding_model.encode(texts, show_progress_bar=True, batch_size=32)
    
    # Add embeddings to chunk data
    for i, chunk_data in enumerate(chunks_data):
        chunk_data['embedding'] = embeddings[i].tolist()  # Convert numpy array to list
        chunk_data['embedding_dim'] = len(embeddings[i])
    
    print(f"✓ Generated {len(embeddings)} embeddings (dimension: {len(embeddings[0])})")
    
    return chunks_data


def store_in_supabase(chunks_data: List[Dict]) -> None:
    """Store chunks with embeddings in Supabase pgvector"""
    print("\n" + "=" * 80)
    print("Storing embeddings in Supabase...")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    
    for i, chunk_data in enumerate(chunks_data, 1):
        try:
            # Prepare data for insertion
            data = {
                "content": chunk_data['content'],
                "embedding": chunk_data['embedding'],
                "source": chunk_data['source'],
                "document": chunk_data['document']
            }
            
            # Insert into Supabase
            result = supabase.table('legal_documents').insert(data).execute()
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
        
        # Store chunks with metadata
        for i, chunk in enumerate(chunks, 1):
            all_chunks.append({
                "source": folder_name.upper(),  # SEBI, INDAS, Companies_Act
                "document": pdf_path.name,
                "chunk_number": i,
                "content": chunk,
                "word_count": len(chunk.split())
            })
    
    return all_chunks


def main():
    """Main function to process PDFs and store in Supabase"""
    print("=" * 80)
    print("RAG Legal Database - Supabase pgvector Setup")
    print("=" * 80)
    
    # Process Companies Act folder
    print("\n📂 Processing Companies Act documents...")
    companies_act_chunks = process_legal_folder("companies_act")
    
    if not companies_act_chunks:
        print("No chunks to process. Exiting.")
        return
    
    # Generate embeddings
    companies_act_chunks = generate_embeddings(companies_act_chunks)
    
    # Store in Supabase
    store_in_supabase(companies_act_chunks)
    
    print("\n" + "=" * 80)
    print("✓ All done! Legal documents stored in Supabase pgvector")
    print("=" * 80)
    
    # Summary
    print(f"\nSummary:")
    print(f"  Total chunks: {len(companies_act_chunks)}")
    print(f"  Embedding dimension: {companies_act_chunks[0]['embedding_dim']}")
    print(f"  Sources: {set(c['source'] for c in companies_act_chunks)}")
    print(f"  Documents: {set(c['document'] for c in companies_act_chunks)}")


if __name__ == "__main__":
    main()
