"""
Pydantic schemas for Asset Registry operations
"""
from pydantic import BaseModel, Field, IPvAnyAddress, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import ipaddress


class AssetRegistryBase(BaseModel):
    """Base schema for Asset Registry with validation"""
    
    # Core Asset Identification
    ip_address: IPvAnyAddress = Field(..., description="Primary asset identifier - must be unique")
    
    # Network Information
    segment: Optional[str] = Field(None, max_length=100, description="Network segment identifier")
    subnet: Optional[str] = Field(None, max_length=50, description="Subnet CIDR or identifier") 
    gateway: Optional[IPvAnyAddress] = Field(None, description="Default gateway IP")
    vlan: Optional[str] = Field(None, max_length=20, description="VLAN identifier")
    
    # System Information
    os: Optional[str] = Field(None, max_length=100, description="Operating system")
    os_version: Optional[str] = Field(None, max_length=100, description="OS version")
    app_version: Optional[str] = Field(None, max_length=100, description="Application version")
    db_version: Optional[str] = Field(None, max_length=100, description="Database version")
    
    # Hardware Resources
    vcpu: Optional[int] = Field(None, ge=0, le=1000, description="Virtual CPU count")
    memory_gb: Optional[float] = Field(None, ge=0, le=10000, description="Memory in GB")
    
    # Asset Metadata
    hostname: Optional[str] = Field(None, max_length=255, description="Asset hostname")
    environment: Optional[str] = Field(None, pattern="^(dev|test|stage|prod|dr)$", description="Environment type")
    business_unit: Optional[str] = Field(None, max_length=100, description="Business unit owning the asset")
    asset_owner: Optional[str] = Field(None, max_length=100, description="Asset owner/responsible person")
    asset_criticality: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$", description="Asset criticality level")
    
    # Compliance & Security
    patch_level: Optional[str] = Field(None, max_length=50, description="Current patch level")
    security_zone: Optional[str] = Field(None, max_length=50, description="Security zone classification")
    compliance_tags: Optional[List[str]] = Field(None, description="Compliance requirements list")
    
    # Extended Properties (Flexible Schema)
    extended_properties: Optional[Dict[str, Any]] = Field(None, description="Additional asset properties")

    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Ensure IP address is valid"""
        try:
            return str(ipaddress.ip_address(v))
        except ValueError:
            raise ValueError('Invalid IP address format')

    @validator('subnet')
    def validate_subnet(cls, v):
        """Validate subnet format if provided"""
        if v and '/' in v:
            try:
                ipaddress.ip_network(v, strict=False)
            except ValueError:
                raise ValueError('Invalid subnet CIDR format')
        return v


class AssetRegistryCreate(AssetRegistryBase):
    """Schema for creating new assets"""
    created_by: str = Field(default='system', max_length=100, description="User who created the asset")


class AssetRegistryUpdate(BaseModel):
    """Schema for updating existing assets - all fields optional except IP"""
    
    # Network Information
    segment: Optional[str] = Field(None, max_length=100)
    subnet: Optional[str] = Field(None, max_length=50)
    gateway: Optional[str] = Field(None)  # Changed from IPvAnyAddress to str to avoid DB conversion issues
    vlan: Optional[str] = Field(None, max_length=20)
    
    # System Information  
    os: Optional[str] = Field(None, max_length=100)
    os_version: Optional[str] = Field(None, max_length=100)
    app_version: Optional[str] = Field(None, max_length=100)
    db_version: Optional[str] = Field(None, max_length=100)
    
    # Hardware Resources
    vcpu: Optional[int] = Field(None, ge=0, le=1000)
    memory_gb: Optional[float] = Field(None, ge=0, le=10000)
    
    # Asset Metadata
    hostname: Optional[str] = Field(None, max_length=255)
    environment: Optional[str] = Field(None, pattern="^(dev|test|stage|prod|dr)$")
    business_unit: Optional[str] = Field(None, max_length=100)
    asset_owner: Optional[str] = Field(None, max_length=100)
    asset_criticality: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    
    # Compliance & Security
    patch_level: Optional[str] = Field(None, max_length=50)
    security_zone: Optional[str] = Field(None, max_length=50)
    compliance_tags: Optional[List[str]] = Field(None)
    
    # Extended Properties
    extended_properties: Optional[Dict[str, Any]] = Field(None)
    
    # Update metadata
    updated_by: str = Field(default='system', max_length=100, description="User who updated the asset")


class AssetRegistryResponse(AssetRegistryBase):
    """Schema for asset responses"""
    id: int
    version: int
    is_active: bool
    data_source: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True


class AssetRegistryHistoryResponse(BaseModel):
    """Schema for asset history responses"""
    id: int
    asset_id: int
    ip_address: str
    version: int
    change_type: str
    change_description: Optional[str]
    asset_data_snapshot: Dict[str, Any]
    changed_fields: Optional[List[str]]
    previous_values: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: str
    upload_batch_id: Optional[str]

    class Config:
        from_attributes = True


class AssetUploadBatchResponse(BaseModel):
    """Schema for upload batch responses"""
    id: int
    batch_id: str
    upload_filename: str
    upload_sha256: str
    upload_size_bytes: int
    total_rows: int
    processed_rows: int
    created_assets: int
    updated_assets: int
    skipped_rows: int
    error_rows: int
    status: str
    error_details: Optional[Dict[str, Any]]
    processing_duration_ms: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    created_by: str

    class Config:
        from_attributes = True


class CSVUploadResponse(BaseModel):
    """Response for CSV upload operations"""
    batch_id: str
    message: str
    summary: Dict[str, Any]
    upload_details: AssetUploadBatchResponse


class AssetSearchFilters(BaseModel):
    """Schema for asset search and filtering"""
    ip_address: Optional[str] = Field(None, description="Exact or partial IP match")
    ip_range: Optional[str] = Field(None, description="IP range in CIDR format") 
    segment: Optional[str] = Field(None, description="Network segment")
    vlan: Optional[str] = Field(None, description="VLAN identifier")
    os: Optional[str] = Field(None, description="Operating system (partial match)")
    environment: Optional[str] = Field(None, description="Environment type")
    business_unit: Optional[str] = Field(None, description="Business unit")
    asset_criticality: Optional[str] = Field(None, description="Criticality level")
    security_zone: Optional[str] = Field(None, description="Security zone")
    is_active: Optional[bool] = Field(True, description="Include only active assets")
    hostname: Optional[str] = Field(None, description="Hostname (partial match)")
    
    # Pagination
    limit: int = Field(default=100, ge=1, le=1000, description="Number of results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class AssetAnalyticsResponse(BaseModel):
    """Analytics and insights about the asset registry"""
    total_assets: int
    active_assets: int
    inactive_assets: int
    environments: Dict[str, int]
    operating_systems: Dict[str, int] 
    criticality_levels: Dict[str, int]
    security_zones: Dict[str, int]
    business_units: Dict[str, int]
    average_vcpu: Optional[float]
    average_memory_gb: Optional[float]
    total_vcpu: Optional[int]
    total_memory_gb: Optional[float]
    last_updated: datetime
