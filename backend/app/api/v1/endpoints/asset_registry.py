"""
Asset Registry API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import io

from app.core.database import get_db
from app.models.asset_registry import AssetRegistry, AssetRegistryHistory, AssetUploadBatch
from app.schemas.asset_registry import (
    AssetRegistryCreate, AssetRegistryUpdate, AssetRegistryResponse,
    AssetRegistryHistoryResponse, AssetUploadBatchResponse, CSVUploadResponse,
    AssetSearchFilters, AssetAnalyticsResponse
)
from app.services.asset_registry_service import AssetRegistryService
from app.utils.error_handlers import success_response, paginated_response

router = APIRouter()


@router.post("/assets", 
             status_code=status.HTTP_201_CREATED,
             summary="Create Asset",
             description="Create a new asset in the registry")
async def create_asset(
    asset: AssetRegistryCreate,
    created_by: str = Query(default="system", description="User creating the asset"),
    db: Session = Depends(get_db)
):
    """Create a new asset in the registry"""
    try:
        new_asset = AssetRegistryService.create_asset(db, asset, created_by)
        asset_data = AssetRegistryResponse.from_orm(new_asset).dict()
        
        return success_response(
            data=asset_data,
            message=f"Successfully created asset for IP {new_asset.ip_address}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create asset: {str(e)}")


@router.get("/assets/{ip_address}",
            summary="Get Asset by IP",
            description="Retrieve asset details by IP address")
async def get_asset_by_ip(
    ip_address: str,
    db: Session = Depends(get_db)
):
    """Get asset by IP address"""
    asset = db.query(AssetRegistry).filter(
        AssetRegistry.ip_address == ip_address,
        AssetRegistry.is_active == True
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset with IP {ip_address} not found")
    
    asset_data = AssetRegistryResponse.from_orm(asset).dict()
    return success_response(
        data=asset_data,
        message=f"Successfully retrieved asset for IP {ip_address}"
    )


@router.put("/assets/{ip_address}",
            summary="Update Asset",
            description="Update an existing asset by IP address")
async def update_asset(
    ip_address: str,
    asset_update: AssetRegistryUpdate,
    updated_by: str = Query(default="system", description="User updating the asset"),
    db: Session = Depends(get_db)
):
    """Update an existing asset"""
    try:
        updated_asset = AssetRegistryService.update_asset(db, ip_address, asset_update, updated_by)
        asset_data = AssetRegistryResponse.from_orm(updated_asset).dict()
        
        return success_response(
            data=asset_data,
            message=f"Successfully updated asset for IP {ip_address}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update asset: {str(e)}")


@router.delete("/assets/{ip_address}",
               summary="Deactivate Asset",
               description="Soft delete (deactivate) an asset by IP address")
async def deactivate_asset(
    ip_address: str,
    deactivated_by: str = Query(default="system", description="User deactivating the asset"),
    db: Session = Depends(get_db)
):
    """Soft delete (deactivate) an asset"""
    try:
        deactivated_asset = AssetRegistryService.deactivate_asset(db, ip_address, deactivated_by)
        asset_data = AssetRegistryResponse.from_orm(deactivated_asset).dict()
        
        return success_response(
            data=asset_data,
            message=f"Successfully deactivated asset for IP {ip_address}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate asset: {str(e)}")


@router.get("/assets",
            summary="Search Assets",
            description="Search and filter assets with pagination")
async def search_assets(
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
            ip_address=ip_address,
            ip_range=ip_range,
            segment=segment,
            vlan=vlan,
            os=os_name,
            environment=environment,
            hostname=hostname,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        
        assets, total_count = AssetRegistryService.search_assets(db, filters)
        
        # Convert to response objects  
        assets_data = []
        for asset in assets:
            asset_dict = {
                "id": str(asset.id),
                "ip_address": str(asset.ip_address),
                "segment": str(asset.segment or ""),
                "vlan": str(asset.vlan or ""),
                "os_name": str(asset.os_name or ""),
                "environment": str(asset.environment or ""),
                "hostname": str(asset.hostname or ""),
                "is_active": bool(asset.is_active),
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


@router.post("/assets/upload-csv",
             summary="Upload CSV",
             description="Upload and process a CSV file to create/update assets")
async def upload_csv(
    file: UploadFile = File(..., description="CSV file containing asset data"),
    uploaded_by: str = Query(default="system", description="User uploading the file"),
    db: Session = Depends(get_db)
):
    """Upload and process CSV file for asset creation/updates"""
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process CSV
        batch = AssetRegistryService.process_csv_upload(
            db, file_content, file.filename, uploaded_by
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")


@router.get("/assets/{ip_address}/history",
            summary="Get Asset History",
            description="Get change history for a specific asset")
async def get_asset_history(
    ip_address: str,
    limit: int = Query(50, ge=1, le=500, description="Number of history records to return"),
    db: Session = Depends(get_db)
):
    """Get change history for an asset"""
    
    # First verify asset exists
    asset = db.query(AssetRegistry).filter(
        AssetRegistry.ip_address == ip_address
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset with IP {ip_address} not found")
    
    # Get history records
    history_records = db.query(AssetRegistryHistory).filter(
        AssetRegistryHistory.ip_address == ip_address
    ).order_by(AssetRegistryHistory.created_at.desc()).limit(limit).all()
    
    history_data = [AssetRegistryHistoryResponse.from_orm(record).dict() for record in history_records]
    
    return success_response(
        data={
            "ip_address": ip_address,
            "total_records": len(history_data),
            "limit": limit,
            "history": history_data
        },
        message=f"Retrieved {len(history_data)} history records for asset {ip_address}"
    )


@router.get("/upload-batches",
            summary="Get Upload Batches",
            description="Get list of CSV upload batches")
async def get_upload_batches(
    limit: int = Query(50, ge=1, le=500, description="Number of batches to return"),
    offset: int = Query(0, ge=0, description="Number of batches to skip"),
    db: Session = Depends(get_db)
):
    """Get list of upload batches"""
    
    # Get total count for pagination
    total_count = db.query(AssetUploadBatch).count()
    
    batches = db.query(AssetUploadBatch).order_by(
        AssetUploadBatch.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    batches_data = [AssetUploadBatchResponse.from_orm(batch).dict() for batch in batches]
    
    return paginated_response(
        data=batches_data,
        total=total_count,
        limit=limit,
        skip=offset,
        message=f"Retrieved {len(batches_data)} of {total_count} upload batches"
    )


@router.get("/upload-batches/{batch_id}",
            summary="Get Upload Batch Details",
            description="Get details of a specific upload batch")
async def get_upload_batch(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific upload batch"""
    
    batch = db.query(AssetUploadBatch).filter(
        AssetUploadBatch.batch_id == batch_id
    ).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail=f"Upload batch {batch_id} not found")
    
    batch_data = AssetUploadBatchResponse.from_orm(batch).dict()
    
    return success_response(
        data=batch_data,
        message=f"Successfully retrieved upload batch {batch_id}"
    )


