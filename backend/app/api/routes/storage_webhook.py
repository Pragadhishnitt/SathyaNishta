"""Storage Webhook API Routes

This endpoint receives webhooks from Supabase storage events
and triggers the document processing pipeline.

Supabase Edge Functions should call this endpoint when
files are uploaded to storage buckets.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.services.document_processor import document_processor
from app.shared.logger import setup_logger

router = APIRouter(tags=["storage-webhook"])
logger = setup_logger("storage_webhook")


class StorageEvent(BaseModel):
    """Storage event payload from Supabase."""

    bucket: str
    record: Dict[str, Any]
    type: Optional[str] = "INSERT"


@router.post("/webhook")
async def storage_webhook(
    event: StorageEvent, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Handle storage webhook events from Supabase.

    This endpoint is called by Supabase Edge Functions when
    files are uploaded to storage buckets.

    Args:
        event: Storage event data
        background_tasks: FastAPI background tasks

    Returns:
        Processing status and details
    """
    try:
        logger.info(
            f"Received storage webhook: {event.bucket}/{event.record.get('name')}"
        )

        # Process the document in background
        background_tasks.add_task(process_document_background, event.dict())

        return {
            "status": "accepted",
            "message": "Document processing started",
            "bucket": event.bucket,
            "file": event.record.get("name"),
        }

    except Exception as e:
        logger.error(f"Storage webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")


async def process_document_background(event_data: Dict[str, Any]):
    """Process document in background task."""
    try:
        result = await document_processor.process_storage_event(event_data)

        if result.get("status") == "success":
            logger.info(f"✅ Background processing completed: {result.get('message')}")
        else:
            logger.error(f"❌ Background processing failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Background processing error: {e}")


@router.get("/status")
async def get_processing_status() -> Dict[str, Any]:
    """Get current processing status and statistics."""
    try:
        # This would typically query a processing queue or status table
        # For now, return basic status
        return {
            "status": "active",
            "processor": "document_processor",
            "supported_buckets": [
                "financial_docs",
                "audio_recordings",
                "temp_uploads",
                "news_uploads",
            ],
            "auto_processing": True,
            "timestamp": "2024-03-29T00:00:00Z",
        }

    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")


@router.post("/test")
async def test_processing(
    bucket: str = "financial_docs", file_name: str = "AAPL/FY2024/Q1/balance_sheet.pdf"
):
    """Test the document processing pipeline."""
    try:
        test_event = {
            "bucket": bucket,
            "record": {
                "name": file_name,
                "id": "test-file-id",
                "size": 1024000,
                "content_type": "application/pdf",
            },
            "type": "INSERT",
        }

        result = await document_processor.process_storage_event(test_event)

        return {"test_result": result, "test_event": test_event}

    except Exception as e:
        logger.error(f"Test processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {e}")
