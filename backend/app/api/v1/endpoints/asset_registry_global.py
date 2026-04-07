"""
Global asset registry (org-wide). Authenticated read; not scoped to a single project.
Linked-projects lists are filtered to projects the current user may access.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.project_auth import visible_project_ids_for_user
from app.models.asset_registry import AssetRegistry
from app.models.project import Project, ProjectAsset
from app.schemas.asset_registry import AssetRegistryResponse, AssetSearchFilters
from app.services.asset_registry_service import AssetRegistryService
from app.utils.error_handlers import paginated_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registry", tags=["Asset Registry (Global)"])


def _normalize_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str if value_str else None


def _asset_summary_dict(asset: AssetRegistry) -> Dict[str, Any]:
    return {
        "id": str(asset.id),
        "ip_address": str(asset.ip_address),
        "segment": _normalize_field(asset.segment),
        "vlan": _normalize_field(asset.vlan),
        "os_name": _normalize_field(asset.os_name),
        "environment": _normalize_field(asset.environment),
        "hostname": _normalize_field(asset.hostname),
        "is_active": bool(asset.is_active),
        "created_by": str(asset.created_by or ""),
        "created_at": str(asset.created_at),
        "updated_at": str(asset.updated_at),
    }


@router.get("/assets")
async def search_global_assets(
    ip_address: Optional[str] = Query(None),
    ip_range: Optional[str] = Query(None),
    segment: Optional[str] = Query(None),
    vlan: Optional[str] = Query(None),
    os_name: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    hostname: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Search all assets in the global registry (no project filter)."""
    filters = AssetSearchFilters(
        project_id=None,
        ip_address=ip_address,
        ip_range=ip_range,
        segment=segment,
        vlan=vlan,
        os=os_name,
        environment=environment,
        hostname=hostname,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    assets, total_count = AssetRegistryService.search_assets(db, filters)
    assets_data = [_asset_summary_dict(a) for a in assets]
    return paginated_response(
        data=assets_data,
        total=total_count,
        limit=limit,
        skip=offset,
        message=f"Retrieved {len(assets_data)} of {total_count} global assets",
    )


@router.get("/assets/{ip_address:path}/projects")
async def list_asset_linked_projects(
    ip_address: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Projects linked to this asset that the current user may access."""
    ip = unquote(ip_address).strip()
    asset = (
        db.query(AssetRegistry)
        .filter(AssetRegistry.ip_address == ip, AssetRegistry.is_active == True)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    visible = visible_project_ids_for_user(db, user)
    if not visible:
        return success_response(data={"projects": []}, message="No linked projects visible")

    links = (
        db.query(Project.id, Project.name, Project.slug)
        .join(ProjectAsset, ProjectAsset.project_id == Project.id)
        .filter(
            ProjectAsset.asset_registry_id == asset.id,
            Project.id.in_(visible),
        )
        .order_by(Project.name)
        .all()
    )
    projects = [{"id": row[0], "name": row[1], "slug": row[2]} for row in links]
    return success_response(
        data={"projects": projects},
        message=f"{len(projects)} project(s) link this asset",
    )


@router.get("/assets/{ip_address:path}")
async def get_global_asset_by_ip(
    ip_address: str,
    db: Session = Depends(get_db),
):
    ip = unquote(ip_address).strip()
    asset = (
        db.query(AssetRegistry)
        .filter(AssetRegistry.ip_address == ip, AssetRegistry.is_active == True)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset_data = AssetRegistryResponse.from_orm(asset).dict()
    return success_response(
        data=asset_data,
        message=f"Retrieved asset for IP {ip}",
    )
