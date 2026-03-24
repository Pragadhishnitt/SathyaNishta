#!/usr/bin/env python3
"""
Seed Financial Data - Extract annual reports, generate embeddings, store in Supabase
Follows exact same pattern as compliance agent RAG setup
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
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed")
    print("Install with: pip install pdfplumber")
    sys.exit(1)

try:
    import cohere
except ImportError:
    print("ERROR: cohere not installed")
    print("Install with: pip install cohere")
    sys.exit(1)

from dotenv import load_dotenv
from app.shared.logger import setup_logger

logger = setup_logger("SeedFinancialData")

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


def extract_text_from_pdf(pdf_path: str, max_pages: int = None) -> str:
    """Extract text from PDF (handles tables like compliance agent)"""
    text = ""
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages) if max_pages is None else min(len(pdf.pages), max_pages)
        
        for page_num in range(total_pages):
            page = pdf.pages[page_num]
            
            # Extract tables first (important for financial reports)
            tables = page.extract_tables()
            if tables:
                for table in tables:
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
        if chunk.strip():
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
                texts=[chunk_data['content']],
                model="embed-english-v3.0",
                input_type="search_document"
            )
            chunk_data['embedding'] = response.embeddings[0]  # 1024 dimensions
            chunk_data['embedding_dim'] = len(response.embeddings[0])
            
            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{len(chunks_data)} embeddings generated...")
        except Exception as e:
            print(f"Error generating embedding for chunk {i}: {e}")
            continue
    
    successful = len([c for c in chunks_data if 'embedding' in c])
    print(f"✓ Generated {successful}/{len(chunks_data)} embeddings (dimension: 1024)")
    
    return chunks_data


def store_in_db(chunks_data: List[Dict]) -> None:
    """Store chunks with embeddings in financial_filings table"""
    print("\n" + "=" * 80)
    print("Storing embeddings in financial_filings table...")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    
    try:
        with engine.connect() as connection:
            print(f"✓ Database connection successful")
            
            for i, chunk_data in enumerate(chunks_data, 1):
                try:
                    # Convert embedding list to pgvector format
                    embedding_list = chunk_data['embedding']
                    
                    # Insert into database
                    # Convert embedding list to pgvector string format: "[0.1, 0.2, ...]"
                    embedding_str = "[" + ",".join(str(x) for x in embedding_list) + "]"
                    
                    # Convert metadata dict to JSON string for JSONB column
                    metadata_json = json.dumps(chunk_data.get('metadata', {}))
                    
                    connection.execute(text("""
                        INSERT INTO financial_filings 
                        (company_name, company_ticker, cin, period, doc_type, filing_date, content_chunk, 
                         page_number, section_name, embedding, source_url, source_file_key, metadata, created_at)
                        VALUES (:company_name, :ticker, :cin, :period, :doc_type, :filing_date, :content,
                                :page_num, :section, CAST(:embedding AS vector), :source_url, :file_key, CAST(:metadata AS jsonb), now())
                    """), {
                        "company_name": chunk_data.get('company_name'),
                        "ticker": chunk_data.get('ticker'),
                        "cin": chunk_data.get('cin'),
                        "period": chunk_data.get('period'),
                        "doc_type": chunk_data.get('doc_type'),
                        "filing_date": chunk_data.get('filing_date'),
                        "content": chunk_data['content'],
                        "page_num": chunk_data.get('chunk_number'),
                        "section": chunk_data.get('section_name'),
                        "embedding": embedding_str,  # pgvector: "[0.1, 0.2, ...]"
                        "source_url": chunk_data.get('source_url'),
                        "file_key": chunk_data.get('source_file'),
                        "metadata": metadata_json  # JSON-serialized string for JSONB
                    })
                    success_count += 1
                    
                    if i % 10 == 0:
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


def process_financial_pdfs(pdf_folder: Path) -> List[Dict]:
    """Process all PDFs in annual_reports folder and return chunks"""
    
    if not pdf_folder.exists():
        print(f"✗ ERROR: PDF folder not found at {pdf_folder}")
        print(f"   Absolute path: {pdf_folder.absolute()}")
        return []
    
    # Find all PDF files
    pdf_files = sorted(pdf_folder.glob("*.pdf"))
    
    print(f"   Found {len(pdf_files)} PDF files")
    
    if not pdf_files:
        print(f"✗ ERROR: No PDF files found in {pdf_folder}")
        return []
    
    # List found files
    print("\n   PDF Files:")
    for pdf_file in pdf_files:
        print(f"     - {pdf_file.name}")
    
    print("=" * 80)
    
    all_chunks = []
    
    # Process each PDF
    for pdf_path in pdf_files:
        print(f"\n📄 Processing: {pdf_path.name}")
        print("-" * 80)
        
        # Extract company name and report type from filename
        # Expected format: CompanyName_ReportType.pdf
        name_parts = pdf_path.stem.split('_')
        company_name = name_parts[0] if name_parts else "Unknown"
        report_type = name_parts[1] if len(name_parts) > 1 else "Unknown"
        
        # Extract text from all pages
        print("Extracting text from PDF...")
        text = extract_text_from_pdf(str(pdf_path))
        word_count = len(text.split())
        print(f"  Extracted {word_count} words")
        
        if not text.strip():
            print(f"  ⚠️  No text extracted from {pdf_path.name}")
            continue
        
        # Chunk into 500-word segments
        print("Chunking text into 500-word segments...")
        chunks = chunk_text(text, chunk_size=500)
        print(f"  Created {len(chunks)} chunks")
        
        # Store chunks with metadata
        for chunk_num, chunk in enumerate(chunks, 1):
            all_chunks.append({
                'company_name': company_name,
                'ticker': company_name.upper()[:6],  # Simple ticker from name
                'cin': '',  # To be filled from metadata if available
                'period': 'FY2024',  # Default period
                'doc_type': report_type.lower(),  # balancesheet, cashflow, etc.
                'filing_date': None,
                'content': chunk,
                'chunk_number': chunk_num,
                'section_name': report_type,
                'source_file': pdf_path.name,
                'source_url': '',
                'embedding': None,  # Will be filled by generate_embeddings
                'metadata': {
                    'company': company_name,
                    'report_type': report_type,
                    'chunk_number': chunk_num,
                    'word_count': len(chunk.split()),
                    'total_chunks': len(chunks),
                    'embedding_model': 'cohere-embed-english-v3.0',
                    'embedding_dim': 1024
                }
            })
    
    print(f"\n✓ Total chunks extracted: {len(all_chunks)}")
    return all_chunks


def main():
    """Main function to process all annual reports and seed database"""
    print("\n" + "=" * 80)
    print("FINANCIAL DATA EMBEDDING PIPELINE")
    print("Seed financial_filings with Cohere embeddings (1024-dim)")
    print("=" * 80)
    
    # Path to annual reports
    pdf_folder = repo_root / "app/agents/financial/annual_reports"
    
    print(f"\n📁 Looking for PDFs in: {pdf_folder}")
    print(f"   Absolute path: {pdf_folder.absolute()}")
    print(f"   Exists: {pdf_folder.exists()}")
    
    # Process all PDFs
    print("\n🔍 Scanning for PDF files...")
    all_chunks = process_financial_pdfs(pdf_folder)
    
    if not all_chunks:
        print("\n✗ CRITICAL: No chunks extracted from PDFs")
        print("   Please check:")
        print(f"   - Folder exists: {pdf_folder.exists()}")
        print(f"   - Folder path: {pdf_folder}")
        print(f"   - PDFs in folder: {list(pdf_folder.glob('*.pdf')) if pdf_folder.exists() else 'N/A'}")
        return
    
    print(f"\n✓ Extracted {len(all_chunks)} chunks from PDFs")
    
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
    print("\n💾 Storing in financial_filings table...")
    store_in_db(chunks_with_embeddings)
    
    print("\n" + "=" * 80)
    print("✓ EMBEDDING PIPELINE COMPLETE")
    print("=" * 80)
    print(f"Successfully embedded and stored {len(chunks_with_embeddings)} chunks")
    print(f"from {len(set(c['source_file'] for c in chunks_with_embeddings))} PDF files")


if __name__ == "__main__":
    main()
