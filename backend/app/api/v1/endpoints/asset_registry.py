"""
Asset Registry API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from typing import List, Optional
import io
import logging

from app.core.database import get_db
from app.core.auth import get_current_user, uploader_from_user
from app.core.project_auth import require_project_role_dep
from app.models.asset_registry import AssetRegistry, AssetUploadBatch
from app.models.project import ProjectAsset
from app.schemas.asset_registry import (
    AssetRegistryCreate, AssetRegistryResponse,
    AssetUploadBatchResponse, CSVUploadResponse,
    AssetSearchFilters, AssetAnalyticsResponse, AssetFilterOptionsResponse
)
from app.services.asset_registry_service import AssetRegistryService
from app.utils.error_handlers import success_response, paginated_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create Asset",
    description="Create a new asset in the registry and link it to this project",
    dependencies=[Depends(require_project_role_dep("member"))],
)
async def create_asset(
    project_id: int,
    asset: AssetRegistryCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new asset in the registry"""
    try:
        created_by = uploader_from_user(user)
        new_asset = AssetRegistryService.create_asset(db, asset, created_by)
        link = (
            db.query(ProjectAsset)
            .filter(
                ProjectAsset.project_id == project_id,
                ProjectAsset.asset_registry_id == new_asset.id,
            )
            .first()
        )
        if not link:
            db.add(
                ProjectAsset(
                    project_id=project_id,
                    asset_registry_id=new_asset.id,
                    linked_by_sub=user.get("sub"),
                )
            )
            db.commit()
        asset_data = AssetRegistryResponse.from_orm(new_asset).dict()
        
        return success_response(
            data=asset_data,
            message=f"Successfully created asset for IP {new_asset.ip_address}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create asset: {str(e)}")


# SPECIFIC ROUTES FIRST (before parameterized routes)

