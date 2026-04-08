"""
Global (application-wide) risky port policy entries for FAR security analysis.
"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


class RiskyPortPolicyEntry(Base):
    __tablename__ = "risky_port_policy_entries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    protocol = Column(String(10), nullable=False)
    port_start = Column(Integer, nullable=False)
    port_end = Column(Integer, nullable=False)
    label = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<RiskyPortPolicyEntry(id={self.id}, {self.protocol} "
            f"{self.port_start}-{self.port_end}, {self.label!r})>"
        )
