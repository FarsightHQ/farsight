"""
Project workspace models: membership, invitations, asset links.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    legacy_unrestricted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_sub = Column(Text, nullable=True)

    members = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    invitations = relationship(
        "ProjectInvitation",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    asset_links = relationship(
        "ProjectAsset",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    far_requests = relationship("FarRequest", back_populates="project")


class ProjectMember(Base):
    __tablename__ = "project_members"

    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    user_sub = Column(String(512), primary_key=True)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="members")


class ProjectInvitation(Base):
    __tablename__ = "project_invitations"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_project_invitations_token_hash"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(320), nullable=False)
    role = Column(String(50), nullable=False)
    token_hash = Column(String(128), nullable=False)
    invited_by_sub = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="invitations")


class ProjectAsset(Base):
    __tablename__ = "project_assets"

    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    asset_registry_id = Column(BigInteger, ForeignKey("asset_registry.id", ondelete="CASCADE"), primary_key=True)
    linked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    linked_by_sub = Column(Text, nullable=True)

    project = relationship("Project", back_populates="asset_links")
    asset = relationship("AssetRegistry", back_populates="project_links")
