"""
Database models
DEPRECATED: Use app.models instead
"""
# Import from new location for backward compatibility
from app.models import Item, FarRequest

__all__ = ["Item", "FarRequest"]
