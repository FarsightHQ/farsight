"""Sync risky_port_policy recommendation text from baseline JSON.

Revision ID: 20260410120000
Revises: 20260408140000
Create Date: 2026-04-10

Updates `recommendation` for rows that match baseline identity
(protocol, port_start, port_end, label). Other rows are unchanged.

Downgrade is a no-op: prior recommendation text is not stored.
"""
from pathlib import Path

from alembic import op
from sqlalchemy.orm import sessionmaker

revision = "20260410120000"
down_revision = "20260408140000"
branch_labels = None
depends_on = None


def _baseline_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "app"
        / "seed_data"
        / "risky_port_policy_baseline.json"
    )


def upgrade() -> None:
    from app.seed_data.risky_port_policy_loader import (
        load_validated_entries_from_path,
        sync_baseline_recommendations_to_existing_rows,
    )

    path = _baseline_path()
    if not path.is_file():
        raise FileNotFoundError(f"Baseline JSON missing: {path}")

    entries = load_validated_entries_from_path(path)
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    session = Session()
    try:
        sync_baseline_recommendations_to_existing_rows(session, entries)
        session.commit()
    finally:
        session.close()


def downgrade() -> None:
    """Prior recommendation strings are not restored."""
    pass
