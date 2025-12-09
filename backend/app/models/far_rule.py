"""
Database models for FAR processing - Phase 2.1/2.2
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, BigInteger, ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class FarRule(Base):
    """
    Model for normalized FAR rules
    """
    __tablename__ = "far_rules"
    
    id = Column(BigInteger, primary_key=True, index=True)
    request_id = Column(BigInteger, ForeignKey('far_requests.id'), nullable=False, index=True)
    canonical_hash = Column(LargeBinary, nullable=False)  # SHA256 hash for deduplication
    action = Column(Text, nullable=False, default='allow')
    direction = Column(Text, nullable=True)  # Optional direction
    facts = Column(JSONB, nullable=True)  # Rule-level facts in hybrid approach
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    request = relationship("FarRequest", back_populates="rules")
    endpoints = relationship("FarRuleEndpoint", back_populates="rule", cascade="all, delete-orphan")
    services = relationship("FarRuleService", back_populates="rule", cascade="all, delete-orphan")
    tuple_facts = relationship("FarTupleFacts", back_populates="rule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FarRule(id={self.id}, request_id={self.request_id}, action='{self.action}')>"


class FarRuleEndpoint(Base):
    """
    Model for normalized endpoints (IP networks) in FAR rules
    """
    __tablename__ = "far_rule_endpoints"
    
    id = Column(BigInteger, primary_key=True, index=True)
    rule_id = Column(BigInteger, ForeignKey('far_rules.id'), nullable=False, index=True)
    endpoint_type = Column(Text, nullable=False)  # 'source' or 'destination'
    network_cidr = Column(Text, nullable=False)  # CIDR notation like '10.0.0.0/24'
    
    # Relationship
    rule = relationship("FarRule", back_populates="endpoints")
    
    def __repr__(self):
        return f"<FarRuleEndpoint(rule_id={self.rule_id}, type='{self.endpoint_type}', cidr='{self.network_cidr}')>"


class FarRuleService(Base):
    """
    Model for normalized services (protocol/port ranges) in FAR rules
    """
    __tablename__ = "far_rule_services"
    
    id = Column(BigInteger, primary_key=True, index=True)
    rule_id = Column(BigInteger, ForeignKey('far_rules.id'), nullable=False, index=True)
    protocol = Column(Text, nullable=False)  # 'tcp', 'udp', etc.
    port_ranges = Column(Text, nullable=False)  # PostgreSQL formatted port ranges as text
    
    # Relationship
    rule = relationship("FarRule", back_populates="services")
    
    def __repr__(self):
        return f"<FarRuleService(rule_id={self.rule_id}, protocol='{self.protocol}', ranges='{self.port_ranges}')>"
