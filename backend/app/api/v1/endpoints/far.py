"""
FAR (File Analysis Request) API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.models import FarRequest
from app.schemas import FarRequestResponse
from app.services import FarIngestionService

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/ingest/far", tags=["FAR Ingestion"])


@router.post("", response_model=FarRequestResponse)
async def ingest_far_request(
    file: UploadFile = File(..., description="CSV file to upload"),
    title: Optional[str] = Form(None, description="Title for the FAR request"),
    external_id: Optional[str] = Form(None, description="External reference ID"),
    created_by: str = Form("system", description="User creating the request"),
    db: Session = Depends(get_db)
) -> FarRequestResponse:
    """
    Upload CSV file for FAR (File Analysis Request) processing
    
    - **file**: CSV file (required, max 50MB)
    - **title**: Optional title (derived from filename if not provided)
    - **external_id**: Optional external reference ID
    - **created_by**: User/system creating the request (defaults to "system")
    
    Returns details of the created FAR request including file information.
    """
    logger.info(f"FAR ingestion request: file={file.filename}, title={title}, external_id={external_id}")
    
    service = FarIngestionService(db)
    return await service.process_upload(
        file=file,
        title=title,
        external_id=external_id,
        created_by=created_by
    )


@router.get("/{request_id}")
def get_far_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """Get FAR request by ID"""
    service = FarIngestionService(db)
    far_request = service.get_far_request(request_id)
    
    if not far_request:
        raise HTTPException(status_code=404, detail="FAR request not found")
    
    return {
        "request_id": far_request.id,
        "status": far_request.status,
        "title": far_request.title,
        "external_id": far_request.external_id,
        "source_filename": far_request.source_filename,
        "source_sha256": far_request.source_sha256,
        "source_size_bytes": far_request.source_size_bytes,
        "storage_path": far_request.storage_path,
        "created_by": far_request.created_by,
        "created_at": far_request.created_at
    }


@router.get("")
def list_far_requests(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List FAR requests with pagination"""
    service = FarIngestionService(db)
    requests = service.list_far_requests(limit=limit, offset=offset)
    
    return {
        "requests": [
            {
                "request_id": req.id,
                "status": req.status,
                "title": req.title,
                "external_id": req.external_id,
                "source_filename": req.source_filename,
                "created_by": req.created_by,
                "created_at": req.created_at
            }
            for req in requests
        ],
        "limit": limit,
        "offset": offset
    }
