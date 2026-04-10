"""Tests for risky port policy baseline loader."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.seed_data.risky_port_policy_loader import (
    apply_entries,
    default_baseline_path,
    load_baseline_json,
    load_validated_entries_from_path,
    sync_baseline_recommendations_to_existing_rows,
    validate_entries,
)


def test_default_baseline_exists_and_validates():
    path = default_baseline_path()
    assert path.is_file()
    entries = load_validated_entries_from_path(path)
    assert len(entries) >= 40
    ssh = [e for e in entries if e.port_start == 22 and e.port_end == 22 and e.protocol == "tcp"]
    assert len(ssh) == 1
    assert ssh[0].severity == "info"
    assert ssh[0].recommendation and "CIS" in ssh[0].recommendation


def test_validate_entries_rejects_bad_port_range(tmp_path: Path):
    bad = [{"protocol": "tcp", "port_start": 100, "port_end": 50, "label": "x", "severity": "high", "enabled": True, "sort_order": 0}]
    with pytest.raises(ValueError):
        validate_entries(bad)


def test_load_baseline_json_requires_array(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text('{"not": "array"}', encoding="utf-8")
    with pytest.raises(ValueError, match="array"):
        load_baseline_json(p)


def test_apply_entries_insert_when_empty_then_skip():
    session = MagicMock()
    q = session.query.return_value
    q.count.side_effect = [0, len(load_validated_entries_from_path(default_baseline_path()))]

    entries = load_validated_entries_from_path(default_baseline_path())
    n1 = apply_entries(session, entries, replace=False)
    assert n1 == len(entries)
    assert session.add.call_count == len(entries)

    n2 = apply_entries(session, entries, replace=False)
    assert n2 == 0
    # Second call: no additional adds beyond the first batch
    assert session.add.call_count == len(entries)


def test_apply_entries_replace_deletes_and_inserts():
    session = MagicMock()
    session.query.return_value.count.return_value = 0

    minimal = [
        {
            "protocol": "tcp",
            "port_start": 1,
            "port_end": 1,
            "label": "one",
            "recommendation": None,
            "severity": "info",
            "enabled": True,
            "sort_order": 0,
        }
    ]
    e1 = validate_entries(minimal)
    n = apply_entries(session, e1, replace=True)
    assert n == 1
    session.query.return_value.delete.assert_called_once()
    session.add.assert_called_once()


def test_sync_baseline_recommendations_updates_when_changed():
    session = MagicMock()
    row = SimpleNamespace(recommendation="old recommendation text")
    session.query.return_value.filter.return_value.first.return_value = row
    entries = validate_entries(
        [
            {
                "protocol": "tcp",
                "port_start": 22,
                "port_end": 22,
                "label": "SSH",
                "recommendation": "new recommendation text",
                "severity": "info",
                "enabled": True,
                "sort_order": 12,
            }
        ]
    )
    assert sync_baseline_recommendations_to_existing_rows(session, entries) == 1
    assert row.recommendation == "new recommendation text"


def test_sync_baseline_recommendations_noop_when_unchanged():
    session = MagicMock()
    row = SimpleNamespace(recommendation="same")
    session.query.return_value.filter.return_value.first.return_value = row
    entries = validate_entries(
        [
            {
                "protocol": "tcp",
                "port_start": 22,
                "port_end": 22,
                "label": "SSH",
                "recommendation": "same",
                "severity": "info",
                "enabled": True,
                "sort_order": 12,
            }
        ]
    )
    assert sync_baseline_recommendations_to_existing_rows(session, entries) == 0


def test_sync_baseline_recommendations_skips_missing_row():
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    entries = validate_entries(
        [
            {
                "protocol": "tcp",
                "port_start": 22,
                "port_end": 22,
                "label": "SSH",
                "recommendation": "x",
                "severity": "info",
                "enabled": True,
                "sort_order": 12,
            }
        ]
    )
    assert sync_baseline_recommendations_to_existing_rows(session, entries) == 0
