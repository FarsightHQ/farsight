"""
API v1 router
"""
from fastapi import APIRouter

from .endpoints import far, items
from .endpoints import ip_rules

# Create main v1 router
router = APIRouter()

# Include endpoint routers
router.include_router(far.router)
router.include_router(items.router)
router.include_router(ip_rules.router, tags=["IP Rules"])
