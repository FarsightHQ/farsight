"""
API v1 router
"""
from fastapi import APIRouter

from .endpoints import far, facts
from .endpoints import ip_rules, hybrid_facts, test_system

# Create main v1 router
router = APIRouter()

# Include endpoint routers
router.include_router(far.router)
router.include_router(ip_rules.router, tags=["IP Rules"])
router.include_router(facts.router, tags=["Facts"])
router.include_router(hybrid_facts.router, tags=["Hybrid Facts"])
router.include_router(test_system.router, tags=["System Test"])
