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
                gateway=asset_data.gateway,
                vlan=asset_data.vlan,
                os_name=asset_data.os_name,
                os_version=asset_data.os_version,
                app_version=asset_data.app_version,
                db_version=asset_data.db_version,
                vcpu=asset_data.vcpu,
                memory=asset_data.memory,
                hostname=asset_data.hostname,
                vm_display_name=asset_data.vm_display_name,
                environment=asset_data.environment,
                location=asset_data.location,
                availability=asset_data.availability,
                itm_id=asset_data.itm_id,
                tool_update=asset_data.tool_update,
                dmz_mz=asset_data.dmz_mz,
                confidentiality=asset_data.confidentiality,
                integrity=asset_data.integrity,
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
            query = query.filter(AssetRegistry.os_name.ilike(f"%{filters.os}%"))
            
        if filters.environment:
            query = query.filter(AssetRegistry.environment == filters.environment)
            
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
            
            for row_idx, (index, row) in enumerate(df.iterrows()):
                try:
                    # Map CSV columns to asset fields (customize based on your CSV structure)
                    asset_data = AssetRegistryService._map_csv_row_to_asset(row)
                    
                    if not asset_data.get('ip_address'):
                        error_count += 1
                        errors.append(f"Row {row_idx + 2}: Missing IP address")  # +2 for header and 1-based indexing
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
                    errors.append(f"Row {row_idx + 2}: {error_msg}")  # +2 because pandas index starts at 0 and we have headers
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
        """Simple direct mapping between CSV columns and asset fields - no calculations"""
        
        # Helper function to safely get string values with length limits
        def safe_string_val(val, max_length=None):
            if pd.notna(val) and str(val).upper() not in ['NA', 'N/A', 'NULL', '']:
                result = str(val).strip()
                if max_length and len(result) > max_length:
                    result = result[:max_length]
                return result
            return None
        
        # Helper function to safely get integer values
        def safe_int_val(val):
            if pd.notna(val) and str(val).upper() not in ['NA', 'N/A', 'NULL', '']:
                try:
                    return int(float(str(val)))
                except (ValueError, TypeError):
                    return None
            return None
        
        # Create case-insensitive column lookup
        if hasattr(row, 'index') and isinstance(row.index, pd.Index):
            columns_lower = {col.lower().strip(): col for col in row.index}
            
            # Helper function to find column by multiple possible names
            def find_column(*possible_names):
                for name in possible_names:
                    if name.lower() in columns_lower:
                        return columns_lower[name.lower()]
                return None
            
            # Direct 1:1 CSV to API mapping (only CSV-available fields)
            mappings = {
                # Core Network Fields
                'ip_address': find_column('ip address', 'ip_address', 'ipaddress', 'ip'),
                'segment': find_column('segment'),
                'subnet': find_column('subnet'),
                'gateway': find_column('gateway'),
                'vlan': find_column('vlan'),
                
                # System Information
                'os_name': find_column('os', 'os name', 'operating system'),
                'os_version': find_column('os version', 'version'),
                'app_version': find_column('app version', 'application version'),
                'db_version': find_column('db version', 'database version'),
                
                # Hardware Resources
                'memory': find_column('memory', 'ram'),
                
                # Asset Identity
                'hostname': find_column('hostname'),
                'vm_display_name': find_column('vm display name - vmware', 'vm display name', 'display name'),
                
                # Organizational
                'environment': find_column('env', 'environment'),
                'location': find_column('location'),
                
                # Operational
                'availability': find_column('availability'),
                
                # Compliance & Security (separate columns)
                'tool_update': find_column('tool_update', 'tool update', 'patch level'),
                'dmz_mz': find_column('dmz/mz', 'dmz', 'mz'),
                'confidentiality': find_column('confidentially', 'confidentiality'),
                'integrity': find_column('integrity'),
                'itm_id': find_column('itam id', 'itm id', 'monitoring id'),
            }
            
            # Apply mappings with length limits
            asset_data = {}
            for field, column in mappings.items():
                if column:
                    # Apply specific length limits for certain fields
                    if field in ['vlan', 'dmz_mz', 'confidentiality', 'integrity']:
                        asset_data[field] = safe_string_val(row.get(column), max_length=50)
                    elif field in ['environment']:
                        asset_data[field] = safe_string_val(row.get(column), max_length=50)
                    elif field in ['segment', 'os_name', 'os_version', 'app_version', 'db_version']:
                        asset_data[field] = safe_string_val(row.get(column), max_length=100)
                    elif field in ['hostname', 'vm_display_name']:
                        asset_data[field] = safe_string_val(row.get(column), max_length=255)
                    elif field in ['subnet', 'itm_id', 'availability', 'location']:
                        asset_data[field] = safe_string_val(row.get(column), max_length=100)
                    elif field in ['tool_update']:
                        asset_data[field] = safe_string_val(row.get(column), max_length=200)
                    else:
                        asset_data[field] = safe_string_val(row.get(column))
                else:
                    asset_data[field] = None
            
            # Special handling for vcpu (integer field)
            vcpu_col = find_column('vcpu', 'cpu count')
            asset_data['vcpu'] = safe_int_val(row.get(vcpu_col)) if vcpu_col else None
            
            # Handle any additional compliance tags (optional)
            compliance_tags = []
            compliance_col = find_column('compliance', 'tags', 'compliance tags')
            if compliance_col:
                compliance_val = safe_string_val(row.get(compliance_col))
                if compliance_val:
                    # Split by common delimiters
                    compliance_tags = [tag.strip() for tag in compliance_val.replace(';', ',').split(',') if tag.strip()]
            
            asset_data['compliance_tags'] = compliance_tags if compliance_tags else None
            
            # Extended properties for any unmapped columns
            asset_data['extended_properties'] = {}
            mapped_columns = set()
            for col in mappings.values():
                if col:
                    mapped_columns.add(col.lower())
            mapped_columns.update(['vcpu', 'compliance', 'tags'])
            
            for col in row.index:
                if col.lower().strip() not in mapped_columns:
                    val = safe_string_val(row.get(col))
                    if val:
                        asset_data['extended_properties'][col] = val
            
            if not asset_data['extended_properties']:
                asset_data['extended_properties'] = None
                
        else:
            # Fallback: create empty structure if no headers
            asset_data = {
                'ip_address': None, 'segment': None, 'subnet': None, 'gateway': None,
                'vlan': None, 'os_name': None, 'os_version': None, 'app_version': None,
                'db_version': None, 'vcpu': None, 'memory': None, 'hostname': None,
                'vm_display_name': None, 'environment': None, 'location': None,
                'availability': None, 'itm_id': None, 'tool_update': None,
                'dmz_mz': None, 'confidentiality': None, 'integrity': None,
                'compliance_tags': None, 'extended_properties': None
            }
        
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
            AssetRegistry.os_name,
            func.count(AssetRegistry.id)
        ).filter(
            AssetRegistry.is_active == True,
            AssetRegistry.os_name.isnot(None)
        ).group_by(AssetRegistry.os_name).all()
        
        operating_systems = {os: count for os, count in os_stats}
        
        # Remove criticality, security zones, and business units (not in CSV)
        criticality_levels = {}
        security_zones = {}
        business_units = {}
        
        # Resource statistics (simplified)
        resource_stats = db.query(
            func.avg(AssetRegistry.vcpu).label('avg_vcpu'),
            func.sum(AssetRegistry.vcpu).label('total_vcpu')
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
            average_memory_gb=None,  # Memory is string field, not numeric
            total_vcpu=int(resource_stats.total_vcpu) if resource_stats.total_vcpu else None,
            total_memory_gb=None,  # Memory is string field, not numeric
            last_updated=last_updated
        )

    @staticmethod
    def _create_history_record(db: Session, asset: AssetRegistry, change_type: str, 
                              description: str, changed_by: str, changed_fields: Optional[List[str]] = None,
                              previous_values: Optional[Dict[str, Any]] = None, batch_id: Optional[str] = None):
        """Create a history record for asset changes"""
        
        # Create complete snapshot of current asset data
        asset_snapshot = {
            'ip_address': str(asset.ip_address),
            'segment': asset.segment,
            'subnet': asset.subnet,
            'gateway': str(asset.gateway) if asset.gateway else None,
            'vlan': asset.vlan,
            'os_name': asset.os_name,
            'os_version': asset.os_version,
            'app_version': asset.app_version,
            'db_version': asset.db_version,
            'vcpu': asset.vcpu,
            'memory': asset.memory,
            'hostname': asset.hostname,
            'vm_display_name': asset.vm_display_name,
            'environment': asset.environment,
            'location': asset.location,
            'availability': asset.availability,
            'itm_id': asset.itm_id,
            'tool_update': asset.tool_update,
            'dmz_mz': asset.dmz_mz,
            'confidentiality': asset.confidentiality,
            'integrity': asset.integrity,
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
