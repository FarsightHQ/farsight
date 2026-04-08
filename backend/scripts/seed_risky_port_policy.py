#!/usr/bin/env python3
"""
Load global risky port policy from JSON into the database.

Usage (from repo root or backend):

  cd backend && python scripts/seed_risky_port_policy.py
  cd backend && python scripts/seed_risky_port_policy.py --replace
  cd backend && python scripts/seed_risky_port_policy.py --dry-run

Requires DATABASE_URL (or POSTGRES_*) in the environment, same as the API.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.seed_data.risky_port_policy_loader import (  # noqa: E402
    apply_entries,
    default_baseline_path,
    load_validated_entries_from_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed risky_port_policy_entries from JSON.")
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help=f"Path to baseline JSON (default: {default_baseline_path()})",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete all existing policy rows before inserting (full replace).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate JSON only; do not write to the database.",
    )
    args = parser.parse_args()

    path = args.json or default_baseline_path()
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        entries = load_validated_entries_from_path(path)
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 1

    print(f"Validated {len(entries)} entries from {path}")

    if args.dry_run:
        print("Dry run: no database changes.")
        return 0

    db = SessionLocal()
    try:
        n = apply_entries(db, entries, replace=args.replace)
        if n == 0 and not args.replace:
            print("Table already has rows; skipped (use --replace to overwrite).")
        else:
            db.commit()
            print(f"Inserted {n} row(s).")
        return 0
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
