"""
Pydantic schemas for Asset Registry operations
"""
from pydantic import BaseModel, Field, IPvAnyAddress, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import ipaddress


class AssetRegistryBase(BaseModel):
    """Base schema for Asset Registry with validation - CSV compatible fields only"""
    
    # Core Asset Identification
    ip_address: str = Field(..., description="Primary asset identifier - must be unique")
    
    # Network Information
    segment: Optional[str] = Field(None, max_length=100, description="Network segment identifier")
    subnet: Optional[str] = Field(None, max_length=50, description="Subnet CIDR or identifier") 
    gateway: Optional[str] = Field(None, max_length=50, description="Default gateway IP")
    vlan: Optional[str] = Field(None, max_length=50, description="VLAN identifier")
    
    # System Information
    os_name: Optional[str] = Field(None, max_length=100, description="Operating system name")
    os_version: Optional[str] = Field(None, max_length=100, description="OS version")
    app_version: Optional[str] = Field(None, max_length=100, description="Application version")
    db_version: Optional[str] = Field(None, max_length=100, description="Database version")
    
    # Hardware Resources
    vcpu: Optional[int] = Field(None, ge=0, le=1000, description="Virtual CPU count")
    memory: Optional[str] = Field(None, max_length=20, description="Memory amount (e.g., '8GB')")
    
    # Asset Metadata
    hostname: Optional[str] = Field(None, max_length=255, description="Asset hostname")
    vm_display_name: Optional[str] = Field(None, max_length=255, description="VM display name")
    environment: Optional[str] = Field(None, max_length=50, description="Environment type")
    location: Optional[str] = Field(None, max_length=100, description="Physical location")
    availability: Optional[str] = Field(None, max_length=50, description="Availability status")
    itm_id: Optional[str] = Field(None, max_length=50, description="ITM monitoring ID")
    
    # Compliance & Security (Direct CSV columns)
    tool_update: Optional[str] = Field(None, max_length=200, description="Tool Update from CSV")
    dmz_mz: Optional[str] = Field(None, max_length=50, description="DMZ/MZ zone from CSV")
    confidentiality: Optional[str] = Field(None, max_length=50, description="Confidentiality level from CSV")
    integrity: Optional[str] = Field(None, max_length=50, description="Integrity level from CSV")
    compliance_tags: Optional[List[str]] = Field(None, description="Additional compliance tags")
    
    # Extended Properties (Flexible Schema)
    extended_properties: Optional[Dict[str, Any]] = Field(None, description="Additional asset properties")

    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Ensure IP address is valid string format"""
        if v:
            return str(v).strip()
        return v

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
    gateway: Optional[str] = Field(None, max_length=50)
    vlan: Optional[str] = Field(None, max_length=50)
    
    # System Information  
    os_name: Optional[str] = Field(None, max_length=100)
    os_version: Optional[str] = Field(None, max_length=100)
    app_version: Optional[str] = Field(None, max_length=100)
    db_version: Optional[str] = Field(None, max_length=100)
    
    # Hardware Resources
    vcpu: Optional[int] = Field(None, ge=0, le=1000)
    memory: Optional[str] = Field(None, max_length=20)
    
    # Asset Metadata
    hostname: Optional[str] = Field(None, max_length=255)
    vm_display_name: Optional[str] = Field(None, max_length=255)
    environment: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    availability: Optional[str] = Field(None, max_length=50)
    itm_id: Optional[str] = Field(None, max_length=50)
    
    # Compliance & Security (Direct CSV columns)
    tool_update: Optional[str] = Field(None, max_length=200)
    dmz_mz: Optional[str] = Field(None, max_length=50)
    confidentiality: Optional[str] = Field(None, max_length=50)
    integrity: Optional[str] = Field(None, max_length=50)
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
    criticality_levels: Dict[str, int]  # Empty for now
    security_zones: Dict[str, int]  # Empty for now
    business_units: Dict[str, int]  # Empty for now
    average_vcpu: Optional[float]
    average_memory_gb: Optional[float]  # Always None (memory is string)
    total_vcpu: Optional[int]
    total_memory_gb: Optional[float]  # Always None (memory is string)
    last_updated: datetime


class AssetFilterOptionsResponse(BaseModel):
    """Unique filter values for asset filtering"""
    segments: List[str] = Field(default_factory=list, description="Unique segment values")
    vlans: List[str] = Field(default_factory=list, description="Unique VLAN values")
    environments: List[str] = Field(default_factory=list, description="Unique environment values")
    os_names: List[str] = Field(default_factory=list, description="Unique OS name values")
