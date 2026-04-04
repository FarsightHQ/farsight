"""
API v1 router
"""
from fastapi import APIRouter, Depends

from app.core.auth import get_current_user

from .endpoints import requests, rules, analysis
from .endpoints import facts, asset_registry
from .endpoints import ip_rules, hybrid_facts, test_system, auth

# Create main v1 router with authentication dependency
# All endpoints under /api/v1 will require authentication
router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

# Include the new decomposed endpoint routers
router.include_router(requests.router, tags=["FAR Requests"])
router.include_router(rules.router, tags=["FAR Rules"])
router.include_router(analysis.router, tags=["FAR Analysis"])

# Include other existing endpoint routers
router.include_router(ip_rules.router, tags=["IP Rules"])
router.include_router(facts.router, tags=["Facts"])
router.include_router(hybrid_facts.router, tags=["Facts"])
router.include_router(asset_registry.router, tags=["Asset Registry"])
router.include_router(test_system.router, tags=["System Test"])
router.include_router(auth.router, tags=["Authentication"])
