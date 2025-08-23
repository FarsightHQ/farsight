"""
Asset Registry Service - Business logic for asset management operations
"""
import csv
import hashlib
import uuid
import ipaddress
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import IntegrityError
import pandas as pd
import io

from app.models.asset_registry import AssetRegistry, AssetRegistryHistory, AssetUploadBatch
from app.schemas.asset_registry import (
    AssetRegistryCreate, AssetRegistryUpdate, AssetSearchFilters,
    AssetAnalyticsResponse
)


class AssetRegistryService:
    """Service class for asset registry operations"""
    
    @staticmethod
    def create_asset(db: Session, asset_data: AssetRegistryCreate, created_by: str = 'system') -> AssetRegistry:
        """Create a new asset in the registry"""
        try:
            # Check if IP already exists
            existing_asset = db.query(AssetRegistry).filter(
                AssetRegistry.ip_address == str(asset_data.ip_address)
            ).first()
            
            if existing_asset:
                if existing_asset.is_active:
                    raise ValueError(f"Asset with IP {asset_data.ip_address} already exists")
                else:
                    # Reactivate existing asset
                    return AssetRegistryService.update_asset(
                        db, str(asset_data.ip_address), 
                        AssetRegistryUpdate(is_active=True, **asset_data.dict(exclude={'ip_address'})),
                        updated_by=created_by
                    )
            
            # Create new asset
            asset = AssetRegistry(
                ip_address=str(asset_data.ip_address),
                segment=asset_data.segment,
                subnet=asset_data.subnet,
                gateway=str(asset_data.gateway) if asset_data.gateway else None,
                vlan=asset_data.vlan,
                os=asset_data.os,
                os_version=asset_data.os_version,
                app_version=asset_data.app_version,
                db_version=asset_data.db_version,
                vcpu=asset_data.vcpu,
                memory_gb=asset_data.memory_gb,
                hostname=asset_data.hostname,
                environment=asset_data.environment,
                business_unit=asset_data.business_unit,
                asset_owner=asset_data.asset_owner,
                asset_criticality=asset_data.asset_criticality,
                patch_level=asset_data.patch_level,
                security_zone=asset_data.security_zone,
                compliance_tags=asset_data.compliance_tags,
                extended_properties=asset_data.extended_properties,
                created_by=created_by,
                updated_by=created_by
            )
            
            db.add(asset)
            db.commit()
            db.refresh(asset)
            
            # Create history record
            AssetRegistryService._create_history_record(
                db, asset, 'create', 'Asset created', created_by
            )
            
            return asset
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")

    @staticmethod
    def update_asset(db: Session, ip_address: str, update_data: AssetRegistryUpdate, 
                    updated_by: str = 'system') -> AssetRegistry:
        """Update an existing asset"""
        asset = db.query(AssetRegistry).filter(
            AssetRegistry.ip_address == ip_address
        ).first()
        
        if not asset:
            raise ValueError(f"Asset with IP {ip_address} not found")
        
        # Track changes for history
        changed_fields = []
        previous_values = {}
        
        # Update fields that have changed
        update_dict = update_data.dict(exclude_unset=True, exclude={'updated_by'})
        for field, new_value in update_dict.items():
            if hasattr(asset, field):
                old_value = getattr(asset, field)
                if old_value != new_value:
                    changed_fields.append(field)
                    previous_values[field] = old_value
                    setattr(asset, field, new_value)
        
        if changed_fields:
            asset.version += 1
            asset.updated_by = updated_by
            asset.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(asset)
            
            # Create history record
            AssetRegistryService._create_history_record(
                db, asset, 'update', f"Updated fields: {', '.join(changed_fields)}", 
                updated_by, changed_fields, previous_values
            )
        
        return asset

    @staticmethod
    def deactivate_asset(db: Session, ip_address: str, deactivated_by: str = 'system') -> AssetRegistry:
        """Soft delete an asset (mark as inactive)"""
        asset = db.query(AssetRegistry).filter(
            AssetRegistry.ip_address == ip_address,
            AssetRegistry.is_active == True
        ).first()
        
        if not asset:
            raise ValueError(f"Active asset with IP {ip_address} not found")
        
        asset.is_active = False
        asset.updated_by = deactivated_by
        asset.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(asset)
        
        # Create history record
        AssetRegistryService._create_history_record(
            db, asset, 'delete', 'Asset deactivated', deactivated_by
        )
        
        return asset

    @staticmethod
    def search_assets(db: Session, filters: AssetSearchFilters) -> Tuple[List[AssetRegistry], int]:
        """Search assets with filters and pagination"""
        query = db.query(AssetRegistry)
        
        # Apply filters
        if filters.ip_address:
            if '/' in filters.ip_address:
                # CIDR range search
                query = query.filter(text(f"ip_address << '{filters.ip_address}'"))
            else:
                # Exact or partial IP match
                query = query.filter(AssetRegistry.ip_address.like(f"%{filters.ip_address}%"))
        
        if filters.ip_range:
            query = query.filter(text(f"ip_address << '{filters.ip_range}'"))
            
        if filters.segment:
            query = query.filter(AssetRegistry.segment.ilike(f"%{filters.segment}%"))
            
        if filters.vlan:
            query = query.filter(AssetRegistry.vlan == filters.vlan)
            
        if filters.os:
            query = query.filter(AssetRegistry.os.ilike(f"%{filters.os}%"))
            
        if filters.environment:
            query = query.filter(AssetRegistry.environment == filters.environment)
            
        if filters.business_unit:
            query = query.filter(AssetRegistry.business_unit.ilike(f"%{filters.business_unit}%"))
            
        if filters.asset_criticality:
            query = query.filter(AssetRegistry.asset_criticality == filters.asset_criticality)
            
        if filters.security_zone:
            query = query.filter(AssetRegistry.security_zone.ilike(f"%{filters.security_zone}%"))
            
        if filters.hostname:
            query = query.filter(AssetRegistry.hostname.ilike(f"%{filters.hostname}%"))
            
        if filters.is_active is not None:
            query = query.filter(AssetRegistry.is_active == filters.is_active)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        assets = query.offset(filters.offset).limit(filters.limit).all()
        
        return assets, total_count

    @staticmethod
    def process_csv_upload(db: Session, file_content: bytes, filename: str, 
                          uploaded_by: str = 'system') -> AssetUploadBatch:
        """Process CSV file upload and create/update assets"""
        start_time = datetime.utcnow()
        batch_id = str(uuid.uuid4())
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Create upload batch record
        batch = AssetUploadBatch(
            batch_id=batch_id,
            upload_filename=filename,
            upload_sha256=file_hash,
            upload_size_bytes=len(file_content),
            total_rows=0,
            processed_rows=0,
            created_by=uploaded_by
        )
        
        try:
            # Parse CSV
            csv_text = file_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_text))
            
            batch.total_rows = len(df)
            db.add(batch)
            db.commit()
            
            # Process each row
            created_count = 0
            updated_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Map CSV columns to asset fields (customize based on your CSV structure)
                    asset_data = AssetRegistryService._map_csv_row_to_asset(row)
                    
                    if not asset_data.get('ip_address'):
                        error_count += 1
                        errors.append(f"Row {len(errors) + 2}: Missing IP address")  # +2 for header and 1-based indexing
                        continue
                    
                    # Check if asset exists
                    existing_asset = db.query(AssetRegistry).filter(
                        AssetRegistry.ip_address == str(asset_data['ip_address'])
                    ).first()
                    
                    if existing_asset:
                        # Update existing asset
                        update_data_dict = {k: v for k, v in asset_data.items() if k != 'ip_address'}
                        
                        # Convert gateway to string if it exists
                        if 'gateway' in update_data_dict and update_data_dict['gateway']:
                            update_data_dict['gateway'] = str(update_data_dict['gateway'])
                        
                        update_data = AssetRegistryUpdate(**update_data_dict)
                        AssetRegistryService.update_asset(
                            db, str(asset_data['ip_address']), update_data, uploaded_by
                        )
                        updated_count += 1
                    else:
                        # Create new asset
                        create_data = AssetRegistryCreate(**asset_data)
                        AssetRegistryService.create_asset(db, create_data, uploaded_by)
                        created_count += 1
                        
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    # Truncate long error messages to prevent database issues
                    if len(error_msg) > 200:
                        error_msg = error_msg[:200] + "..."
                    errors.append(f"Row {index + 2}: {error_msg}")  # +2 because pandas index starts at 0 and we have headers
                    continue
            
            # Update batch with results
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            batch.processed_rows = len(df) - error_count
            batch.created_assets = created_count
            batch.updated_assets = updated_count
            batch.error_rows = error_count
            batch.status = 'completed' if error_count == 0 else 'completed_with_errors'
            batch.error_details = {'errors': errors} if errors else None
            batch.processing_duration_ms = int(processing_time)
            batch.completed_at = datetime.utcnow()
            
            db.commit()
            db.refresh(batch)
            
            return batch
            
        except Exception as e:
            batch.status = 'failed'
            batch.error_details = {'error': str(e)}
            batch.completed_at = datetime.utcnow()
            db.commit()
            raise

    @staticmethod
    def _map_csv_row_to_asset(row: pd.Series) -> Dict[str, Any]:
        """Map CSV row to asset data structure"""
        asset_data = {}
        
        try:
            # Try to use column names first (if headers are present)
            if hasattr(row, 'index') and isinstance(row.index, pd.Index):
                # Create case-insensitive column lookup
                columns_lower = {col.lower(): col for col in row.index}
                
                # Check if we have header-based access
                ip_col = columns_lower.get('ip address') or columns_lower.get('ip_address')
                if ip_col:
                    asset_data['ip_address'] = str(row.get(ip_col)) if pd.notna(row.get(ip_col)) else None
                    
                    # Helper function to safely get string values
                    def safe_string_val(val):
                        if pd.notna(val) and str(val).upper() not in ['NA', 'N/A', '']:
                            return str(val)
                        return None
                    
                    asset_data['segment'] = safe_string_val(row.get(columns_lower.get('segment', 'Segment')))
                    asset_data['subnet'] = safe_string_val(row.get(columns_lower.get('subnet', 'Subnet')))
                    
                    # Ensure gateway is always a string, not an IP object
                    gateway_val = row.get(columns_lower.get('gateway', 'Gateway'))
                    asset_data['gateway'] = safe_string_val(gateway_val)
                    
                    asset_data['vlan'] = safe_string_val(row.get(columns_lower.get('vlan', 'VLAN')))
                    asset_data['os'] = safe_string_val(row.get(columns_lower.get('os', 'OS')))
                    asset_data['os_version'] = safe_string_val(row.get(columns_lower.get('os version', 'OS Version')))
                    asset_data['app_version'] = safe_string_val(row.get(columns_lower.get('app version', 'App Version')))
                    asset_data['db_version'] = safe_string_val(row.get(columns_lower.get('db version', 'DB Version')))
                    
                    # Handle numeric fields safely
                    try:
                        vcpu_val = row.get(columns_lower.get('vcpu', 'vCPU'))
                        if pd.notna(vcpu_val) and str(vcpu_val).upper() not in ['NA', 'N/A', '']:
                            asset_data['vcpu'] = int(float(vcpu_val))
                        else:
                            asset_data['vcpu'] = None
                    except (ValueError, TypeError):
                        asset_data['vcpu'] = None
                        
                    try:
                        memory_val = row.get(columns_lower.get('memory gb', 'Memory GB')) or row.get(columns_lower.get('memory', 'Memory'))
                        if pd.notna(memory_val) and str(memory_val).upper() not in ['NA', 'N/A', '']:
                            # Handle both "Memory GB" and "Memory" columns
                            memory_str = str(memory_val)
                            # Extract numeric value from memory string
                            import re
                            memory_match = re.search(r'(\d+(?:\.\d+)?)', memory_str)
                            asset_data['memory_gb'] = float(memory_match.group(1)) if memory_match else None
                        else:
                            asset_data['memory_gb'] = None
                    except (ValueError, TypeError):
                        asset_data['memory_gb'] = None
                    
                    # Extract hostname, environment, business unit, asset owner, criticality, patch level, security zone
                    asset_data['hostname'] = safe_string_val(row.get(columns_lower.get('hostname', 'Hostname')))
                    
                    env_val = row.get(columns_lower.get('environment', 'Environment')) or row.get(columns_lower.get('env', 'Env'))
                    if pd.notna(env_val) and str(env_val).upper() not in ['NA', 'N/A', '']:
                        env_mapping = {
                            'PREPROD-1': 'stage',
                            'PREPROD': 'stage', 
                            'PROD': 'prod',
                            'DEV': 'dev',
                            'TEST': 'test',
                            'DR': 'dr'
                        }
                        mapped_env = env_mapping.get(str(env_val).upper(), str(env_val).lower())
                        if mapped_env in ['dev', 'test', 'stage', 'prod', 'dr']:
                            asset_data['environment'] = mapped_env
                    
                    asset_data['business_unit'] = safe_string_val(row.get(columns_lower.get('business unit', 'Business Unit')))
                    asset_data['asset_owner'] = safe_string_val(row.get(columns_lower.get('asset owner', 'Asset Owner')))
                    
                    criticality_val = row.get(columns_lower.get('asset criticality', 'Asset Criticality'))
                    if pd.notna(criticality_val) and str(criticality_val).upper() not in ['NA', 'N/A', ''] and str(criticality_val).lower() in ['low', 'medium', 'high', 'critical']:
                        asset_data['asset_criticality'] = str(criticality_val).lower()
                    
                    asset_data['patch_level'] = safe_string_val(row.get(columns_lower.get('patch level', 'Patch Level')))
                    asset_data['security_zone'] = safe_string_val(row.get(columns_lower.get('security zone', 'Security Zone')))
                
                else:
                    # Fall back to positional access if no recognizable headers
                    asset_data['ip_address'] = row.iloc[1] if len(row) > 1 and pd.notna(row.iloc[1]) else None
                    asset_data['segment'] = row.iloc[0] if len(row) > 0 and pd.notna(row.iloc[0]) else None
                    asset_data['subnet'] = row.iloc[2] if len(row) > 2 and pd.notna(row.iloc[2]) else None
                    asset_data['gateway'] = row.iloc[3] if len(row) > 3 and pd.notna(row.iloc[3]) else None
                    asset_data['vlan'] = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else None
                    asset_data['os'] = row.iloc[5] if len(row) > 5 and pd.notna(row.iloc[5]) else None
                    asset_data['os_version'] = row.iloc[6] if len(row) > 6 and pd.notna(row.iloc[6]) else None
                    asset_data['app_version'] = row.iloc[7] if len(row) > 7 and pd.notna(row.iloc[7]) else None
                    asset_data['db_version'] = row.iloc[8] if len(row) > 8 and pd.notna(row.iloc[8]) else None
                    
                    # Handle numeric fields safely
                    try:
                        asset_data['vcpu'] = int(float(row.iloc[9])) if len(row) > 9 and pd.notna(row.iloc[9]) else None
                    except (ValueError, TypeError):
                        asset_data['vcpu'] = None
                        
                    try:
                        memory_str = str(row.iloc[10]) if len(row) > 10 and pd.notna(row.iloc[10]) else None
                        if memory_str:
                            import re
                            memory_match = re.search(r'(\d+(?:\.\d+)?)', memory_str)
                            asset_data['memory_gb'] = float(memory_match.group(1)) if memory_match else None
                        else:
                            asset_data['memory_gb'] = None
                    except (ValueError, TypeError):
                        asset_data['memory_gb'] = None
                    
                    # Map additional columns as extended properties for positional access
                    extended_props = {}
                    if len(row) > 11:
                        column_names = [
                            'tool_update', 'display_name', 'hostname', 'env', 'dmz_mz',
                            'confidentiality', 'integrity', 'availability', 'itam_id', 'location'
                        ]
                        
                        for i, col_name in enumerate(column_names, start=11):
                            if i < len(row) and pd.notna(row.iloc[i]):
                                extended_props[col_name] = row.iloc[i]
                    
                    if extended_props:
                        asset_data['extended_properties'] = extended_props
                        
                    # Extract hostname if available in extended properties
                    if 'hostname' in extended_props:
                        asset_data['hostname'] = extended_props['hostname']
                
        except Exception as e:
            raise ValueError(f"Error mapping CSV row: {str(e)}")
        
        return asset_data

    @staticmethod
    def get_analytics(db: Session) -> AssetAnalyticsResponse:
        """Get analytics and insights about the asset registry"""
        
        # Basic counts
        total_assets = db.query(AssetRegistry).count()
        active_assets = db.query(AssetRegistry).filter(AssetRegistry.is_active == True).count()
        inactive_assets = total_assets - active_assets
        
        # Environment distribution
        env_stats = db.query(
            AssetRegistry.environment, 
            func.count(AssetRegistry.id)
        ).filter(
            AssetRegistry.is_active == True,
            AssetRegistry.environment.isnot(None)
        ).group_by(AssetRegistry.environment).all()
        
        environments = {env: count for env, count in env_stats}
        
        # OS distribution
        os_stats = db.query(
            AssetRegistry.os,
            func.count(AssetRegistry.id)
        ).filter(
            AssetRegistry.is_active == True,
            AssetRegistry.os.isnot(None)
        ).group_by(AssetRegistry.os).all()
        
        operating_systems = {os: count for os, count in os_stats}
        
        # Criticality distribution
        crit_stats = db.query(
            AssetRegistry.asset_criticality,
            func.count(AssetRegistry.id)
        ).filter(
            AssetRegistry.is_active == True,
            AssetRegistry.asset_criticality.isnot(None)
        ).group_by(AssetRegistry.asset_criticality).all()
        
        criticality_levels = {crit: count for crit, count in crit_stats}
        
        # Security zones
        zone_stats = db.query(
            AssetRegistry.security_zone,
            func.count(AssetRegistry.id)
        ).filter(
            AssetRegistry.is_active == True,
            AssetRegistry.security_zone.isnot(None)
        ).group_by(AssetRegistry.security_zone).all()
        
        security_zones = {zone: count for zone, count in zone_stats}
        
        # Business units
        bu_stats = db.query(
            AssetRegistry.business_unit,
            func.count(AssetRegistry.id)
        ).filter(
            AssetRegistry.is_active == True,
            AssetRegistry.business_unit.isnot(None)
        ).group_by(AssetRegistry.business_unit).all()
        
        business_units = {bu: count for bu, count in bu_stats}
        
        # Resource statistics
        resource_stats = db.query(
            func.avg(AssetRegistry.vcpu).label('avg_vcpu'),
            func.avg(AssetRegistry.memory_gb).label('avg_memory'),
            func.sum(AssetRegistry.vcpu).label('total_vcpu'),
            func.sum(AssetRegistry.memory_gb).label('total_memory')
        ).filter(AssetRegistry.is_active == True).first()
        
        # Last updated
        last_updated = db.query(
            func.max(AssetRegistry.updated_at)
        ).scalar() or datetime.utcnow()
        
        return AssetAnalyticsResponse(
            total_assets=total_assets,
            active_assets=active_assets,
            inactive_assets=inactive_assets,
            environments=environments,
            operating_systems=operating_systems,
            criticality_levels=criticality_levels,
            security_zones=security_zones,
            business_units=business_units,
            average_vcpu=float(resource_stats.avg_vcpu) if resource_stats.avg_vcpu else None,
            average_memory_gb=float(resource_stats.avg_memory) if resource_stats.avg_memory else None,
            total_vcpu=int(resource_stats.total_vcpu) if resource_stats.total_vcpu else None,
            total_memory_gb=float(resource_stats.total_memory) if resource_stats.total_memory else None,
            last_updated=last_updated
        )

    @staticmethod
    def _create_history_record(db: Session, asset: AssetRegistry, change_type: str, 
                              description: str, changed_by: str, changed_fields: List[str] = None,
                              previous_values: Dict[str, Any] = None, batch_id: str = None):
        """Create a history record for asset changes"""
        
        # Create complete snapshot of current asset data
        asset_snapshot = {
            'ip_address': str(asset.ip_address),
            'segment': asset.segment,
            'subnet': asset.subnet,
            'gateway': str(asset.gateway) if asset.gateway else None,
            'vlan': asset.vlan,
            'os': asset.os,
            'os_version': asset.os_version,
            'app_version': asset.app_version,
            'db_version': asset.db_version,
            'vcpu': asset.vcpu,
            'memory_gb': asset.memory_gb,
            'hostname': asset.hostname,
            'environment': asset.environment,
            'business_unit': asset.business_unit,
            'asset_owner': asset.asset_owner,
            'asset_criticality': asset.asset_criticality,
            'patch_level': asset.patch_level,
            'security_zone': asset.security_zone,
            'compliance_tags': asset.compliance_tags,
            'extended_properties': asset.extended_properties,
            'version': asset.version,
            'is_active': asset.is_active,
            'data_source': asset.data_source
        }
        
        history = AssetRegistryHistory(
            asset_id=asset.id,
            ip_address=str(asset.ip_address),
            version=asset.version,
            change_type=change_type,
            change_description=description,
            asset_data_snapshot=asset_snapshot,
            changed_fields=changed_fields,
            previous_values=previous_values,
            created_by=changed_by,
            upload_batch_id=batch_id
        )
        
        db.add(history)
        db.commit()
