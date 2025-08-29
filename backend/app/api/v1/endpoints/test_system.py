"""
Simple test endpoint for system validation
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.error_handlers import success_response

router = APIRouter()

@router.get("/test/system")
async def test_system(db: Session = Depends(get_db)):
    """Test basic system functionality"""
    try:
        # Test database connection
        from sqlalchemy import text
        result = db.execute(text("SELECT 1 as test")).fetchone()
        
        # Test basic queries
        from app.models.far_request import FarRequest
        request_count = db.query(FarRequest).count()
        
        from app.models.far_rule import FarRule  
        rule_count = db.query(FarRule).count()
        
        # Test hybrid facts service import
        from app.services.hybrid_facts_service import HybridFactsService
        service = HybridFactsService(db)
        
        system_data = {
            "database": "connected",
            "test_query": result[0] if result else None,
            "far_requests": request_count,
            "far_rules": rule_count,
            "hybrid_service": "loaded successfully",
            "system_status": "✅ System is working!"
        }
        
        return success_response(
            data=system_data,
            message="System test completed successfully"
        )
        
    except Exception as e:
        error_data = {
            "system_status": "❌ System has issues",
            "error": str(e),
            "error_type": type(e).__name__
        }
        
        return success_response(
            data=error_data,
            message="System test completed with errors"
        )
