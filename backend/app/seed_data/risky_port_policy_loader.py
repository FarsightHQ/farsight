"""
Load and apply risky port policy baseline from JSON (shared by CLI and Alembic).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Union

from sqlalchemy.orm import Session

from app.models.risky_port_policy import RiskyPortPolicyEntry
from app.schemas.risky_port_policy import RiskyPortPolicyEntryCreate


def default_baseline_path() -> Path:
    """Path to packaged baseline JSON (next to this module)."""
    return Path(__file__).resolve().parent / "risky_port_policy_baseline.json"


def load_baseline_json(path: Union[str, Path]) -> List[dict]:
    """Read JSON array from disk. Does not validate."""
    p = Path(path)
    with p.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Baseline JSON must be a JSON array")
    return data


def validate_entries(raw: List[dict]) -> List[RiskyPortPolicyEntryCreate]:
    """Validate each object with Pydantic (same rules as API)."""
    return [RiskyPortPolicyEntryCreate.model_validate(item) for item in raw]


def load_validated_entries_from_path(path: Union[str, Path]) -> List[RiskyPortPolicyEntryCreate]:
    raw = load_baseline_json(path)
    return validate_entries(raw)


def apply_entries(
    session: Session,
    entries: List[RiskyPortPolicyEntryCreate],
    *,
    replace: bool = False,
) -> int:
    """
    Persist entries. If replace=True, delete all rows then insert.
    If replace=False, insert only when the table is empty (no-op otherwise).

    Returns number of rows inserted.
    """
    count_existing = session.query(RiskyPortPolicyEntry).count()
    if not replace and count_existing > 0:
        return 0

    if replace:
        session.query(RiskyPortPolicyEntry).delete()

    inserted = 0
    for item in entries:
        row = RiskyPortPolicyEntry(
            protocol=item.protocol,
            port_start=item.port_start,
            port_end=item.port_end,
            label=item.label,
            recommendation=item.recommendation,
            severity=item.severity,
            enabled=item.enabled,
            sort_order=item.sort_order,
        )
        session.add(row)
        inserted += 1
    return inserted
