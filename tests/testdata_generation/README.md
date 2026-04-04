# Test data generation

Synthetic **asset registry** CSVs, **firewall rule** CSVs, and **error-scenario** fixtures for local development and automated tests. Reference YAML under `reference/` is the single source of truth for topology, asset profiles, and rule templates.

## Layout

| Path | Purpose |
|------|---------|
| `reference/` | `network_topology.yaml`, `asset_profiles.yaml`, `firewall_patterns.yaml` |
| `scripts/` | Python generators and API verification helper |
| `generated/assets/` | `asset_registry_{small,medium,large}.csv` plus matching `*_manifest.json` |
| `generated/firewall_rules/` | `rules_{clean,security_audit,all_facts,cross_zone,scale}.csv` |
| `generated/error_scenarios/` | Negative-test firewall CSVs and `not_a_csv.txt` |

**Git:** Repository `.gitignore` ignores `*.csv`, so generated CSVs are not committed. Run `run_all_generators.sh` after clone. VLAN IP manifests (`*_manifest.json`) under `generated/assets/` are tracked when they change.

Firewall rule CSVs are built from VLAN→IP lists in the asset manifest so rule endpoints line up with `AssetService.get_asset_by_ip()` enrichment when you load the **same** asset file (or a superset) that was used to build that manifest.

## Dependencies

Generators need **Python 3** with **PyYAML** (`pip install pyyaml`). The backend virtualenv usually already has it; otherwise install into your environment.

## Regenerate everything

From the repository root:

```bash
./tests/testdata_generation/run_all_generators.sh
```

Or manually from `tests/testdata_generation/scripts/`:

```bash
SEED=42
python generate_assets.py --size small --seed "$SEED"
python generate_assets.py --size medium --seed "$SEED"
python generate_assets.py --size large --seed "$SEED"

python generate_firewall_rules.py --scenario clean --seed "$SEED" \
  --asset-manifest ../generated/assets/asset_registry_medium_manifest.json
python generate_firewall_rules.py --scenario security_audit --seed "$SEED" \
  --asset-manifest ../generated/assets/asset_registry_medium_manifest.json
python generate_firewall_rules.py --scenario all_facts --seed "$SEED" \
  --asset-manifest ../generated/assets/asset_registry_medium_manifest.json
python generate_firewall_rules.py --scenario cross_zone --seed "$SEED" \
  --asset-manifest ../generated/assets/asset_registry_medium_manifest.json
python generate_firewall_rules.py --scenario scale --seed "$SEED" \
  --asset-manifest ../generated/assets/asset_registry_large_manifest.json

python generate_error_scenarios.py
```

### CLI options

- **`generate_assets.py`**: `--size small|medium|large` (50 / 500 / 5000 rows), `--seed`, `--output` (default `../generated/assets/`).
- **`generate_firewall_rules.py`**: `--scenario clean|security_audit|all_facts|cross_zone|scale`, `--seed`, `--asset-manifest` (required), `--output`, `--tuple-cap`.
- **`generate_error_scenarios.py`**: optional `--output` (default `../generated/error_scenarios/`).

## Using the CSVs in the app

1. **Asset registry** — `POST /api/v1/assets/upload-csv` with the generated asset CSV (multipart field `file`).
2. **Firewall rules** — `POST /api/v1/far` with form fields `title` (string) and `file` (CSV). Use `rules_*.csv` or `error_scenarios/valid_sample.csv` for positive paths.

For enrichment to match generated rules, upload **`asset_registry_medium.csv`** before ingesting rules that were built from `asset_registry_medium_manifest.json` (`rules_clean`, `rules_security_audit`, `rules_all_facts`, `rules_cross_zone`). Use **`asset_registry_large.csv`** before **`rules_scale.csv`**.

## Verify ingestion via the API (in-process)

This uses FastAPI’s `TestClient`, overrides JWT auth, and talks to the real database from `DATABASE_URL` / `POSTGRES_*` in `.env`.

```bash
# Use the backend virtualenv (or any env with backend/requirements.txt installed).
cd backend && PYTHONPATH=. python ../tests/testdata_generation/scripts/verify_api_load.py
```

- Uploads `generated/assets/asset_registry_medium.csv` and `generated/firewall_rules/rules_clean.csv` (paths resolved relative to the repo root).
- Exits non-zero if the DB is unreachable or either upload does not return a success response.

To skip (e.g. CI without Postgres):

```bash
export SKIP_TESTDATA_API_VERIFY=1
```

Successful runs **create** a FAR request and asset upload batch in the database (same as a normal UI/API upload).

## After schema or mapping changes

1. Update `reference/*.yaml` and/or `scripts/models.py` / generators as needed.
2. Re-run `run_all_generators.sh`.
3. Re-run `verify_api_load.py` against a migrated database.
