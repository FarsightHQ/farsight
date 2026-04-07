"""
Database model for Asset Registry System
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, Boolean, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class AssetRegistry(Base):
    """
    Main Asset Registry model - stores all asset information
    """
    __tablename__ = "asset_registry"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Core Asset Identification (UNIQUE CONSTRAINT)
    ip_address = Column(String(50), nullable=False, unique=True, index=True, comment="Primary asset identifier - must be unique")
    
    # Network Information
    segment = Column(String(100), nullable=True, index=True)
    subnet = Column(String(50), nullable=True)
    gateway = Column(String(50), nullable=True)  # Changed from INET to String to handle various formats
    vlan = Column(String(50), nullable=True, index=True)
    
    # System Information
    os_name = Column(String(100), nullable=True, index=True)  # Renamed from 'os'
    os_version = Column(String(100), nullable=True)
    app_version = Column(String(100), nullable=True)
    db_version = Column(String(100), nullable=True)
    
    # Hardware Resources
    vcpu = Column(Integer, nullable=True)
    memory = Column(String(20), nullable=True)  # Changed to string to handle formats like "8GB"
    
    # Asset Metadata
    hostname = Column(String(255), nullable=True, index=True)
    vm_display_name = Column(String(255), nullable=True)  # Added VM display name
    environment = Column(String(50), nullable=True, index=True)  # dev/stage/prod
    location = Column(String(100), nullable=True)  # Added location field
    availability = Column(String(50), nullable=True)  # Added availability field
    itm_id = Column(String(50), nullable=True)  # Added ITM ID field
    
    # Compliance & Security
    tool_update = Column(String(200), nullable=True, index=True)  # Direct from CSV "Tool_Update" column
    dmz_mz = Column(String(50), nullable=True, index=True)  # Direct from CSV "DMZ/MZ" column
    confidentiality = Column(String(50), nullable=True, index=True)  # Direct from CSV "Confidentially" column
    integrity = Column(String(50), nullable=True, index=True)  # Direct from CSV "Integrity" column
    compliance_tags = Column(JSONB, nullable=True)  # For any additional compliance data
    
    # Extended Properties (Flexible Schema)
    extended_properties = Column(JSONB, nullable=True, comment="Flexible JSON storage for additional asset properties")
    
    # Data Management
    data_source = Column(String(100), nullable=False, default='csv_upload')
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=False, default='system')
    updated_by = Column(String(100), nullable=False, default='system')

    project_links = relationship(
        "ProjectAsset",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<AssetRegistry(id={self.id}, ip='{self.ip_address}', hostname='{self.hostname}', version={self.version})>"


class AssetUploadBatch(Base):
    """
    Track CSV upload batches for auditing and rollback capabilities
    """
    __tablename__ = "asset_upload_batches"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Batch Information
    batch_id = Column(String(100), nullable=False, unique=True, index=True)
    upload_filename = Column(String(500), nullable=False)
    upload_sha256 = Column(String(64), nullable=False)
    upload_size_bytes = Column(BigInteger, nullable=False)
    
    # Processing Results
    total_rows = Column(Integer, nullable=False)
    processed_rows = Column(Integer, nullable=False)
    created_assets = Column(Integer, nullable=False, default=0)
    updated_assets = Column(Integer, nullable=False, default=0)
    skipped_rows = Column(Integer, nullable=False, default=0)
    error_rows = Column(Integer, nullable=False, default=0)
    
    # Status and Metadata
    status = Column(String(50), nullable=False, default='processing')  # processing/completed/failed/completed_with_errors
    error_details = Column(JSONB, nullable=True)
    processing_duration_ms = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=False, default='system')
    project_id = Column(BigInteger, ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)

    def __repr__(self):
        return f"<AssetUploadBatch(batch_id='{self.batch_id}', status='{self.status}', assets={self.created_assets + self.updated_assets})>"
