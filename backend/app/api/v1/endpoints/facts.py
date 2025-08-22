"""
Phase 2.3 Facts Computation API endpoint
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.services.facts_computation_service import FactsComputationService

router = APIRouter()


@router.post("/requests/{request_id}/facts/compute", status_code=status.HTTP_200_OK)
async def compute_facts_for_request(
    request_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Compute policy-independent facts for all rules in a request.
    
    This endpoint processes all FAR rules for the given request and computes
    various facts such as:
    - Any/Any presence (0.0.0.0/0)
    - Self-flow detection (source/destination overlap)
    - Public/Private IP classification
    - Special IP ranges (multicast, link-local, loopback, broadcast)
    - Service shape metrics
    - Expansion estimates
    
    Args:
        request_id: ID of the FAR request to process
        
    Returns:
        Dict containing computation statistics:
        - request_id: The processed request ID
        - rules_total: Total number of rules in the request
        - rules_updated: Number of rules successfully updated with facts
        - self_flow_count: Number of rules with self-flow detected
        - src_any: Number of rules with source = 0.0.0.0/0
        - dst_any: Number of rules with destination = 0.0.0.0/0
        - public_src: Number of rules with public source IPs
        - public_dst: Number of rules with public destination IPs
        - duration_ms: Time taken for computation in milliseconds
        
    Raises:
        HTTPException 404: If request not found
        HTTPException 409: If request has no rules (ingestion not run)
    """
    
    try:
        service = FactsComputationService(db)
        result = await service.compute_facts_for_request(request_id)
        return result
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        elif "no rules" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Request {request_id} has no rules - run ingestion first"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Facts computation failed: {error_msg}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during facts computation: {str(e)}"
        )
