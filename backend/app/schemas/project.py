"""Pydantic schemas for project workspaces."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

ProjectRole = Literal["viewer", "member", "admin", "owner"]


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    legacy_unrestricted: bool
    created_at: datetime
    created_by_sub: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectMemberOut(BaseModel):
    user_sub: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    user_sub: str = Field(..., min_length=1, max_length=512)
    role: ProjectRole = "member"


class InvitationCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    role: ProjectRole = "member"


class InvitationCreatedOut(BaseModel):
    invitation_id: int
    expires_at: datetime
    token: str
    accept_path: str


class InvitationAccept(BaseModel):
    token: str = Field(..., min_length=8)


class ProjectListOut(BaseModel):
    projects: List[ProjectOut]
