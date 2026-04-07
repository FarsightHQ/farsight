"""
Pydantic schemas for FAR (File Analysis Request) operations
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FarRequestResponse(BaseModel):
    """Response model for FAR request submissions"""
    id: int
    project_id: int
    title: str
    external_id: Optional[str] = None
    source_filename: str
    source_sha256: str
    source_size_bytes: int
    storage_path: str
    status: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class FarRequestCreate(BaseModel):
    """Internal model for creating FAR requests"""
    project_id: int
    title: str
    external_id: Optional[str] = None
    source_filename: str
    source_sha256: str
    source_size_bytes: int
    storage_path: str
    status: str = "submitted"
    created_by: str = "system"


FarRequestResponse.model_rebuild()
