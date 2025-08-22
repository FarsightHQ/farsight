"""
FAR (Federated Access Request) API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import aiofiles
import os
from app.core.database import get_db
from app.models.far_request import FarRequest
from app.schemas.far_request import FarRequestCreate, FarRequestResponse
from app.services.far_service import FarIngestionService
from app.services.csv_ingestion_service import CsvIngestionService

router = APIRouter()


@router.post("/requests", response_model=FarRequestResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/requests", response_model=List[FarRequestResponse])
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


@router.get("/requests/{request_id}", response_model=FarRequestResponse)
def get_far_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific FAR request by ID
    """
    request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="FAR request not found")
    return request


@router.post("/requests/{request_id}/ingest", status_code=status.HTTP_200_OK)
async def ingest_far_csv(
    request_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Phase 2.2: Ingest and normalize CSV data for a FAR request
    
    This endpoint processes the uploaded CSV file, normalizes IP addresses and port ranges,
    and creates FAR rules with endpoint and service normalization.
    """
    # Verify the request exists
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail="FAR request not found")
    
    if far_request.status not in ['submitted', 'processing']:
        raise HTTPException(
            status_code=400, 
            detail=f"Request is in '{far_request.status}' status and cannot be ingested"
        )
    
    try:
        # Update status to processing
        far_request.status = 'processing'
        db.commit()
        
        # Read the uploaded CSV file
        full_path = os.path.join("uploads", far_request.storage_path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Uploaded file not found")
        
        async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
            file_content = await f.read()
        
        # Process the CSV with the ingestion service
        ingestion_service = CsvIngestionService(db)
        statistics = await ingestion_service.ingest_csv_file(request_id, file_content)
        
        return {
            "message": "CSV ingestion completed",
            "request_id": request_id,
            "statistics": statistics
        }
        
    except Exception as e:
        # Reset status on error
        far_request.status = 'submitted'
        db.commit()
        raise HTTPException(status_code=400, detail=f"CSV ingestion failed: {str(e)}")


@router.get("/requests/{request_id}/rules")
def get_far_rules(
    request_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get normalized FAR rules for a request
    """
    # Verify the request exists
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail="FAR request not found")
    
    # Get rules with their relationships
    from app.models.far_rule import FarRule
    rules = db.query(FarRule).filter(
        FarRule.request_id == request_id
    ).offset(skip).limit(limit).all()
    
    # Format rules with their endpoints and services
    formatted_rules = []
    for rule in rules:
        rule_data = {
            "id": rule.id,
            "action": rule.action,
            "direction": rule.direction,
            "created_at": rule.created_at.isoformat(),
            "endpoints": {
                "sources": [
                    {"network_cidr": ep.network_cidr} 
                    for ep in rule.endpoints if ep.endpoint_type == 'source'
                ],
                "destinations": [
                    {"network_cidr": ep.network_cidr} 
                    for ep in rule.endpoints if ep.endpoint_type == 'destination'
                ]
            },
            "services": [
                {
                    "protocol": svc.protocol,
                    "port_ranges": str(svc.port_ranges)  # PostgreSQL multirange format
                }
                for svc in rule.services
            ]
        }
        formatted_rules.append(rule_data)
    
    # Get total count
    total_rules = db.query(FarRule).filter(FarRule.request_id == request_id).count()
    
    return {
        "request_id": request_id,
        "total_rules": total_rules,
        "rules": formatted_rules,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "returned": len(formatted_rules)
        }
    }
