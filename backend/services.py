"""
Service layer for FAR request processing
DEPRECATED: Use app.services instead
"""
# Import from new location for backward compatibility
from app.services import FarIngestionService

__all__ = ["FarIngestionService"]
