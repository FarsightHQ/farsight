"""
FAR Request Management API endpoints
Handles CRUD operations for FAR requests and file ingestion
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, cast
import aiofiles
import os
from app.core.database import get_db
from app.core.auth import get_current_user, uploader_from_user
from app.core.config import settings
from app.models.far_request import FarRequest
from app.schemas.far_request import FarRequestCreate, FarRequestResponse
from app.schemas.responses import (
    StandardResponse, StatusEnum,
    FarRulesResponse, FarRulesSummaryModel, RuleDetailModel
)
from app.services.far_service import FarIngestionService
from app.services.csv_ingestion_service import CsvIngestionService
from app.services.csv_validation_service import CSVValidationService
from app.utils.error_handlers import success_response, paginated_response
from sqlalchemy.exc import OperationalError
from app.utils.csv_errors import (
    CSVFileError, CSVEncodingError, CSVValidationError, CSVColumnError,
    DatabaseConnectionError, FileSystemError, InsufficientStorageError
)
from datetime import datetime

# Import assessment computation function from far.py
from app.api.v1.endpoints.far import _compute_rule_assessment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/far", tags=["FAR Requests"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_far_request(
    title: str = Form(...),
    file: UploadFile = File(...),
    external_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    Create a new FAR request with file upload
    Enhanced with better error handling
    """
    service = FarIngestionService(db)
    created_by = uploader_from_user(user)

    try:
        result = await service.process_upload(
            title=title,
            file=file,
            external_id=external_id,
            created_by=created_by,
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
    except (HTTPException, DatabaseConnectionError, FileSystemError, InsufficientStorageError):
        # Re-raise known exceptions as-is (they're already properly formatted)
        raise
    except Exception as e:
        logger.error(f"Error creating FAR request: {str(e)}", exc_info=True)
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
    try:
        total = db.query(FarRequest).count()
        requests = db.query(FarRequest).offset(skip).limit(limit).all()
        
        # Convert SQLAlchemy models to dictionaries for JSON serialization
        requests_data = []
        for req in requests:
            requests_data.append({
                "id": str(req.id),
                "source_sha256": str(req.source_sha256 or ""),
                "source_size_bytes": req.source_size_bytes,
                "status": str(req.status or ""),
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "source_filename": str(req.source_filename or ""),
                "title": str(req.title or ""),
                "external_id": str(req.external_id or "") if req.external_id else None,
                "storage_path": str(req.storage_path or ""),
                "created_by": str(req.created_by or "")
            })
        
        return success_response(
            data=requests_data,
            message=f"Retrieved {len(requests_data)} of {total} FAR requests",
            metadata={
                "pagination": {
                    "skip": skip,
                    "limit": limit, 
                    "total": total,
                    "returned": len(requests_data),
                    "has_next": skip + len(requests_data) < total,
                    "has_previous": skip > 0
                }
            }
        )
    except OperationalError as e:
        logger.error(f"Database error listing FAR requests: {e}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed",
            details={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error listing FAR requests: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve FAR requests: {str(e)}"
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
            except (PermissionError, OSError) as e:
                # Permission or filesystem error, raise FileSystemError
                logger.error(f"Filesystem error deleting file {file_path}: {str(e)}", exc_info=True)
                raise FileSystemError(
                    message=f"Failed to delete file {file_path}: {str(e)}",
                    details={"filename": far_request.source_filename, "path": file_path}
                )
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
    except (HTTPException, FileSystemError):
        raise
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database connection error deleting FAR request {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed during request deletion",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting FAR request {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete request: {str(e)}")


@router.post("/{request_id}/ingest", status_code=status.HTTP_200_OK)
async def ingest_far_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Process the uploaded file for a FAR request and create firewall rules
    with comprehensive error handling
    """
    # Get the request
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    if far_request.status not in ['submitted', 'processing']:
        raise HTTPException(
            status_code=400, 
            detail=f"Request {request_id} is not in 'submitted' or 'processing' status. Current: {far_request.status}"
        )
    
    try:
        # Update status to processing
        far_request.status = 'processing'
        db.commit()
        
        # Process the file
        full_path = os.path.join("uploads", far_request.storage_path)
        
        if not os.path.exists(full_path):
            far_request.status = 'error'
            db.commit()
            raise HTTPException(
                status_code=404, 
                detail=f"File not found: {far_request.storage_path}"
            )
        
        # Read file as bytes for encoding detection
        async with aiofiles.open(full_path, 'rb') as f:
            file_content_bytes = await f.read()
        
        # Validate and decode
        try:
            file_content, metadata = CSVValidationService.validate_file_structure(
                file_content_bytes,
                filename=far_request.source_filename
            )
        except CSVFileError as e:
            far_request.status = 'error'
            db.commit()
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message
            )
        except CSVEncodingError as e:
            far_request.status = 'error'
            db.commit()
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message
            )
        
        # Process CSV
        csv_service = CsvIngestionService(db)
        
        try:
            result = await csv_service.ingest_csv_file(
                request_id=request_id,
                file_content=file_content
            )
        except CSVValidationError as e:
            far_request.status = 'error'
            db.commit()
            raise HTTPException(
                status_code=400,
                detail={
                    "message": e.message,
                    "details": e.details
                }
            )
        except CSVColumnError as e:
            far_request.status = 'error'
            db.commit()
            raise HTTPException(
                status_code=400,
                detail={
                    "message": e.message,
                    "missing_columns": e.details.get('missing_columns'),
                    "found_columns": e.details.get('found_columns')
                }
            )
        
        # Build response
        ingest_data = {
            "request_id": request_id,
            "rules_created": result.get("created_rules", 0),
            "total_rows": result.get("total_rows", 0),
            "processed_rows": result.get("processed_rows", 0),
            "error_rows": result.get("error_rows", 0),
            "skipped_rows": result.get("skipped_rows", 0),
            "duplicate_rules": result.get("duplicate_rules", 0),
            "ingestion_details": result,
            "status": far_request.status
        }
        
        # Include errors if any (limit to prevent huge responses)
        if result.get("errors"):
            ingest_data["errors"] = result["errors"][:50]  # Limit to first 50
            ingest_data["error_count"] = len(result["errors"])
        
        if result.get("row_errors"):
            ingest_data["row_errors"] = result["row_errors"][:100]  # Limit to first 100
        
        if result.get("warnings"):
            ingest_data["warnings"] = result["warnings"][:50]  # Limit to first 50
        
        return success_response(
            data=ingest_data,
            message=f"CSV ingestion completed: {result.get('created_rules', 0)} rules created, {result.get('error_rows', 0)} errors"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Unexpected errors
        db.rollback()
        far_request.status = 'error'
        db.commit()
        logger.error(f"Unexpected error ingesting request {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during ingestion: {str(e)}"
        )


@router.get("/{request_id}/rules")
def get_far_rules(
    request_id: int,
    skip: int = 0,
    limit: int = 100,
    include_summary: bool = True,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get enhanced, human-readable FAR rules for a request
    
    Returns comprehensive rule information instead of just hashes:
    - Complete source/destination networks
    - Service details (protocols, ports)
    - Human-readable rule summaries
    - Rule statistics and analysis
    
    Query Parameters:
    - skip: Number of rules to skip (pagination)
    - limit: Maximum rules to return (pagination)
    - include_summary: Include summary statistics
    """
    # Verify the request exists
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail="FAR request not found")
    
    # Import models here to avoid circular imports
    from app.models.far_rule import FarRule
    
    # Get rules with their relationships
    rules_query = db.query(FarRule).filter(FarRule.request_id == request_id)
    total_rules = rules_query.count()
    
    rules = rules_query.offset(skip).limit(limit).all()
    
    # Process rules to extract human-readable information
    enhanced_rules = []
    all_sources = set()
    all_destinations = set()
    all_protocols = set()
    allow_rules = 0
    deny_rules = 0
    total_tuple_estimate = 0
    
    for rule in rules:
        # Extract source networks
        source_networks = [
            ep.network_cidr for ep in rule.endpoints 
            if ep.endpoint_type == 'source'
        ]
        all_sources.update(source_networks)
        
        # Extract destination networks
        destination_networks = [
            ep.network_cidr for ep in rule.endpoints 
            if ep.endpoint_type == 'destination'
        ]
        all_destinations.update(destination_networks)
        
        # Extract protocols and ports
        protocols = []
        port_ranges = []
        for service in rule.services:
            protocols.append(service.protocol)
            port_ranges.append(str(service.port_ranges))
            all_protocols.add(service.protocol)
        
        # Count rule types
        if str(rule.action).upper() == 'ALLOW':
            allow_rules += 1
        elif str(rule.action).upper() == 'DENY':
            deny_rules += 1
        
        # Calculate tuple estimate for this rule
        tuple_estimate = len(source_networks) * len(destination_networks) * len(rule.services)
        total_tuple_estimate += tuple_estimate
        
        # Generate human-readable summary
        rule_summary = _generate_rule_summary(
            str(rule.action), source_networks, destination_networks, protocols, port_ranges
        )
        
        # Compute assessment data from facts
        # Ensure facts is a dict (SQLAlchemy ORM should return the value, but verify)
        facts_raw = rule.facts
        if facts_raw is not None and isinstance(facts_raw, dict):
            facts: Optional[Dict[str, Any]] = cast(Dict[str, Any], facts_raw)
        else:
            facts = None
        assessment = _compute_rule_assessment(facts)
        
        # Create enhanced rule data in the format expected by frontend
        enhanced_rule_dict = {
            'id': rule.id,
            'action': rule.action,
            'direction': rule.direction,
            'source_networks': source_networks,
            'source_count': len(source_networks),
            'destination_networks': destination_networks,
            'destination_count': len(destination_networks),
            'protocols': protocols,
            'port_ranges': port_ranges,
            'service_count': len(rule.services),
            'created_at': rule.created_at.isoformat(),
            'rule_hash': rule.canonical_hash.hex() if rule.canonical_hash is not None else None,
            'tuple_estimate': tuple_estimate,
            'rule_summary': rule_summary,
            'health_status': assessment["health_status"],
            'problem_count': assessment["problem_count"],
            'criticality_score': assessment["criticality_score"],
            # Add endpoints array with proper structure for frontend
            'endpoints': [
                {
                    'endpoint_type': 'source',
                    'network_cidr': cidr,
                    'cidr': cidr,
                    'type': 'source'
                }
                for cidr in source_networks
            ] + [
                {
                    'endpoint_type': 'destination',
                    'network_cidr': cidr,
                    'cidr': cidr,
                    'type': 'destination'
                }
                for cidr in destination_networks
            ],
            # Add services array with proper structure for frontend
            'services': [
                {
                    'protocol': protocol,
                    'port_ranges': port_ranges[i] if i < len(port_ranges) else '',
                    'ports': port_ranges[i] if i < len(port_ranges) else ''
                }
                for i, protocol in enumerate(protocols)
            ]
        }
        
        # Add facts if available
        if rule.facts:
            enhanced_rule_dict['facts'] = rule.facts
        
        enhanced_rules.append(enhanced_rule_dict)
    
    # Create summary if requested
    summary = FarRulesSummaryModel(
        total_rules=total_rules,
        allow_rules=allow_rules,
        deny_rules=deny_rules,
        unique_sources=len(all_sources),
        unique_destinations=len(all_destinations),
        protocols_used=list(all_protocols),
        estimated_tuples=total_tuple_estimate
    ) if include_summary else FarRulesSummaryModel(
        total_rules=0,
        allow_rules=0,
        deny_rules=0,
        unique_sources=0,
        unique_destinations=0,
        protocols_used=[],
        estimated_tuples=0
    )
    
    # Create pagination info
    pagination = {
        "skip": skip,
        "limit": limit,
        "total": total_rules,
        "returned": len(enhanced_rules),
        "has_next": skip + limit < total_rules,
        "has_previous": skip > 0
    }
    
    # Create response data - use dicts directly to include endpoints and services
    # that frontend expects but aren't in RuleDetailModel schema
    response_data = {
        "far_request_id": request_id,
        "summary": summary.model_dump() if hasattr(summary, 'model_dump') else summary.dict(),
        "rules": enhanced_rules,  # Keep as dicts to include endpoints/services
        "pagination": pagination,
        "metadata": {
            "request_title": far_request.title,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "processing_notes": "Enhanced human-readable rule format"
        }
    }
    
    response = StandardResponse(
        status=StatusEnum.SUCCESS,
        message=f"Retrieved {len(enhanced_rules)} enhanced rules for FAR request {request_id}",
        data=response_data,
        errors=None,
        metadata={
            "api_version": "2.0",
            "enhancement": "human_readable_rules"
        },
        request_id=None
    )
    
    # Convert to dict to match return type annotation
    return response.model_dump(exclude_none=True) if hasattr(response, 'model_dump') else response.dict(exclude_none=True)


def _generate_rule_summary(action: str, sources: List[str], destinations: List[str], 
                          protocols: List[str], ports: List[str]) -> str:
    """
    Generate a human-readable summary of a firewall rule
    """
    # Simplify network lists for display
    src_display = f"{len(sources)} source{'s' if len(sources) != 1 else ''}"
    if len(sources) == 1:
        src_display = sources[0]
    elif len(sources) <= 3:
        src_display = ", ".join(sources)
    
    dst_display = f"{len(destinations)} destination{'s' if len(destinations) != 1 else ''}"
    if len(destinations) == 1:
        dst_display = destinations[0]
    elif len(destinations) <= 3:
        dst_display = ", ".join(destinations)
    
    # Simplify protocol/port display
    service_display = ""
    if protocols:
        if len(protocols) == 1:
            protocol = protocols[0].upper()
            if ports and len(ports) == 1:
                service_display = f" on {protocol} port {ports[0]}"
            else:
                service_display = f" using {protocol}"
        else:
            service_display = f" using {'/'.join(set(protocols)).upper()}"
    
    return f"{action.upper()}: {src_display} → {dst_display}{service_display}"
