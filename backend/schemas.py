"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FarRequestResponse(BaseModel):
    """Response model for FAR request submissions"""
    request_id: int
    status: str
    file: "FileInfo"
    metadata: "RequestMetadata"

    class Config:
        from_attributes = True


class FileInfo(BaseModel):
    """File information in the response"""
    filename: str
    sha256: str
    size_bytes: int
    storage_path: str


class RequestMetadata(BaseModel):
    """Metadata information in the response"""
    title: str
    external_id: Optional[str] = None
    created_by: str


class FarRequestCreate(BaseModel):
    """Internal model for creating FAR requests"""
    title: str
    external_id: Optional[str] = None
    source_filename: str
    source_sha256: str
    source_size_bytes: int
    storage_path: str
    status: str = "submitted"
    created_by: str = "system"


# Update forward references
FarRequestResponse.model_rebuild()
