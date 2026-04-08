# Farsight backend

FastAPI service for firewall rule ingestion and analysis.

## Risky port policy seed

The global risky port list lives in `app/seed_data/risky_port_policy_baseline.json`. On a **fresh database**, running **`alembic upgrade head`** inserts those rows only when `risky_port_policy_entries` is **empty**, so existing deployments are not overwritten.

To load or reload manually (uses `DATABASE_URL` or `POSTGRES_*` from the environment):

```bash
cd backend
python scripts/seed_risky_port_policy.py              # insert if table is empty
python scripts/seed_risky_port_policy.py --replace    # delete all policy rows, then insert baseline
python scripts/seed_risky_port_policy.py --dry-run    # validate JSON only
python scripts/seed_risky_port_policy.py --json /path/to/custom.json
```

Saving the policy from the Settings UI requires a **platform admin** JWT role: **`admin`** or **`farsight-admin`** (realm or `farsight-backend` client roles, same as project admin bypass). The seed script bypasses HTTP and writes directly to the database.
