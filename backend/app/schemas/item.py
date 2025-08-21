"""
Pydantic schemas for Item operations
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ItemBase(BaseModel):
    """Base schema for Item"""
    name: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    """Schema for creating items"""
    pass


class ItemResponse(ItemBase):
    """Schema for item responses"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
