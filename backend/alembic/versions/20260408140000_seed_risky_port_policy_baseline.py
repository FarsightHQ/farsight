"""Seed risky_port_policy_entries from baseline JSON when table is empty.

Revision ID: 20260408140000
Revises: 20260408120000
Create Date: 2026-04-08

Downgrade is a no-op: seeded rows are not distinguishable from user-created rows.
"""
from pathlib import Path

from alembic import op
from sqlalchemy.orm import sessionmaker

revision = "20260408140000"
down_revision = "20260408120000"
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
    from app.seed_data.risky_port_policy_loader import apply_entries, load_validated_entries_from_path

    path = _baseline_path()
    if not path.is_file():
        raise FileNotFoundError(f"Baseline JSON missing: {path}")

    entries = load_validated_entries_from_path(path)
    bind = op.get_bind()
    Session = sessionmaker(bind=bind)
    session = Session()
    try:
        inserted = apply_entries(session, entries, replace=False)
        session.commit()
        if inserted:
            # Alembic logs upgrade steps; optional print for operators
            pass
    finally:
        session.close()


def downgrade() -> None:
    """Do not delete rows: cannot safely distinguish seeded vs user data."""
    pass
