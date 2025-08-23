"""
Simple test endpoint for system validation
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

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
        
        return {
            "status": "✅ System is working!",
            "database": "connected",
            "test_query": result[0] if result else None,
            "far_requests": request_count,
            "far_rules": rule_count,
            "hybrid_service": "loaded successfully"
        }
        
    except Exception as e:
        return {
            "status": "❌ System has issues",
            "error": str(e),
            "error_type": type(e).__name__
        }
