"""
Project-scoped authorization (membership + legacy unrestricted projects).
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.far_request import FarRequest
from app.models.project import Project, ProjectMember

logger = logging.getLogger(__name__)

ROLE_RANK = {
    "viewer": 0,
    "member": 1,
    "admin": 2,
    "owner": 3,
}

DEFAULT_ADMIN_REALM_ROLES = ("farsight-admin", "admin")


def _rank(role: str) -> int:
    r = ROLE_RANK.get((role or "").lower())
    if r is None:
        return -1
    return r


def user_has_platform_admin_bypass(user: dict) -> bool:
    roles = [r.lower() for r in (user.get("roles") or [])]
    return any(r in roles for r in DEFAULT_ADMIN_REALM_ROLES)


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def require_project_access(
    db: Session,
    project_id: int,
    user: dict,
    min_role: str = "viewer",
) -> Project:
    """
    Ensure user may access the project at least at min_role.
    legacy_unrestricted projects allow any authenticated user (viewer+).
    Platform admin realm roles bypass membership checks.
    """
    project = get_project_or_404(db, project_id)
    if user_has_platform_admin_bypass(user):
        return project
    if project.legacy_unrestricted:
        return project
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_sub == user.get("sub"),
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )
    if _rank(member.role) < _rank(min_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient project role",
        )
    return project


def get_far_request_in_project_or_404(
    db: Session,
    request_id: int,
    project_id: int,
) -> FarRequest:
    req = (
        db.query(FarRequest)
        .filter(FarRequest.id == request_id, FarRequest.project_id == project_id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAR request not found")
    return req


def require_project_role_dep(min_role: str) -> Callable:
    async def _dep(
        project_id: int,
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        require_project_access(db, project_id, user, min_role=min_role)

    return _dep


async def require_project_viewer(
    project_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    require_project_access(db, project_id, user, min_role="viewer")