@router.get(
    "",
    summary="Search Assets",
    description="Search and filter assets linked to this project",
)
async def search_assets(
    project_id: int,
    ip_address: Optional[str] = Query(None, description="IP address filter (exact or partial)"),
    ip_range: Optional[str] = Query(None, description="IP range in CIDR format"),
    segment: Optional[str] = Query(None, description="Network segment filter"),
    vlan: Optional[str] = Query(None, description="VLAN filter"),
    os_name: Optional[str] = Query(None, description="Operating system filter"),
    environment: Optional[str] = Query(None, description="Environment filter"),
    hostname: Optional[str] = Query(None, description="Hostname filter"),
    is_active: Optional[bool] = Query(True, description="Include only active assets"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Search assets with filters and pagination"""
    try:
        filters = AssetSearchFilters(
            project_id=project_id,
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
        
        # Convert to response objects  
        assets_data = []
        for asset in assets:
            # Helper function to normalize string fields
            def normalize_field(value):
                if value is None:
                    return None
                value_str = str(value).strip()
                return value_str if value_str else None
            
            asset_dict = {
                "id": str(asset.id),
                "ip_address": str(asset.ip_address),
                "segment": normalize_field(asset.segment),
                "vlan": normalize_field(asset.vlan),
                "os_name": normalize_field(asset.os_name),
                "environment": normalize_field(asset.environment),
                "hostname": normalize_field(asset.hostname),
                "is_active": bool(asset.is_active),
                "created_by": str(asset.created_by or ""),
                "created_at": str(asset.created_at),
                "updated_at": str(asset.updated_at)
            }
            assets_data.append(asset_dict)
        
        return paginated_response(
            data=assets_data,
            total=total_count,
            limit=limit,
            skip=offset,
            message=f"Retrieved {len(assets_data)} of {total_count} assets"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search assets: {str(e)}")


@router.post(
    "/upload-csv",
    summary="Upload CSV",
    description="Upload and process a CSV file to create/update assets",
    dependencies=[Depends(require_project_role_dep("member"))],
)
async def upload_csv(
    project_id: int,
    file: UploadFile = File(..., description="CSV file containing asset data"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Upload and process CSV file for asset creation/updates"""
    uploaded_by = uploader_from_user(user)

    # Enhanced file validation
    from app.utils.file_utils import validate_csv_file_enhanced
    from app.utils.csv_errors import (
        DatabaseConnectionError, FileSystemError, InsufficientStorageError
    )
    
    try:
        validate_csv_file_enhanced(file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File validation failed: {str(e)}")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process CSV
        batch = AssetRegistryService.process_csv_upload(
            db,
            file_content,
            file.filename,
            uploaded_by,
            project_id=project_id,
            linked_by_sub=user.get("sub"),
        )
        
        # Prepare response data
        upload_data = {
            "batch_id": str(batch.batch_id),
            "filename": batch.upload_filename,
            "summary": {
                "total_rows": batch.total_rows,
                "processed_rows": batch.processed_rows,
                "created_assets": batch.created_assets,
                "updated_assets": batch.updated_assets,
                "error_rows": batch.error_rows,
                "processing_time_ms": batch.processing_duration_ms
            },
            "upload_details": AssetUploadBatchResponse.from_orm(batch).dict()
        }
        
        message = f"CSV processing completed. Created: {batch.created_assets}, Updated: {batch.updated_assets}"
        if batch.error_rows > 0:
            message += f", Errors: {batch.error_rows}"
        
        return success_response(
            data=upload_data,
            message=message
        )
        
    except (HTTPException, DatabaseConnectionError, FileSystemError, InsufficientStorageError):
        # Re-raise known exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error processing CSV upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")


@router.get(
    "/upload-batches",
    summary="Get Upload Batches",
    description="Get list of CSV upload batches for this project",
)
async def get_upload_batches(
    project_id: int,
    limit: int = Query(50, ge=1, le=500, description="Number of batches to return"),
    offset: int = Query(0, ge=0, description="Number of batches to skip"),
    db: Session = Depends(get_db),
):
    """Get list of upload batches"""
    q = db.query(AssetUploadBatch).filter(AssetUploadBatch.project_id == project_id)
    total_count = q.count()

    batches = (
        q.order_by(AssetUploadBatch.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    batches_data = [AssetUploadBatchResponse.from_orm(batch).dict() for batch in batches]
    
    return paginated_response(
        data=batches_data,
        total=total_count,
        limit=limit,
        skip=offset,
        message=f"Retrieved {len(batches_data)} of {total_count} upload batches"
    )


@router.get(
    "/upload-batches/{batch_id}",
    summary="Get Upload Batch Details",
    description="Get details of a specific upload batch",
)
async def get_upload_batch(
    project_id: int,
    batch_id: str,
    db: Session = Depends(get_db),
):
    """Get details of a specific upload batch"""
    
    batch = (
        db.query(AssetUploadBatch)
        .filter(
            AssetUploadBatch.batch_id == batch_id,
            AssetUploadBatch.project_id == project_id,
        )
        .first()
    )

    if not batch:
        raise HTTPException(status_code=404, detail=f"Upload batch {batch_id} not found")
    
    batch_data = AssetUploadBatchResponse.from_orm(batch).dict()
    
    return success_response(
        data=batch_data,
        message=f"Successfully retrieved upload batch {batch_id}"
    )


@router.get(
    "/analytics",
    summary="Get Asset Analytics",
    description="Get analytics for assets linked to this project",
)
async def get_analytics(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Get asset registry analytics and insights"""
    try:
        analytics_result = AssetRegistryService.get_analytics(db, project_id=project_id)
        if hasattr(analytics_result, "model_dump"):
            analytics_data = analytics_result.model_dump(mode="json")
        else:
            analytics_data = analytics_result.dict()

        return success_response(
            data=analytics_data,
            message="Successfully retrieved asset registry analytics"
        )
    except OperationalError as e:
        logger.exception("Analytics: database unavailable (%s)", e)
        raise HTTPException(
            status_code=503,
            detail=(
                "Database unavailable. If you run the API on your machine (not inside Docker), "
                "set POSTGRES_HOST=localhost in .env (or point DATABASE_URL at a reachable PostgreSQL)."
            ),
        )
    except Exception as e:
        logger.exception("Failed to get analytics: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get(
    "/filter-options",
    summary="Get Filter Options",
    description="Get unique filter values for assets in this project",
)
async def get_filter_options(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Get unique filter values for asset filtering"""
    try:
        filter_options = AssetRegistryService.get_filter_options(db, project_id=project_id)
        options_data = filter_options.dict() if hasattr(filter_options, 'dict') else filter_options
        
        return success_response(
            data=options_data,
            message="Successfully retrieved filter options"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get filter options: {str(e)}")


@router.get(
    "/health",
    summary="Health Check",
    description="Check asset registry service health for this project",
)
async def health_check(project_id: int, db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Simple query to verify database connectivity
        from sqlalchemy import text
        db.execute(text("SELECT 1"))

        # Count active assets linked to project
        asset_count = (
            db.query(AssetRegistry)
            .join(
                ProjectAsset,
                ProjectAsset.asset_registry_id == AssetRegistry.id,
            )
            .filter(
                ProjectAsset.project_id == project_id,
                AssetRegistry.is_active == True,
            )
            .count()
        )
        
        health_data = {
            "service": "asset_registry",
            "database": "connected",
            "active_assets": asset_count,
            "timestamp": "2025-08-29T00:00:00Z"
        }
        
        return success_response(
            data=health_data,
            message="Asset registry service is healthy"
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# PARAMETERIZED ROUTES AFTER SPECIFIC ROUTES


@router.get(
    "/{ip_address:path}",
    summary="Get Asset by IP",
    description="Retrieve asset details by IP address (must be linked to this project)",
)
async def get_asset_by_ip(
    project_id: int,
    ip_address: str,
    db: Session = Depends(get_db),
):
    """Get asset by IP address"""
    asset = (
        db.query(AssetRegistry)
        .join(
            ProjectAsset,
            ProjectAsset.asset_registry_id == AssetRegistry.id,
        )
        .filter(
            ProjectAsset.project_id == project_id,
            AssetRegistry.ip_address == ip_address,
            AssetRegistry.is_active == True,
        )
        .first()
    )

    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset with IP {ip_address} not found")
    
    asset_data = AssetRegistryResponse.from_orm(asset).dict()
    return success_response(
        data=asset_data,
        message=f"Successfully retrieved asset for IP {ip_address}"
    )




