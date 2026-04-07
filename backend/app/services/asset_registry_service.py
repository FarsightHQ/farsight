"""
Asset Registry Service - Business logic for asset management operations
"""
import csv
import hashlib
import uuid
import ipaddress
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import IntegrityError, OperationalError
import pandas as pd
import io

from app.models.asset_registry import AssetRegistry, AssetUploadBatch
from app.models.project import ProjectAsset
from app.schemas.asset_registry import (
    AssetRegistryCreate, AssetRegistryUpdate, AssetSearchFilters,
    AssetAnalyticsResponse, AssetFilterOptionsResponse
)
from app.utils.csv_errors import DatabaseConnectionError

logger = logging.getLogger(__name__)


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
            
            return asset
            
        except OperationalError as e:
            db.rollback()
            logger.error(f"Database connection error creating asset: {str(e)}", exc_info=True)
            raise DatabaseConnectionError(
                message="Database connection failed during asset creation",
                details={"error": str(e), "ip_address": str(asset_data.ip_address)}
            )
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating asset: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def update_asset(db: Session, ip_address: str, update_data: AssetRegistryUpdate, 
                    updated_by: str = 'system') -> AssetRegistry:
        """Update an existing asset"""
        try:
            asset = db.query(AssetRegistry).filter(
                AssetRegistry.ip_address == ip_address
            ).first()
            
            if not asset:
                raise ValueError(f"Asset with IP {ip_address} not found")
            
            # Track changed fields
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
            
            return asset
        except ValueError:
            raise
        except OperationalError as e:
            db.rollback()
            logger.error(f"Database connection error updating asset {ip_address}: {str(e)}", exc_info=True)
            raise DatabaseConnectionError(
                message="Database connection failed during asset update",
                details={"error": str(e), "ip_address": ip_address}
            )
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating asset {ip_address}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def deactivate_asset(db: Session, ip_address: str, deactivated_by: str = 'system') -> AssetRegistry:
        """Soft delete an asset (mark as inactive)"""
        try:
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
            
            return asset
        except ValueError:
            raise
        except OperationalError as e:
            db.rollback()
            logger.error(f"Database connection error deactivating asset {ip_address}: {str(e)}", exc_info=True)
            raise DatabaseConnectionError(
                message="Database connection failed during asset deactivation",
                details={"error": str(e), "ip_address": ip_address}
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error deactivating asset {ip_address}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def search_assets(db: Session, filters: AssetSearchFilters) -> Tuple[List[AssetRegistry], int]:
        """Search assets with filters and pagination"""
        query = db.query(AssetRegistry)
        if filters.project_id is not None:
            query = (
                query.join(
                    ProjectAsset,
                    ProjectAsset.asset_registry_id == AssetRegistry.id,
                ).filter(ProjectAsset.project_id == filters.project_id)
            )

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
            # Trim the filter value and do case-insensitive match with trimmed database values
            env_filter = filters.environment.strip()
            query = query.filter(
                func.trim(func.lower(AssetRegistry.environment)) == func.lower(env_filter)
            )
            
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
    def link_ips_to_project(
        db: Session,
        project_id: int,
        ip_addresses: List[str],
        linked_by_sub: Optional[str],
    ) -> None:
        """Ensure project_assets rows exist for the given IPs (global registry rows)."""
        if not ip_addresses:
            return
        ips = {str(ip).strip() for ip in ip_addresses if ip}
        if not ips:
            return
        assets = (
            db.query(AssetRegistry)
            .filter(AssetRegistry.ip_address.in_(ips))
            .all()
        )
        for asset in assets:
            exists = (
                db.query(ProjectAsset)
                .filter(
                    ProjectAsset.project_id == project_id,
                    ProjectAsset.asset_registry_id == asset.id,
                )
                .first()
            )
            if not exists:
                db.add(
                    ProjectAsset(
                        project_id=project_id,
                        asset_registry_id=asset.id,
                        linked_by_sub=linked_by_sub,
                    )
                )
        db.commit()

    @staticmethod
    def process_csv_upload(
        db: Session,
        file_content: bytes,
        filename: str,
        uploaded_by: str = "system",
        project_id: Optional[int] = None,
        linked_by_sub: Optional[str] = None,
    ) -> AssetUploadBatch:
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
            created_by=uploaded_by,
            project_id=project_id,
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
            processed_ips: List[str] = []

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
                        # Patch only fields present in the CSV; omit missing columns so we do not
                        # overwrite existing DB values with None (IP-only uploads = link-only).
                        update_data_dict = {
                            k: v
                            for k, v in asset_data.items()
                            if k != 'ip_address' and v is not None
                        }
                        if 'gateway' in update_data_dict and update_data_dict['gateway']:
                            update_data_dict['gateway'] = str(update_data_dict['gateway'])
                        if update_data_dict:
                            update_data = AssetRegistryUpdate(**update_data_dict)
                            AssetRegistryService.update_asset(
                                db, str(asset_data['ip_address']), update_data, uploaded_by
                            )
                            updated_count += 1
                        processed_ips.append(str(asset_data["ip_address"]))
                    else:
                        # Create new asset
                        create_data = AssetRegistryCreate(**asset_data)
                        AssetRegistryService.create_asset(db, create_data, uploaded_by)
                        created_count += 1
                        processed_ips.append(str(asset_data["ip_address"]))

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

            if project_id is not None and processed_ips:
                AssetRegistryService.link_ips_to_project(
                    db, project_id, processed_ips, linked_by_sub or uploaded_by
                )

            return batch
            
        except OperationalError as e:
            db.rollback()
            batch.status = 'failed'
            batch.error_details = {'error': f"Database connection failed: {str(e)}"}
            batch.completed_at = datetime.utcnow()
            try:
                db.commit()
            except Exception:
                pass  # Ignore commit errors if rollback already happened
            logger.error(f"Database connection error processing CSV upload: {str(e)}", exc_info=True)
            raise DatabaseConnectionError(
                message="Database connection failed during CSV upload processing",
                details={"error": str(e), "filename": filename}
            )
        except Exception as e:
            db.rollback()
            batch.status = 'failed'
            batch.error_details = {'error': str(e)}
            batch.completed_at = datetime.utcnow()
            try:
                db.commit()
            except Exception:
                pass  # Ignore commit errors if rollback already happened
            logger.error(f"Error processing CSV upload: {str(e)}", exc_info=True)
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
            
            # Only include keys when the CSV has that column and the cell has a value.
            # Missing columns are omitted entirely so updates do not clear existing data.
            asset_data: Dict[str, Any] = {}
            for field, column in mappings.items():
                if not column:
                    continue
                val: Any
                if field in ['vlan', 'dmz_mz', 'confidentiality', 'integrity']:
                    val = safe_string_val(row.get(column), max_length=50)
                elif field in ['environment']:
                    val = safe_string_val(row.get(column), max_length=50)
                elif field in ['segment', 'os_name', 'os_version', 'app_version', 'db_version']:
                    val = safe_string_val(row.get(column), max_length=100)
                elif field in ['hostname', 'vm_display_name']:
                    val = safe_string_val(row.get(column), max_length=255)
                elif field in ['subnet', 'itm_id', 'availability', 'location']:
                    val = safe_string_val(row.get(column), max_length=100)
                elif field in ['tool_update']:
                    val = safe_string_val(row.get(column), max_length=200)
                elif field == 'ip_address':
                    val = safe_string_val(row.get(column), max_length=50)
                else:
                    val = safe_string_val(row.get(column))
                if val is not None:
                    asset_data[field] = val

            vcpu_col = find_column('vcpu', 'cpu count')
            if vcpu_col:
                vcpu_val = safe_int_val(row.get(vcpu_col))
                if vcpu_val is not None:
                    asset_data['vcpu'] = vcpu_val

            compliance_col = find_column('compliance', 'tags', 'compliance tags')
            if compliance_col:
                compliance_val = safe_string_val(row.get(compliance_col))
                if compliance_val:
                    compliance_tags = [
                        tag.strip()
                        for tag in compliance_val.replace(';', ',').split(',')
                        if tag.strip()
                    ]
                    if compliance_tags:
                        asset_data['compliance_tags'] = compliance_tags

            mapped_columns = set()
            for col in mappings.values():
                if col:
                    mapped_columns.add(col.lower())
            mapped_columns.update(['vcpu', 'compliance', 'tags'])

            extended_properties: Dict[str, Any] = {}
            for col in row.index:
                if col.lower().strip() not in mapped_columns:
                    val = safe_string_val(row.get(col))
                    if val:
                        extended_properties[col] = val
            if extended_properties:
                asset_data['extended_properties'] = extended_properties

        else:
            # No usable headers — cannot map columns; treat as missing IP downstream
            asset_data = {}
        
        return asset_data

    @staticmethod
    def get_analytics(db: Session, project_id: Optional[int] = None) -> AssetAnalyticsResponse:
        """Get analytics and insights about the asset registry"""
        base = db.query(AssetRegistry)
        if project_id is not None:
            base = (
                base.join(
                    ProjectAsset,
                    ProjectAsset.asset_registry_id == AssetRegistry.id,
                ).filter(ProjectAsset.project_id == project_id)
            )

        # Basic counts
        total_assets = base.count()
        active_assets = base.filter(AssetRegistry.is_active == True).count()
        inactive_assets = total_assets - active_assets
        
        # Environment distribution
        env_stats = (
            base.filter(
                AssetRegistry.is_active == True,
                AssetRegistry.environment.isnot(None),
                AssetRegistry.environment != "",
            )
            .with_entities(AssetRegistry.environment, func.count(AssetRegistry.id))
            .group_by(AssetRegistry.environment)
            .all()
        )

        environments = {env: count for env, count in env_stats if env}

        # OS distribution
        os_stats = (
            base.filter(
                AssetRegistry.is_active == True,
                AssetRegistry.os_name.isnot(None),
                AssetRegistry.os_name != "",
            )
            .with_entities(AssetRegistry.os_name, func.count(AssetRegistry.id))
            .group_by(AssetRegistry.os_name)
            .all()
        )
        
        operating_systems = {os: count for os, count in os_stats if os}
        
        # Remove criticality, security zones, and business units (not in CSV)
        criticality_levels = {}
        security_zones = {}
        business_units = {}
        
        # Resource statistics (simplified)
        resource_stats = (
            base.filter(AssetRegistry.is_active == True)
            .with_entities(
                func.avg(AssetRegistry.vcpu).label("avg_vcpu"),
                func.sum(AssetRegistry.vcpu).label("total_vcpu"),
            )
            .first()
        )

        avg_vcpu = None
        total_vcpu_val = None
        if resource_stats is not None:
            if resource_stats.avg_vcpu is not None:
                avg_vcpu = float(resource_stats.avg_vcpu)
            if resource_stats.total_vcpu is not None:
                total_vcpu_val = int(resource_stats.total_vcpu)
        
        # Last updated
        last_updated = (
            base.with_entities(func.max(AssetRegistry.updated_at)).scalar()
            or datetime.utcnow()
        )
        
        return AssetAnalyticsResponse(
            total_assets=total_assets,
            active_assets=active_assets,
            inactive_assets=inactive_assets,
            environments=environments,
            operating_systems=operating_systems,
            criticality_levels=criticality_levels,
            security_zones=security_zones,
            business_units=business_units,
            average_vcpu=avg_vcpu,
            average_memory_gb=None,  # Memory is string field, not numeric
            total_vcpu=total_vcpu_val,
            total_memory_gb=None,  # Memory is string field, not numeric
            last_updated=last_updated
        )

    @staticmethod
    def get_filter_options(db: Session, project_id: Optional[int] = None) -> AssetFilterOptionsResponse:
        """Get unique filter values for asset filtering"""
        base = db.query(AssetRegistry)
        if project_id is not None:
            base = (
                base.join(
                    ProjectAsset,
                    ProjectAsset.asset_registry_id == AssetRegistry.id,
                ).filter(ProjectAsset.project_id == project_id)
            )

        # Get unique segments (active assets only)
        segments = (
            base.filter(
                AssetRegistry.is_active == True,
                AssetRegistry.segment.isnot(None),
                AssetRegistry.segment != "",
            )
            .with_entities(AssetRegistry.segment)
            .distinct()
            .order_by(AssetRegistry.segment)
            .all()
        )
        segments_list = [s[0] for s in segments if s[0]]

        # Get unique VLANs (active assets only)
        vlans = (
            base.filter(
                AssetRegistry.is_active == True,
                AssetRegistry.vlan.isnot(None),
                AssetRegistry.vlan != "",
            )
            .with_entities(AssetRegistry.vlan)
            .distinct()
            .order_by(AssetRegistry.vlan)
            .all()
        )
        vlans_list = [v[0] for v in vlans if v[0]]

        # Get unique environments (active assets only)
        environments = (
            base.filter(
                AssetRegistry.is_active == True,
                AssetRegistry.environment.isnot(None),
                AssetRegistry.environment != "",
            )
            .with_entities(AssetRegistry.environment)
            .distinct()
            .order_by(AssetRegistry.environment)
            .all()
        )
        environments_list = [e[0] for e in environments if e[0]]

        # Get unique OS names (active assets only)
        os_names = (
            base.filter(
                AssetRegistry.is_active == True,
                AssetRegistry.os_name.isnot(None),
                AssetRegistry.os_name != "",
            )
            .with_entities(AssetRegistry.os_name)
            .distinct()
            .order_by(AssetRegistry.os_name)
            .all()
        )
        os_names_list = [o[0] for o in os_names if o[0]]
        
        return AssetFilterOptionsResponse(
            segments=segments_list,
            vlans=vlans_list,
            environments=environments_list,
            os_names=os_names_list
        )

