"""
Project CRUD, members, invitations.
"""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.project_auth import (
    get_project_or_404,
    require_project_access,
    user_has_platform_admin_bypass,
)
from app.models.far_request import FarRequest
from app.models.project import Project, ProjectInvitation, ProjectMember
from app.schemas.project import (
    InvitationAccept,
    InvitationCreate,
    InvitationCreatedOut,
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberOut,
    ProjectOut,
    ProjectUpdate,
)
from app.utils.error_handlers import success_response

router = APIRouter(prefix="/projects", tags=["Projects"])
invitations_router = APIRouter(prefix="/invitations", tags=["Projects"])


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower().strip()).strip("-")
    return (s[:180] if s else "project") or "project"


def _unique_slug(db: Session, base: str) -> str:
    slug = base
    n = 0
    while db.query(Project.id).filter(Project.slug == slug).first():
        n += 1
        suffix = f"-{n}"
        slug = (base[: 180 - len(suffix)] + suffix) if len(base) + len(suffix) > 180 else base + suffix
    return slug


def _projects_visible_to_user(db: Session, user: dict) -> List[Project]:
    sub = user.get("sub")
    q = (
        db.query(Project)
        .outerjoin(ProjectMember, ProjectMember.project_id == Project.id)
        .filter(
            or_(
                Project.legacy_unrestricted.is_(True),
                ProjectMember.user_sub == sub,
            )
        )
        .distinct()
        .order_by(Project.name)
    )
    return q.all()


@router.get("")
def list_projects(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    if user_has_platform_admin_bypass(user):
        projects = db.query(Project).order_by(Project.name).all()
    else:
        projects = _projects_visible_to_user(db, user)
    return success_response(
        data={"projects": [ProjectOut.model_validate(p).model_dump() for p in projects]},
        message=f"Found {len(projects)} project(s)",
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    sub = user.get("sub")
    if not sub:
        raise HTTPException(status_code=400, detail="Missing user sub")
    base = _slugify(body.name)
    slug = _unique_slug(db, base)
    p = Project(
        name=body.name.strip(),
        slug=slug,
        description=body.description,
        legacy_unrestricted=False,
        created_by_sub=sub,
    )
    db.add(p)
    db.flush()
    db.add(
        ProjectMember(
            project_id=p.id,
            user_sub=sub,
            role="owner",
        )
    )
    db.commit()
    db.refresh(p)
    return success_response(
        data=ProjectOut.model_validate(p).model_dump(),
        message="Project created",
        metadata={"status_code": status.HTTP_201_CREATED},
    )


@router.get("/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_project_access(db, project_id, user, "viewer")
    p = get_project_or_404(db, project_id)
    return success_response(data=ProjectOut.model_validate(p).model_dump())


@router.patch("/{project_id}")
def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_project_access(db, project_id, user, "admin")
    p = get_project_or_404(db, project_id)
    if body.name is not None:
        p.name = body.name.strip()
    if body.description is not None:
        p.description = body.description
    db.commit()
    db.refresh(p)
    return success_response(data=ProjectOut.model_validate(p).model_dump(), message="Project updated")


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_project_access(db, project_id, user, "owner")
    p = get_project_or_404(db, project_id)
    if p.slug == "default":
        raise HTTPException(
            status_code=400,
            detail="The default migrated project cannot be deleted",
        )
    far_count = db.query(FarRequest).filter(FarRequest.project_id == project_id).count()
    if far_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Project still has FAR requests; delete or move them first",
        )
    db.delete(p)
    db.commit()
    return success_response(data={"deleted": True}, message="Project deleted")


@router.get("/{project_id}/members")
def list_members(
    project_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_project_access(db, project_id, user, "viewer")
    members = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.role.desc(), ProjectMember.user_sub)
        .all()
    )
    return success_response(
        data={
            "members": [ProjectMemberOut.model_validate(m).model_dump() for m in members],
        }
    )


@router.post("/{project_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(
    project_id: int,
    body: ProjectMemberAdd,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_project_access(db, project_id, user, "admin")
    exists = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_sub == body.user_sub,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="User is already a member")
    db.add(
        ProjectMember(
            project_id=project_id,
            user_sub=body.user_sub,
            role=body.role,
        )
    )
    db.commit()
    m = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_sub == body.user_sub,
        )
        .first()
    )
    return success_response(
        data=ProjectMemberOut.model_validate(m).model_dump(),
        message="Member added",
    )


@router.delete("/{project_id}/members/{user_sub:path}")
def remove_member(
    project_id: int,
    user_sub: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_project_access(db, project_id, user, "admin")
    target = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_sub == user_sub,
        )
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    if target.role == "owner":
        owners = (
            db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.role == "owner",
            )
            .count()
        )
        if owners <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last owner")
    db.delete(target)
    db.commit()
    return success_response(data={"removed": True}, message="Member removed")


@router.post("/{project_id}/invitations", status_code=status.HTTP_201_CREATED)
def create_invitation(
    project_id: int,
    body: InvitationCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    require_project_access(db, project_id, user, "admin")
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=7)
    inv = ProjectInvitation(
        project_id=project_id,
        email=body.email.strip().lower(),
        role=body.role,
        token_hash=token_hash,
        invited_by_sub=user.get("sub"),
        expires_at=expires_at,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return success_response(
        data=InvitationCreatedOut(
            invitation_id=inv.id,
            expires_at=inv.expires_at,
            token=token,
            accept_path="/api/v1/invitations/accept",
        ).model_dump(),
        message="Invitation created; share token securely with the invitee",
    )


@invitations_router.post("/accept")
def accept_invitation(
    body: InvitationAccept,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    token_hash = hashlib.sha256(body.token.encode("utf-8")).hexdigest()
    inv = (
        db.query(ProjectInvitation)
        .filter(
            ProjectInvitation.token_hash == token_hash,
            ProjectInvitation.accepted_at.is_(None),
        )
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invalid or already used invitation")
    if inv.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation expired")
    email = (user.get("email") or "").strip().lower()
    if email and inv.email.lower() != email:
        raise HTTPException(
            status_code=403,
            detail="Signed-in account email does not match invitation",
        )
    sub = user.get("sub")
    if not sub:
        raise HTTPException(status_code=400, detail="Missing user sub")
    exists = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == inv.project_id,
            ProjectMember.user_sub == sub,
        )
        .first()
    )
    if not exists:
        db.add(
            ProjectMember(
                project_id=inv.project_id,
                user_sub=sub,
                role=inv.role,
            )
        )
    inv.accepted_at = datetime.utcnow()
    db.commit()
    return success_response(
        data={"project_id": inv.project_id, "role": inv.role},
        message="Joined project",
    )
