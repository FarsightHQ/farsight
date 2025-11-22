"""
Hybrid Facts API Endpoint
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.core.database import get_db, SessionLocal
from app.services.hybrid_facts_service import HybridFactsService
from app.utils.error_handlers import success_response
from app.utils.csv_errors import DatabaseConnectionError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/far")

@router.post("/{request_id}/facts/compute-hybrid")
async def compute_hybrid_facts(request_id: int, db: Session = Depends(get_db)):
    """
    Compute hybrid facts for a FAR request
    
    Uses selective tuple storage:
    - Rule-level facts for fast aggregation
    - Tuple-level facts only for problematic/interesting tuples
    """
    try:
        # Get the FAR request
        from app.models.far_request import FarRequest
        from app.models.far_rule import FarRule, FarRuleEndpoint
        
        far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
        if not far_request:
            raise HTTPException(status_code=404, detail="FAR request not found")
        
        # Get rules for this request to extract CIDRs, ports, protocols
        rules = db.query(FarRule).filter(FarRule.request_id == request_id).all()
        if not rules:
            raise HTTPException(status_code=404, detail="No rules found for this request")
        
        # Extract unique CIDRs, ports, protocols from rules and their endpoints
        source_cidrs = set()
        destination_cidrs = set()
        port_ranges = set()
        protocols = set()
        
        for rule in rules:
            # Get endpoints for this rule
            endpoints = db.query(FarRuleEndpoint).filter(FarRuleEndpoint.rule_id == rule.id).all()
            
            for endpoint in endpoints:
                if endpoint.endpoint_type == 'source':
                    source_cidrs.add(endpoint.network_cidr)
                elif endpoint.endpoint_type == 'destination':
                    destination_cidrs.add(endpoint.network_cidr)
            
            # Note: Services/ports are in separate table, for now using placeholder
            if hasattr(rule, 'services') and rule.services:
                for service in rule.services:
                    if hasattr(service, 'port_range'):
                        port_ranges.add(service.port_range)
                    if hasattr(service, 'protocol'):
                        protocols.add(service.protocol)
            else:
                # Fallback to common defaults for demonstration
                port_ranges.add("80")
                port_ranges.add("443")
                protocols.add("tcp")
        
        # Prepare request data for the service
        request_data = {
            'source_cidrs': list(source_cidrs),
            'destination_cidrs': list(destination_cidrs),
            'port_ranges': list(port_ranges),
            'protocols': list(protocols)
        }
        
        service = HybridFactsService(db)
        result = await service.compute_hybrid_facts_for_request(request_data, db)
        
        # Add request context to result
        result['request_id'] = request_id
        result['request_title'] = far_request.title
        
        return success_response(
            data=result,
            message=f"Successfully computed hybrid facts for request {request_id}"
        )
    except HTTPException:
        raise
    except DatabaseConnectionError:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error computing hybrid facts for request {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed during hybrid facts computation",
            details={"error": str(e), "request_id": request_id}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error computing hybrid facts for request {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Facts computation failed: {str(e)}")

@router.get("/{request_id}/facts/hybrid-summary")
async def get_hybrid_facts_summary(request_id: int, db: Session = Depends(get_db)):
    """
    Get hybrid facts summary for a request
    Shows both rule-level aggregates and tuple-level details
    """
    try:
        # Rule-level summary
        rule_summary = db.execute(
            text("""
            SELECT 
                COUNT(*) as total_rules,
                COUNT(CASE WHEN r.facts->>'health_status' = 'clean' THEN 1 END) as clean_rules,
                COUNT(CASE WHEN r.facts->>'health_status' = 'critical' THEN 1 END) as critical_rules,
                SUM((r.facts->'tuple_summary'->>'total_count')::int) as total_tuples,
                SUM((r.facts->'tuple_summary'->>'clean_count')::int) as clean_tuples,
                SUM((r.facts->'tuple_summary'->>'problem_count')::int) as problem_tuples
            FROM far_rules r
            WHERE r.request_id = :request_id AND r.facts IS NOT NULL
            """),
            {"request_id": request_id}
        ).fetchone()
        
        # Tuple-level details (only stored problematic tuples)
        tuple_details = db.execute(
            text("""
            SELECT 
                COUNT(*) as stored_tuples,
                COUNT(CASE WHEN tf.facts->>'is_clean' = 'false' THEN 1 END) as problematic_tuples,
                array_agg(DISTINCT tf.facts->>'primary_violation') FILTER (WHERE tf.facts->>'primary_violation' IS NOT NULL) as violation_types
            FROM far_tuple_facts tf
            JOIN far_rules r ON tf.rule_id = r.id
            WHERE r.request_id = :request_id
            """),
            {"request_id": request_id}
        ).fetchone()

        # Handle None results safely
        rule_summary = rule_summary or (0, 0, 0, 0, 0, 0)
        tuple_details = tuple_details or (0, 0, [])
        
        hybrid_summary_data = {
            "request_id": request_id,
            "rule_summary": {
                "total_rules": rule_summary[0] or 0,
                "clean_rules": rule_summary[1] or 0,
                "critical_rules": rule_summary[2] or 0,
                "total_tuples": rule_summary[3] or 0,
                "clean_tuples": rule_summary[4] or 0,
                "problem_tuples": rule_summary[5] or 0
            },
            "tuple_details": {
                "stored_tuples": tuple_details[0] or 0,
                "problematic_tuples": tuple_details[1] or 0,
                "violation_types": tuple_details[2] or []
            }
        }
        
        return success_response(
            data=hybrid_summary_data,
            message=f"Retrieved hybrid facts summary for request {request_id}"
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting hybrid facts summary for request {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving hybrid facts summary",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"Error getting hybrid facts summary for request {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get hybrid summary: {str(e)}")

@router.get("/{request_id}/tuples/problematic")
async def get_problematic_tuples(request_id: int, db: Session = Depends(get_db)):
    """
    Get only the problematic tuples for detailed analysis
    """
    try:
        result = db.execute(
            text("""
            SELECT 
                r.id as rule_id,
                tf.source_cidr,
                tf.destination_cidr,
                tf.facts
            FROM far_tuple_facts tf
            JOIN far_rules r ON tf.rule_id = r.id
            WHERE r.request_id = :request_id 
              AND tf.facts->>'is_clean' = 'false'
            ORDER BY r.id, tf.source_cidr, tf.destination_cidr
            """),
            {"request_id": request_id}
        ).fetchall()
        
        problematic_tuples_data = {
            "request_id": request_id,
            "problematic_tuples": [
                {
                    "rule_id": row[0],
                    "source_cidr": row[1],
                    "destination_cidr": row[2],
                    "facts": row[3]
                }
                for row in result
            ]
        }
        
        return success_response(
            data=problematic_tuples_data,
            message=f"Retrieved {len(result)} problematic tuples for request {request_id}"
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting problematic tuples for request {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving problematic tuples",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"Error getting problematic tuples for request {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get problematic tuples: {str(e)}")