@router.get("/analytics",
            summary="Get Asset Analytics",
            description="Get comprehensive analytics and insights about the asset registry")
async def get_analytics(
    db: Session = Depends(get_db)
):
    """Get asset registry analytics and insights"""
    try:
        analytics_result = AssetRegistryService.get_analytics(db)
        analytics_data = analytics_result.dict() if hasattr(analytics_result, 'dict') else analytics_result
        
        return success_response(
            data=analytics_data,
            message="Successfully retrieved asset registry analytics"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/health",
            summary="Health Check",
            description="Check asset registry service health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Simple query to verify database connectivity
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        
        # Get basic asset count for health metrics
        asset_count = db.query(AssetRegistry).filter(AssetRegistry.is_active == True).count()
        
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


# Additional utility endpoints

@router.get("/assets/{ip_address}/versions",
            summary="Get Asset Versions",
            description="Get all versions of a specific asset")
async def get_asset_versions(
    ip_address: str,
    db: Session = Depends(get_db)
):
    """Get all versions of an asset from history"""
    
    history_records = db.query(AssetRegistryHistory).filter(
        AssetRegistryHistory.ip_address == ip_address
    ).order_by(AssetRegistryHistory.version.desc()).all()
    
    if not history_records:
        version_data = {
            "ip_address": ip_address,
            "total_versions": 0,
            "versions": []
        }
        
        return success_response(
            data=version_data,
            message=f"No version history found for asset {ip_address}"
        )
    
    versions = []
    for record in history_records:
        versions.append({
            "version": record.version,
            "change_type": record.change_type,
            "change_description": record.change_description,
            "changed_by": record.created_by,
            "changed_at": record.created_at,
            "asset_data": record.asset_data_snapshot
        })
    
    version_data = {
        "ip_address": ip_address,
        "total_versions": len(versions),
        "versions": versions
    }
    
    return success_response(
        data=version_data,
        message=f"Retrieved {len(versions)} versions for asset {ip_address}"
    )
