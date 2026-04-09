# Farsight

Farsight is a **firewall access rule (FAR) analysis** application. You work inside **projects**: upload firewall rule CSVs, optionally load an **asset registry** for enrichment, and explore rules, facts, and analysis through a **Vue** frontend. The **FastAPI** backend is protected with **Keycloak** (JWT).

## Product details

### What it is for

Farsight helps teams **ingest firewall or access-rule exports** (CSV), **normalize** them into a consistent rule model, and **review** them with structured **facts**, **risk-oriented analysis**, and UI workflows. It suits security engineering, network operations, and compliance-style reviews where you need repeatable processing beyond ad hoc spreadsheets.

### Main capabilities

- **Projects** — Each **project** is an isolated workspace for FAR requests, rules, and project-scoped assets. Users authenticate via **OpenID Connect (Keycloak)**; API access is JWT-based with project membership and roles enforced on scoped routes.
- **FAR requests** — Upload a firewall-rules CSV to create a **FAR request**. The backend validates structure, parses rows, and stores **normalized rules** (sources, destinations, services, actions).
- **Asset registry** — Upload a separate **asset registry CSV** (IPs and metadata such as segment, OS, hostname, environment). Assets can be linked to a project so rule endpoints can be **enriched** with registry context during analysis.
- **Facts and analysis** — The system computes **per-rule facts** and supports **hybrid** / deeper analysis paths for security insights. You can summarize activity at the **request** level, list involved **IPs**, and browse **rules** across requests (project-scoped under `/api/v1/projects/{project_id}/...`).
- **Graphs** — Data is exposed for **network-style visualization** (topology views compatible with graph consumers in the UI).
- **Risky port policy** — An application-wide **risky port list** (configurable by privileged users) feeds into security scoring and analysis. Baseline data can be seeded with Alembic or scripts; see [backend/README.md](backend/README.md).

### Typical workflow

1. Create or join a **project**.
2. Optionally upload **asset registry** CSV for the project.
3. Create a **FAR request** by uploading a **firewall rules** CSV.
4. Run **ingestion / processing** as needed, then use **analysis**, **facts**, and **rule browsers** in the UI or via the API.

### API shape

Versioned JSON API under **`/api/v1`**, with standardized success/error envelopes, pagination where applicable, and OpenAPI documentation at **`/docs`** when running in development. Project-scoped resources live under **`/api/v1/projects/{project_id}/`** (for example FAR routes under `.../far`, assets under `.../assets`, rules under `.../rules`).

## Architecture

- The browser talks to the SPA and to Keycloak on **localhost** (typical dev).
- The SPA calls the API on **localhost:8000** (Vite proxies `/api` to the backend in development).
- Inside Docker Compose, the backend uses **`http://keycloak:8080`** to validate tokens and **`postgres`** as the database host.

```mermaid
flowchart LR
  subgraph host [Developer machine]
    Browser[Browser]
    VueSPA["Vue SPA Vite"]
  end
  subgraph compose [Docker Compose]
    API[FastAPI]
    KC[Keycloak]
    DB[(Postgres)]
  end
  Browser --> VueSPA
  Browser --> KC
  VueSPA --> API
  API --> KC
  API --> DB
```

## Repository layout

| Path | Purpose |
|------|---------|
| [backend/](backend/) | FastAPI app, Alembic migrations, services |
| [frontend/](frontend/) | Vue 3 + Vite UI |
| [keycloak/import/](keycloak/import/) | Realm export for local Keycloak (`--import-realm`) |
| [samples/](samples/) | Small CSV examples for asset registry and FAR uploads |
| [tests/testdata_generation/](tests/testdata_generation/) | Generators for larger synthetic CSVs |
| [docker-compose.yml](docker-compose.yml) | Postgres, Keycloak, backend, pgAdmin, Swagger UI |

## Prerequisites

- **Docker** and **Docker Compose** (recommended for Postgres, Keycloak, and API)
- **Node.js** and **npm** (for the frontend; not containerized in Compose)
- **Python 3** (only if you run the backend or Alembic on the host instead of in Docker)

## Quick start

### 1. Environment

Copy the example env file and set secrets:

```bash
cp .env.example .env
```

**Required for `docker compose up`:** set at least `POSTGRES_PASSWORD`, `KEYCLOAK_ADMIN_PASSWORD`, `KEYCLOAK_CLIENT_SECRET`, and `PGADMIN_PASSWORD`. Use the **same** `POSTGRES_PASSWORD` in `DATABASE_URL` when you run tools on the host against the Compose-published Postgres port.

**Keycloak client secret:** `KEYCLOAK_CLIENT_SECRET` must match the **`farsight-backend`** confidential client secret in [keycloak/import/farsight-realm.json](keycloak/import/farsight-realm.json). If you change the secret in that JSON, update `.env` accordingly. See [.env.example](.env.example) for all related variables.

### 2. Backend stack (Compose)

From the repository root:

```bash
docker compose up --build
```

The backend container runs **`alembic upgrade head`** then **`uvicorn`** (see [docker-compose.yml](docker-compose.yml)). Wait for Postgres and Keycloak to become healthy before using the API.

### 3. Frontend (host)

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) (port is set in [frontend/vite.config.js](frontend/vite.config.js)).

Optional [frontend](frontend/) environment variables (defaults work for local dev):

- `VITE_API_BASE_URL` — API base URL (default `http://localhost:8000`)
- `VITE_KEYCLOAK_URL`, `VITE_KEYCLOAK_REALM`, `VITE_KEYCLOAK_CLIENT_ID` — see [frontend/src/services/keycloak.ts](frontend/src/services/keycloak.ts)

## Service URLs (default ports)

| Service | URL | Notes |
|---------|-----|--------|
| API | [http://localhost:8000](http://localhost:8000) | Interactive docs: `/docs`, OpenAPI: `/openapi.json` |
| Keycloak | [http://localhost:8080](http://localhost:8080) | Realm: `farsight` |
| Swagger UI (container) | [http://localhost:8081](http://localhost:8081) | Uses `SWAGGER_PORT` (default **8081** in Compose) |
| pgAdmin | [http://localhost:5050](http://localhost:5050) | Uses `PGADMIN_PORT` |

## Sample CSV uploads

Curated files live under [samples/](samples/). Upload the asset registry CSV before the FAR rules CSV if you want IP enrichment to line up. See [samples/README.md](samples/README.md) for API paths and field names.

## Local development (backend on the host)

1. Run Postgres and Keycloak (e.g. via Docker Compose, or your own installs).
2. Point `DATABASE_URL` (or `POSTGRES_*`) at Postgres on **localhost** with the same database name and credentials as Compose.
3. For JWT validation, set `KEYCLOAK_URL` to **http://localhost:8080** when the backend runs on the host (not `http://keycloak:8080`).
4. From `backend/`: create a virtualenv, install dependencies, then:

   ```bash
   alembic upgrade head
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

Risky-port policy seeding and admin scripts are described in [backend/README.md](backend/README.md).

## Testing and synthetic data

- **Backend:** from `backend/`, run `PYTHONPATH=. pytest` (install dependencies from `backend/requirements.txt` first).
- **Frontend:** `npm test` in [frontend/](frontend/).
- **Large generated CSVs:** [tests/testdata_generation/README.md](tests/testdata_generation/README.md) (generators; most `*.csv` files are gitignored except [samples/](samples/)).

## Further reading

- [backend/README.md](backend/README.md) — risky port policy seeding
- [frontend/README.md](frontend/README.md) — Vue/Vite scripts and structure

No `LICENSE` file is present in this repository; add one if you distribute the project.
