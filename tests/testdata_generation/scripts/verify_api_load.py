#!/usr/bin/env python3
"""
Verify generated asset and firewall CSVs load through the FastAPI app.

Uses TestClient + dependency override for JWT auth. Requires PostgreSQL
reachable via DATABASE_URL / POSTGRES_* (same as the running backend).

Skip with: SKIP_TESTDATA_API_VERIFY=1

Run from repository root:
  cd backend && PYTHONPATH=. python ../tests/testdata_generation/scripts/verify_api_load.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _backend_dir() -> Path:
    return _repo_root() / "backend"


def _ensure_backend_path() -> None:
    bd = str(_backend_dir())
    if bd not in sys.path:
        sys.path.insert(0, bd)


def main() -> int:
    if os.environ.get("SKIP_TESTDATA_API_VERIFY", "").strip() in ("1", "true", "yes"):
        print("SKIP_TESTDATA_API_VERIFY set — skipping API load verification.")
        return 0

    _ensure_backend_path()

    from sqlalchemy import text

    from app.core.auth import get_current_user
    from app.core.database import engine
    from app.main import app
    from starlette.testclient import TestClient

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(
            "Cannot connect to the database (check DATABASE_URL / POSTGRES_* and that "
            f"Postgres is running): {e}",
            file=sys.stderr,
        )
        return 2

    root = _repo_root()
    asset_csv = root / "tests/testdata_generation/generated/assets/asset_registry_medium.csv"
    rules_csv = root / "tests/testdata_generation/generated/firewall_rules/rules_clean.csv"

    for p in (asset_csv, rules_csv):
        if not p.is_file():
            print(f"Missing generated file: {p}", file=sys.stderr)
            return 3

    async def mock_user():
        return {
            "sub": "testdata-api-verify",
            "username": "testdata_api_verify",
            "roles": [],
        }

    app.dependency_overrides[get_current_user] = mock_user
    try:
        client = TestClient(app)

        with asset_csv.open("rb") as f:
            r1 = client.post(
                "/api/v1/assets/upload-csv",
                files={"file": (asset_csv.name, f, "text/csv")},
            )
        body1 = r1.json()
        if r1.status_code != 200 or body1.get("status") != "success":
            print(f"Asset upload failed: {r1.status_code} {body1}", file=sys.stderr)
            return 4

        with rules_csv.open("rb") as f:
            r2 = client.post(
                "/api/v1/far",
                data={"title": "testdata_generation verify — rules_clean"},
                files={"file": (rules_csv.name, f, "text/csv")},
            )
        body2 = r2.json()
        if r2.status_code not in (200, 201) or body2.get("status") != "success":
            print(f"FAR upload failed: {r2.status_code} {body2}", file=sys.stderr)
            return 5

        print("API verification OK: asset CSV and rules_clean.csv ingested successfully.")
        return 0
    finally:
        app.dependency_overrides.pop(get_current_user, None)


if __name__ == "__main__":
    raise SystemExit(main())
