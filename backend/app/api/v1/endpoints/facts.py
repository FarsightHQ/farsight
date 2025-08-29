"""
Phase 2.3 Facts Computation API endpoint
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.services.facts_computation_service import FactsComputationService
from app.utils.error_handlers import success_response

router = APIRouter()


@router.post(
    "/requests/{request_id}/facts/compute", 
    status_code=status.HTTP_200_OK,
    summary="Compute Rule Facts",
    description="Compute detailed facts for all firewall rules in a request",
    responses={
        200: {
            "description": "Facts computed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "request_id": 31,
                        "rules_total": 59,
                        "rules_updated": 59,
                        "self_flow_count": 8,
                        "src_any": 0,
                        "dst_any": 0,
                        "public_src": 0,
                        "public_dst": 0,
                        "duration_ms": 68
                    }
                }
            }
        },
        404: {"description": "Request not found"},
        409: {"description": "Request has no rules - run ingestion first"}
    }
)
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
        
        return success_response(
            data=result,
            message=f"Successfully computed facts for request {request_id}"
        )
        
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


@router.get("/requests/{request_id}/analysis", status_code=status.HTTP_200_OK)
async def get_request_analysis(
    request_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive analysis of a FAR request for UI display.
    
    This endpoint provides a complete overview of a processed FAR request including:
    - Request metadata
    - Rule statistics and facts summary  
    - Security and risk analysis
    - Tuple facts insights
    - Network topology breakdown
    
    Args:
        request_id: ID of the FAR request to analyze
        
    Returns:
        Dict containing comprehensive analysis data for UI display
        
    Raises:
        HTTPException 404: If request not found
    """
    try:
        from app.models.far_request import FarRequest
        from app.models.far_rule import FarRule
        from app.models.far_tuple_facts import FarTupleFacts
        from sqlalchemy import func, text
        import json
        
        # Get request info
        far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
        if not far_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        # Get basic rule statistics
        rule_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_rules,
                COUNT(CASE WHEN facts IS NOT NULL THEN 1 END) as rules_with_facts,
                SUM((facts->>'service_count')::int) as total_services,
                SUM((facts->>'tuple_estimate')::int) as total_estimated_tuples
            FROM far_rules 
            WHERE request_id = :request_id
        """), {"request_id": request_id}).fetchone()
        
        # Get detailed facts analysis
        detailed_facts = db.execute(text("""
            SELECT 
                COUNT(CASE WHEN (facts->>'src_is_any')::boolean = true THEN 1 END) as src_any_count,
                COUNT(CASE WHEN (facts->>'dst_is_any')::boolean = true THEN 1 END) as dst_any_count,
                COUNT(CASE WHEN (facts->>'is_self_flow')::boolean = true THEN 1 END) as self_flow_count,
                COUNT(CASE WHEN (facts->>'src_has_public')::boolean = true THEN 1 END) as src_public_count,
                COUNT(CASE WHEN (facts->>'dst_has_public')::boolean = true THEN 1 END) as dst_public_count,
                COUNT(CASE WHEN (facts->>'src_has_loopback')::boolean = true THEN 1 END) as src_loopback_count,
                COUNT(CASE WHEN (facts->>'dst_has_loopback')::boolean = true THEN 1 END) as dst_loopback_count,
                COUNT(CASE WHEN (facts->>'expansion_capped')::boolean = true THEN 1 END) as expansion_capped_count,
                AVG((facts->>'max_port_span')::int) as avg_port_span
            FROM far_rules 
            WHERE request_id = :request_id AND facts IS NOT NULL
        """), {"request_id": request_id}).fetchone()
        
        # Get tuple facts analysis
        tuple_facts_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_tuple_facts,
                COUNT(DISTINCT rule_id) as rules_with_tuple_facts
            FROM far_tuple_facts tf
            JOIN far_rules r ON tf.rule_id = r.id
            WHERE r.request_id = :request_id
        """), {"request_id": request_id}).fetchone()
        
        # Get sample rules with interesting facts
        sample_rules = db.execute(text("""
            SELECT 
                id,
                facts,
                (SELECT COUNT(*) FROM far_tuple_facts WHERE rule_id = fr.id) as tuple_facts_count
            FROM far_rules fr
            WHERE request_id = :request_id AND facts IS NOT NULL
            ORDER BY 
                (facts->>'tuple_estimate')::int DESC,
                (CASE WHEN (facts->>'is_self_flow')::boolean = true THEN 1 ELSE 0 END) DESC
            LIMIT 5
        """), {"request_id": request_id}).fetchall()
        
        # Build comprehensive analysis
        analysis = {
            "request_info": {
                "id": far_request.id,
                "title": far_request.title,
                "created_at": far_request.created_at.isoformat(),
                "file_path": getattr(far_request, 'file_path', 'N/A')
            },
            "overview": {
                "total_rules": rule_stats.total_rules if rule_stats else 0,
                "rules_with_facts": rule_stats.rules_with_facts if rule_stats else 0,
                "total_services": rule_stats.total_services if rule_stats else 0,
                "total_estimated_tuples": rule_stats.total_estimated_tuples if rule_stats else 0,
                "total_tuple_facts_stored": tuple_facts_stats.total_tuple_facts if tuple_facts_stats else 0,
                "rules_with_stored_tuples": tuple_facts_stats.rules_with_tuple_facts if tuple_facts_stats else 0
            },
            "security_analysis": {
                "any_source_rules": detailed_facts.src_any_count if detailed_facts else 0,
                "any_destination_rules": detailed_facts.dst_any_count if detailed_facts else 0,
                "self_flow_rules": detailed_facts.self_flow_count if detailed_facts else 0,
                "public_source_rules": detailed_facts.src_public_count if detailed_facts else 0,
                "public_destination_rules": detailed_facts.dst_public_count if detailed_facts else 0,
                "loopback_source_rules": detailed_facts.src_loopback_count if detailed_facts else 0,
                "loopback_destination_rules": detailed_facts.dst_loopback_count if detailed_facts else 0,
                "expansion_capped_rules": detailed_facts.expansion_capped_count if detailed_facts else 0
            },
            "network_topology": {
                "average_port_span": float(detailed_facts.avg_port_span) if detailed_facts and detailed_facts.avg_port_span else 0,
                "completion_percentage": round((rule_stats.rules_with_facts / rule_stats.total_rules * 100) if rule_stats and rule_stats.total_rules > 0 else 0, 1)
            },
            "sample_rules": [
                {
                    "rule_id": rule.id,
                    "facts": rule.facts if isinstance(rule.facts, dict) else json.loads(rule.facts) if rule.facts else {},
                    "tuple_facts_stored": rule.tuple_facts_count
                }
                for rule in sample_rules
            ]
        }
        
        return success_response(
            data=analysis,
            message=f"Retrieved comprehensive analysis for request {request_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating analysis: {str(e)}"
        )
