"""
API v1 router
"""
from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.core.project_auth import require_project_viewer

from .endpoints import projects
from .endpoints import requests, rules, analysis
from .endpoints import facts, asset_registry
from .endpoints import ip_rules, hybrid_facts, test_system, auth
from .endpoints import asset_registry_global

# All endpoints under /api/v1 require authentication
router = APIRouter(dependencies=[Depends(get_current_user)])

# Project management and invitations (no project_id path prefix)
router.include_router(projects.router)
router.include_router(projects.invitations_router)
router.include_router(asset_registry_global.router)

# FAR, rules, assets, IP lookup scoped to a project
project_scoped = APIRouter(
    prefix="/projects/{project_id}",
    dependencies=[Depends(require_project_viewer)],
)
project_scoped.include_router(requests.router, prefix="/far")
project_scoped.include_router(facts.router, prefix="/far")
project_scoped.include_router(hybrid_facts.router, prefix="/far")
project_scoped.include_router(analysis.router, prefix="/far")
project_scoped.include_router(rules.router, prefix="/rules")
project_scoped.include_router(ip_rules.router)
project_scoped.include_router(asset_registry.router, prefix="/assets")

router.include_router(project_scoped)

router.include_router(test_system.router, tags=["System Test"])
router.include_router(auth.router, tags=["Authentication"])
