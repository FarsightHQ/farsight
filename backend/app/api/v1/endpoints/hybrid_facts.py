"""
Hybrid Facts API Endpoint
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.services.hybrid_facts_service import HybridFactsService

router = APIRouter()

@router.post("/requests/{request_id}/facts/compute-hybrid")
async def compute_hybrid_facts(request_id: int, db: Session = Depends(get_db)):
    """
    Compute hybrid facts for a FAR request
    
    Uses selective tuple storage:
    - Rule-level facts for fast aggregation
    - Tuple-level facts only for problematic/interesting tuples
    """
    try:
        service = HybridFactsService(db)
        result = await service.compute_hybrid_facts_for_request(request_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Facts computation failed: {str(e)}")

@router.get("/requests/{request_id}/facts/hybrid-summary")
async def get_hybrid_facts_summary(request_id: int, db: Session = Depends(get_db)):
    """
    Get hybrid facts summary for a request
    Shows both rule-level aggregates and tuple-level details
    """
    try:
        # Rule-level summary
        rule_summary = db.execute(
            """
            SELECT 
                COUNT(*) as total_rules,
                COUNT(CASE WHEN facts->>'health_status' = 'clean' THEN 1 END) as clean_rules,
                COUNT(CASE WHEN facts->>'health_status' = 'critical' THEN 1 END) as critical_rules,
                SUM((facts->'tuple_summary'->>'total_count')::int) as total_tuples,
                SUM((facts->'tuple_summary'->>'clean_count')::int) as clean_tuples,
                SUM((facts->'tuple_summary'->>'problem_count')::int) as problem_tuples
            FROM far_rules 
            WHERE request_id = :request_id AND facts IS NOT NULL
            """,
            {"request_id": request_id}
        ).fetchone()
        
        # Tuple-level details (only stored problematic tuples)
        tuple_details = db.execute(
            """
            SELECT 
                COUNT(*) as stored_tuples,
                COUNT(CASE WHEN facts->>'is_clean' = 'false' THEN 1 END) as problematic_tuples,
                array_agg(DISTINCT facts->>'primary_violation') FILTER (WHERE facts->>'primary_violation' IS NOT NULL) as violation_types
            FROM far_tuple_facts tf
            JOIN far_rules r ON tf.rule_id = r.id
            WHERE r.request_id = :request_id
            """,
            {"request_id": request_id}
        ).fetchone()
        
        return {
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get hybrid summary: {str(e)}")

@router.get("/requests/{request_id}/tuples/problematic")
async def get_problematic_tuples(request_id: int, db: Session = Depends(get_db)):
    """
    Get only the problematic tuples for detailed analysis
    """
    try:
        result = db.execute(
            """
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
            """,
            {"request_id": request_id}
        ).fetchall()
        
        return {
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get problematic tuples: {str(e)}")
