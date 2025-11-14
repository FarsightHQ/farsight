"""
FAR Request Management API endpoints
Handles CRUD operations for FAR requests and file ingestion
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import aiofiles
import os
from app.core.database import get_db
from app.core.config import settings
from app.models.far_request import FarRequest
from app.schemas.far_request import FarRequestCreate, FarRequestResponse
from app.services.far_service import FarIngestionService
from app.services.csv_ingestion_service import CsvIngestionService
from app.utils.error_handlers import success_response, paginated_response

router = APIRouter(prefix="/far", tags=["FAR Requests"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_far_request(
    title: str = Form(...),
    file: UploadFile = File(...),
    external_id: Optional[str] = Form(None),
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


@router.delete("/{request_id}", status_code=status.HTTP_200_OK)
def delete_far_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a FAR request and all associated data.
    
    - Deletes the uploaded CSV file from disk
    - Deletes all related rules (via cascade)
    - Deletes the request record
    
    Returns:
        Success response with deletion confirmation
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Get the request
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    # Optional: Prevent deletion if currently processing
    if far_request.status == 'processing':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete request {request_id} while it is being processed. Please wait for processing to complete."
        )
    
    # Store file path before deletion
    file_path = None
    if far_request.storage_path:
        file_path = os.path.join(settings.UPLOAD_DIR, far_request.storage_path)
    
    try:
        # Delete the uploaded file from filesystem
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path} for request {request_id}")
            except FileNotFoundError:
                # File already deleted, log warning but continue
                logger.warning(f"File not found for deletion: {file_path} (request {request_id})")
            except PermissionError as e:
                # Permission error, log but continue with DB deletion
                logger.error(f"Permission error deleting file {file_path}: {str(e)}")
            except Exception as e:
                # Other file errors, log but continue
                logger.warning(f"Error deleting file {file_path}: {str(e)}")
        elif file_path:
            logger.warning(f"File path specified but file does not exist: {file_path}")
        
        # Delete the database record (cascade will handle related rules)
        db.delete(far_request)
        db.commit()
        
        logger.info(f"Successfully deleted FAR request {request_id}")
        
        return success_response(
            data={"request_id": request_id, "deleted": True},
            message=f"FAR request {request_id} and all associated data deleted successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting FAR request {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete request: {str(e)}")


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
        
        # Read the file content
        async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
            file_content = await f.read()
        
        # Use CSV ingestion service
        csv_service = CsvIngestionService(db)
        
        # Ingest the CSV file
        result = await csv_service.ingest_csv_file(
            request_id=request_id,
            file_content=file_content
        )
        
        # Update status to ingested
        far_request.status = 'ingested'
        db.commit()
        
        ingest_data = {
            "request_id": request_id,
            "rules_created": result.get("created_rules", 0),
            "ingestion_details": result
        }
        
        return success_response(
            data=ingest_data,
            message=f"Successfully ingested request {request_id} with {result.get('created_rules', 0)} rules created"
        )
        
    except Exception as e:
        # Rollback on error
        far_request.status = 'error'
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
