"""
Database model for FAR (Federated Access Request) 
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class FarRequest(Base):
    """
    Model for FAR (File Analysis Request) submissions
    """
    __tablename__ = "far_requests"
    
    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    external_id = Column(Text, nullable=True)
    source_filename = Column(Text, nullable=False)
    source_sha256 = Column(Text, nullable=False)
    source_size_bytes = Column(BigInteger, nullable=False)
    storage_path = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default='submitted')
    created_by = Column(Text, nullable=False, default='system')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    rules = relationship("FarRule", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FarRequest(id={self.id}, title='{self.title}', status='{self.status}')>"
