"""
FastAPI application entry point
DEPRECATED: Use app.main instead
"""
# Import from new location for backward compatibility
from app.main import app

__all__ = ["app"]
