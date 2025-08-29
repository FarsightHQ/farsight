"""
FAR Request Management API endpoints
Handles CRUD operations for FAR requests and file ingestion
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import aiofiles
import os
from app.core.database import get_db
from app.models.far_request import FarRequest
from app.schemas.far_request import FarRequestCreate, FarRequestResponse
from app.services.far_service import FarIngestionService
from app.services.csv_ingestion_service import CsvIngestionService
from app.utils.error_handlers import success_response, paginated_response

router = APIRouter(prefix="/far", tags=["FAR Requests"])


@router.post("", status_code=status.HTTP_201_CREATED)
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
        
        return success_response(
            data=result.dict() if hasattr(result, 'dict') else result,
            message=f"FAR request '{title}' created successfully",
            metadata={
                "filename": file.filename,
                "external_id": external_id,
                "file_size": file.size if hasattr(file, 'size') else None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_far_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all FAR requests with pagination
    """
    total = db.query(FarRequest).count()
    requests = db.query(FarRequest).offset(skip).limit(limit).all()
    
    return success_response(
        data=requests,  # Return objects directly for now
        message=f"Retrieved {len(requests)} of {total} FAR requests",
        metadata={
            "pagination": {
                "skip": skip,
                "limit": limit, 
                "total": total,
                "returned": len(requests),
                "has_next": skip + len(requests) < total,
                "has_previous": skip > 0
            }
        }
    )


@router.get("/{request_id}")
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
    
    # Convert to dict for standardized response
    request_data = {
        "id": str(far_request.id),
        "source_sha256": str(far_request.source_sha256 or ""),
        "source_size_bytes": far_request.source_size_bytes,
        "status": str(far_request.status or ""),
        "created_at": str(far_request.created_at),
        "source_filename": str(far_request.source_filename or ""),
        "title": str(far_request.title or ""),
        "external_id": str(far_request.external_id or ""),
        "storage_path": str(far_request.storage_path or ""),
        "created_by": str(far_request.created_by or "")
    }
    
    return success_response(
        data=request_data,
        message=f"Retrieved FAR request {request_id}"
    )


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
        
        ingest_data = {
            "request_id": request_id,
            "rules_created": result.get("rules_created", 0),
            "ingestion_details": result
        }
        
        return success_response(
            data=ingest_data,
            message=f"Successfully ingested request {request_id} with {result.get('rules_created', 0)} rules created"
        )
        
    except Exception as e:
        # Rollback on error
        far_request.status = 'error'
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
