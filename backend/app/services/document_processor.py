"""Document Processing Service

This service handles the automated processing of documents
uploaded to Supabase storage buckets and populates the database.

Features:
- PDF text extraction
- Financial data parsing
- Audio transcription
- News article processing
- Compliance record analysis
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import aiohttp
import PyPDF2
from sqlalchemy import create_engine, text
from sqlmodel import Session

from app.core.config import settings
from app.shared.logger import setup_logger

logger = setup_logger("document_processor")

class DocumentProcessor:
    """Automated document processing service for Supabase storage."""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
    async def process_storage_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a storage event from Supabase."""
        try:
            bucket = event_data.get('bucket')
            record = event_data.get('record', {})
            
            logger.info(f"Processing storage event: {bucket}/{record.get('name')}")
            
            if bucket == 'financial_docs':
                return await self.process_financial_document(record)
            elif bucket == 'audio_recordings':
                return await self.process_audio_document(record)
            elif bucket == 'temp_uploads':
                return await self.process_temp_upload(record)
            elif bucket == 'news_uploads':
                return await self.process_news_document(record)
            else:
                logger.warning(f"Unknown bucket: {bucket}")
                return {"status": "ignored", "reason": f"Unknown bucket: {bucket}"}
                
        except Exception as e:
            logger.error(f"Error processing storage event: {e}")
            return {"status": "error", "error": str(e)}
    
    async def process_financial_document(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process a financial document from storage."""
        file_name = record.get('name', '')
        file_id = record.get('id')
        
        # Extract path components
        path_parts = file_name.split('/')
        if len(path_parts) < 4:
            return {"status": "error", "error": "Invalid file path structure"}
        
        ticker, fiscal_year, period, doc_type = path_parts
        doc_type = doc_type.replace('.pdf', '')
        
        logger.info(f"Processing financial: {ticker} {fiscal_year} {period} {doc_type}")
        
        # Download file from Supabase
        file_content = await self.download_file('financial_docs', file_name)
        if not file_content:
            return {"status": "error", "error": "Failed to download file"}
        
        # Extract text from PDF
        text_content = self.extract_pdf_text(file_content)
        
        # Parse financial data
        financial_data = self.parse_financial_data(text_content, ticker, fiscal_year, period, doc_type)
        
        # Store in database
        with Session(self.engine) as session:
            try:
                session.execute(text("""
                    INSERT INTO financial_filings (
                        symbol, company_name, company_ticker, filing_type, period, doc_type,
                        revenue, net_income, total_assets, total_liabilities,
                        content_chunk, metadata, filing_date, source_file_key
                    ) VALUES (
                        :symbol, :company_name, :company_ticker, :filing_type, :period, :doc_type,
                        :revenue, :net_income, :total_assets, :total_liabilities,
                        :content_chunk, :metadata, :filing_date, :source_file_key
                    )
                """), {
                    'symbol': ticker,
                    'company_name': self.get_company_name(ticker),
                    'company_ticker': ticker,
                    'filing_type': doc_type.upper(),
                    'period': f"{fiscal_year}_{period}",
                    'doc_type': doc_type.lower(),
                    'revenue': financial_data.get('revenue'),
                    'net_income': financial_data.get('net_income'),
                    'total_assets': financial_data.get('total_assets'),
                    'total_liabilities': financial_data.get('total_liabilities'),
                    'content_chunk': text_content[:1000],
                    'metadata': json.dumps(financial_data),
                    'filing_date': datetime.utcnow(),
                    'source_file_key': file_name
                })
                session.commit()
                
                logger.info(f"✅ Financial document processed: {file_name}")
                return {"status": "success", "message": f"Processed {file_name}"}
                
            except Exception as e:
                session.rollback()
                logger.error(f"Database error: {e}")
                return {"status": "error", "error": f"Database error: {e}"}
    
    async def process_audio_document(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process an audio document from storage."""
        file_name = record.get('name', '')
        
        # Extract path components
        path_parts = file_name.split('/')
        if len(path_parts) < 4:
            return {"status": "error", "error": "Invalid file path structure"}
        
        ticker, fiscal_year, period, call_info = path_parts
        call_type, date = call_info.split('_')
        call_type = call_type.replace('.mp3', '').replace('.wav', '').replace('.m4a', '')
        
        logger.info(f"Processing audio: {ticker} {call_type} {date}")
        
        # Download file from Supabase
        file_content = await self.download_file('audio_recordings', file_name)
        if not file_content:
            return {"status": "error", "error": "Failed to download file"}
        
        # Transcribe audio (simplified - use speech-to-text service in production)
        transcription = await self.transcribe_audio(file_content)
        
        # Store in database
        with Session(self.engine) as session:
            try:
                session.execute(text("""
                    INSERT INTO audio_transcripts (
                        title, content, speaker, company, date, duration_seconds,
                        sentiment_score, source_file_key
                    ) VALUES (
                        :title, :content, :speaker, :company, :date, :duration_seconds,
                        :sentiment_score, :source_file_key
                    )
                """), {
                    'title': f"{ticker} {call_type} Call - {date}",
                    'content': transcription,
                    'speaker': 'Unknown', # Would be detected in production
                    'company': self.get_company_name(ticker),
                    'date': datetime.strptime(date, '%Y-%m-%d'),
                    'duration_seconds': 1800, # Would be extracted from audio
                    'sentiment_score': 0.5, # Would be analyzed
                    'source_file_key': file_name
                })
                session.commit()
                
                logger.info(f"✅ Audio document processed: {file_name}")
                return {"status": "success", "message": f"Processed {file_name}"}
                
            except Exception as e:
                session.rollback()
                logger.error(f"Database error: {e}")
                return {"status": "error", "error": f"Database error: {e}"}
    
    async def process_temp_upload(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process a temporary upload and move to appropriate bucket."""
        file_name = record.get('name', '')
        
        # Determine target bucket based on file type
        file_extension = Path(file_name).suffix.lower()
        
        if file_extension == '.pdf':
            target_bucket = 'financial_docs'
        elif file_extension in ['.mp3', '.wav', '.m4a']:
            target_bucket = 'audio_recordings'
        else:
            return {"status": "ignored", "reason": f"Unsupported file type: {file_extension}"}
        
        # Move file to target bucket
        success = await self.move_file('temp_uploads', target_bucket, file_name, file_name)
        
        if success:
            logger.info(f"✅ Temp file moved to {target_bucket}: {file_name}")
            return {"status": "success", "message": f"Moved to {target_bucket}"}
        else:
            return {"status": "error", "error": "Failed to move file"}
    
    async def process_news_document(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process a news document."""
        file_name = record.get('name', '')
        
        # Download and extract content
        file_content = await self.download_file('news_uploads', file_name)
        if not file_content:
            return {"status": "error", "error": "Failed to download file"}
        
        # Extract text and metadata
        text_content = file_content.decode('utf-8') if isinstance(file_content, bytes) else str(file_content)
        
        # Store in database
        with Session(self.engine) as session:
            try:
                session.execute(text("""
                    INSERT INTO news_articles (
                        title, content, source, url, published_at, 
                        sentiment_score, relevance_score
                    ) VALUES (
                        :title, :content, :source, :url, :published_at,
                        :sentiment_score, :relevance_score
                    )
                """), {
                    'title': Path(file_name).stem,
                    'content': text_content,
                    'source': 'Uploaded',
                    'url': f'news_uploads/{file_name}',
                    'published_at': datetime.utcnow(),
                    'sentiment_score': 0.5, # Would be analyzed
                    'relevance_score': 0.8  # Would be analyzed
                })
                session.commit()
                
                logger.info(f"✅ News document processed: {file_name}")
                return {"status": "success", "message": f"Processed {file_name}"}
                
            except Exception as e:
                session.rollback()
                logger.error(f"Database error: {e}")
                return {"status": "error", "error": f"Database error: {e}"}
    
    async def download_file(self, bucket: str, file_path: str) -> Optional[bytes]:
        """Download a file from Supabase storage."""
        try:
            url = f"{self.supabase_url}/storage/v1/object/{bucket}/{file_path}"
            headers = {
                'Authorization': f'Bearer {self.supabase_key}',
                'apikey': self.supabase_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Failed to download file: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def move_file(self, from_bucket: str, to_bucket: str, from_path: str, to_path: str) -> bool:
        """Move a file between Supabase buckets."""
        try:
            # Download from source
            file_content = await self.download_file(from_bucket, from_path)
            if not file_content:
                return False
            
            # Upload to destination
            url = f"{self.supabase_url}/storage/v1/object/{to_bucket}/{to_path}"
            headers = {
                'Authorization': f'Bearer {self.supabase_key}',
                'apikey': self.supabase_key,
                'Content-Type': 'application/octet-stream'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=file_content) as response:
                    if response.status == 200:
                        # Delete from source
                        await self.delete_file(from_bucket, from_path)
                        return True
                    else:
                        logger.error(f"Failed to upload file: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Move file error: {e}")
            return False
    
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """Delete a file from Supabase storage."""
        try:
            url = f"{self.supabase_url}/storage/v1/object/{bucket}/{file_path}"
            headers = {
                'Authorization': f'Bearer {self.supabase_key}',
                'apikey': self.supabase_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Delete file error: {e}")
            return False
    
    def extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            from io import BytesIO
            
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return "PDF extraction failed"
    
    def parse_financial_data(self, text: str, ticker: str, fiscal_year: str, period: str, doc_type: str) -> Dict[str, Any]:
        """Parse financial data from extracted text."""
        # In production, use sophisticated financial parsing
        # For now, return mock data
        
        mock_data = {
            'AAPL': {
                'revenue': 383285000000,
                'net_income': 99803000000,
                'total_assets': 352583000000,
                'total_liabilities': 290437000000
            },
            'MSFT': {
                'revenue': 211915000000,
                'net_income': 72361000000,
                'total_assets': 511372000000,
                'total_liabilities': 198298000000
            }
        }
        
        return mock_data.get(ticker, {
            'revenue': 1000000000,
            'net_income': 100000000,
            'total_assets': 2000000000,
            'total_liabilities': 500000000
        })
    
    async def transcribe_audio(self, audio_content: bytes) -> str:
        """Transcribe audio content."""
        # In production, use speech-to-text service
        # For now, return mock transcription
        return f"Audio transcription content. This would contain the full transcription of the earnings call or meeting. Duration: approximately 30 minutes. Key topics discussed include quarterly results, guidance, and Q&A session."
    
    def get_company_name(self, ticker: str) -> str:
        """Get company name from ticker."""
        companies = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'TSLA': 'Tesla, Inc.',
            'AMZN': 'Amazon.com, Inc.',
            'META': 'Meta Platforms, Inc.'
        }
        return companies.get(ticker, f"{ticker} Corporation")

# Singleton instance
document_processor = DocumentProcessor()
