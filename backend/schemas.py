"""
Pydantic schemas for API request/response models
DEPRECATED: Use app.schemas instead
"""
# Import from new location for backward compatibility
from app.schemas import (
    FarRequestResponse, 
    FileInfo, 
    RequestMetadata, 
    FarRequestCreate,
    ItemBase,
    ItemCreate, 
    ItemResponse
)

__all__ = [
    "FarRequestResponse", 
    "FileInfo", 
    "RequestMetadata", 
    "FarRequestCreate",
    "ItemBase",
    "ItemCreate", 
    "ItemResponse"
]
