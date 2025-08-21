"""
Configuration settings for the application
DEPRECATED: Use app.core.config instead
"""
# Import from new location for backward compatibility
from app.core.config import Settings, settings

__all__ = ["Settings", "settings"]
