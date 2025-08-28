"""
FAR Request Management API endpoints
Handles CRUD operations for FAR requests and file ingestion
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
import aiofiles
import os
from app.core.database import get_db
from app.models.far_request import FarRequest
from app.schemas.far_request import FarRequestCreate, FarRequestResponse
from app.services.far_service import FarIngestionService
from app.services.csv_ingestion_service import CsvIngestionService

router = APIRouter(prefix="/requests", tags=["FAR Requests"])


@router.post("", response_model=FarRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_far_request(
    title: str,
    file: UploadFile = File(...),
    external_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new FAR request with file upload
    """
    service = FarIngestionService(db)
    
    try:
        result = await service.process_upload(
            title=title,
            file=file,
            external_id=external_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[FarRequestResponse])
def list_far_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all FAR requests
    """
    requests = db.query(FarRequest).offset(skip).limit(limit).all()
    return requests


@router.get("/{request_id}", response_model=FarRequestResponse)
def get_far_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific FAR request by ID
    """
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    return far_request


@router.post("/{request_id}/ingest", status_code=status.HTTP_200_OK)
async def ingest_far_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Process the uploaded file for a FAR request and create firewall rules
    """
    # Get the request
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    if far_request.status != 'submitted':
        raise HTTPException(
            status_code=400, 
            detail=f"Request {request_id} is not in 'submitted' status. Current status: {far_request.status}"
        )
    
    try:
        # Update status to processing
        far_request.status = 'processing'
        db.commit()
        
        # Process the file
        full_path = os.path.join("uploads", far_request.storage_path)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"File not found: {far_request.storage_path}")
        
        # Use CSV ingestion service
        csv_service = CsvIngestionService(db)
        
        # Ingest the CSV file
        result = await csv_service.ingest_csv_file(
            file_path=full_path,
            request_id=request_id
        )
        
        # Update status to ingested
        far_request.status = 'ingested'
        db.commit()
        
        return {
            "message": f"Successfully ingested request {request_id}",
            "rules_created": result.get("rules_created", 0),
            "details": result
        }
        
    except Exception as e:
        # Rollback on error
        far_request.status = 'error'
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
