"""
Main API router
"""
from fastapi import APIRouter

from .v1.router import router as v1_router

# Create main API router
router = APIRouter()

# Include version routers with prefix
router.include_router(v1_router, prefix="/api/v1")
