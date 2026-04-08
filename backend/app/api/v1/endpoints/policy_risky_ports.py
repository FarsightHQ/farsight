"""
Global risky port policy (application-wide). Authenticated read; admin replace.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.project_auth import user_has_platform_admin_bypass
from app.models.risky_port_policy import RiskyPortPolicyEntry
from app.schemas.risky_port_policy import (
    RiskyPortPolicyEntryCreate,
    RiskyPortPolicyEntryResponse,
    RiskyPortPolicyReplaceRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy/risky-ports", tags=["Policy"])


async def require_platform_admin_for_policy(
    user: Dict[str, Any] = Depends(get_current_user),
) -> None:
    """Same elevated roles as project platform admin: realm/client admin or farsight-admin."""
    if not user_has_platform_admin_bypass(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: platform admin role required (admin or farsight-admin)",
        )


@router.get("", response_model=List[RiskyPortPolicyEntryResponse])
def get_risky_port_policy(
    db: Session = Depends(get_db),
) -> List[RiskyPortPolicyEntryResponse]:
    rows = (
        db.query(RiskyPortPolicyEntry)
        .order_by(RiskyPortPolicyEntry.sort_order.asc(), RiskyPortPolicyEntry.id.asc())
        .all()
    )
    return [RiskyPortPolicyEntryResponse.model_validate(r) for r in rows]


@router.put("", response_model=List[RiskyPortPolicyEntryResponse])
def replace_risky_port_policy(
    body: RiskyPortPolicyReplaceRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_platform_admin_for_policy),
) -> List[RiskyPortPolicyEntryResponse]:
    try:
        db.query(RiskyPortPolicyEntry).delete()
        for item in body.entries:
            row = RiskyPortPolicyEntry(
                protocol=item.protocol,
                port_start=item.port_start,
                port_end=item.port_end,
                label=item.label,
                recommendation=item.recommendation,
                severity=item.severity,
                enabled=item.enabled,
                sort_order=item.sort_order,
            )
            db.add(row)
        db.commit()
    except Exception as e:
        logger.error("Failed to replace risky port policy: %s", e, exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save risky port policy",
        ) from e

    return get_risky_port_policy(db=db)
