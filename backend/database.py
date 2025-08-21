"""
Database configuration and connection management
DEPRECATED: Use app.core.database instead
"""
# Import from new location for backward compatibility
from app.core.database import engine, SessionLocal, Base, get_db

__all__ = ["engine", "SessionLocal", "Base", "get_db"]
