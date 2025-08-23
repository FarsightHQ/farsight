"""
Database model for FAR tuple-level facts
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class FarTupleFacts(Base):
    """
    Model for tuple-level facts storage in hybrid facts approach
    """
    __tablename__ = "far_tuple_facts"
    
    id = Column(BigInteger, primary_key=True, index=True)
    rule_id = Column(BigInteger, ForeignKey('far_rules.id'), nullable=False, index=True)
    source_cidr = Column(Text, nullable=False, index=True)
    destination_cidr = Column(Text, nullable=False, index=True)
    facts = Column(JSONB, nullable=False)  # Tuple-specific facts
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    rule = relationship("FarRule", back_populates="tuple_facts")
    
    def __repr__(self):
        return f"<FarTupleFacts(rule_id={self.rule_id}, src={self.source_cidr}, dst={self.destination_cidr})>"
