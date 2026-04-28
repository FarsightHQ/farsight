# Farsight

Farsight is an application for **firewall access rule (FAR) analysis**. You organize work in **projects**, bring in rule exports and optional asset data, and review **rules**, **facts**, and **analysis** in one place—so firewall reviews are repeatable and structured instead of scattered across spreadsheets.

---

## What Farsight does

### Who it’s for

Teams that need to **ingest firewall or access-rule exports**, **normalize** them into a consistent picture, and **review** them with structured facts and security-oriented insights—common in security engineering, network operations, and compliance reviews.

### Core ideas

- **Projects** — A project is an isolated workspace for your rule reviews, FAR requests, and project-scoped assets. You sign in once; everything you do is scoped to the projects you belong to (unless your organization uses a platform-wide administrator role).

- **FAR requests** — You upload a firewall-rules file (CSV) to open a FAR request. Farsight validates and normalizes the data so you get a clear view of sources, destinations, services, and actions.

- **Asset registry** — Optionally upload an asset registry (CSV) with IPs and context (for example segment, hostname, environment). When rules reference those addresses, analysis can **enrich** endpoints with registry context.

- **Facts and analysis** — The product computes **per-rule facts** and supports deeper analysis paths for security insights. You can summarize work at the request level, see involved addresses, and browse rules in context.

- **Visualization** — Data is available for **network-style views** (topology-oriented visualizations in the UI) so you can explore how rules relate to each other.

- **Risky port policy** — An application-wide **risky port list** (maintained by platform administrators) feeds into scoring and analysis so “risky” services are evaluated consistently.

### Typical workflow

1. **Sign in** with the account your administrator created in the identity system.
2. **Create a project** (you become the project owner) or **join** a project through an invitation from a colleague.
3. Optionally upload an **asset registry** for your project so rules can be enriched.
4. Create a **FAR request** by uploading a **firewall rules** CSV.
5. Run through **processing and analysis**, then use **facts**, summaries, and **rule browsing** (and graphs where available) to complete your review.

### Sample data

Example CSVs for trying uploads live under [samples/](samples/). See [samples/README.md](samples/README.md) for which file to use for assets vs. rules.

---

## Quick start (using the product)

These steps assume the **environment is already running** (for example after the initial Docker setup on your machine or a shared environment your team provides).

1. Open the **Farsight web app** in your browser at the URL your team uses (local development is often **http://localhost:3000**).
2. You will be redirected to **sign in**. Use the **username and password** an administrator created for you in Keycloak (see below if you are the one setting up users).
3. After login, **create a new project** or open a project you were **invited to**.
4. Optionally upload your **asset registry** CSV first, then create a **FAR request** and upload your **firewall rules** CSV.
5. Use the UI to move through **ingestion**, **facts**, **analysis**, and **visualizations** as needed for your review.

**Platform administration (optional):** Some settings (for example editing the global **risky port policy**) require a **platform administrator** role assigned in Keycloak (`farsight-admin` or `admin` realm role). Regular analysts only need a valid login and membership in the right projects.

---

## Initial setup: environment and Docker

1. Copy the example environment file and fill in the secrets your team requires (database, Keycloak admin password, backend client secret, pgAdmin password).  
   `cp .env.example .env`

2. From the repository root, start the stack:  
   `docker compose up --build`

3. Wait until Postgres and Keycloak are healthy and the backend has finished starting.

4. Start the web UI on your machine (not started by Compose by default):  
   `cd frontend && npm install && npm run dev`

5. Open the app (**http://localhost:3000** by default).

Details such as exact variables and ports are documented in [.env.example](.env.example) and [docker-compose.yml](docker-compose.yml).

---

## Configure Keycloak users (after Docker is up)

Self-registration is **disabled** in the bundled realm: each person needs a user created in Keycloak (or your organization’s equivalent). Use the **Keycloak Administration Console** with the admin account from your `.env` (`KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD`).

1. Open **http://localhost:8080** (or your configured Keycloak host/port).

2. Click **Administration Console** and sign in with the Keycloak **admin** credentials from `.env` (not the application realm users yet).

3. In the **master** realm menu (top-left), switch to the **`farsight`** realm.

4. **Create realm roles for platform admins (only if needed)**  
   Go to **Realm roles** → **Create role**. Add at least **`farsight-admin`** if it does not already exist. The application also treats a realm role named **`admin`** as a platform administrator. Assign these only to people who should manage global policy (for example risky ports) and see all projects.

5. **Create an application user**  
   Go to **Users** → **Create new user**. Set username, email, and name as appropriate → **Save**.

6. **Set a password**  
   Open the user → **Credentials** tab → **Set password**. Turn **Temporary** **off** so the user is not forced to change it on first login (unless your policy requires that).

7. **Assign platform admin role (optional)**  
   Open the user → **Role mapping** → **Assign role** → filter **Realm roles** → assign **`farsight-admin`** or **`admin`** for platform-wide administrators. Leave other users without these roles if they only need normal project access.

8. **What happens in Farsight**  
   - Any authenticated user can **create a project** and becomes **owner** of that project.  
   - Other users get access when an **owner** or **project admin** **invites them by email** or **adds their account** as a member (they must sign in with the email that matches the invitation when applicable).  
   - Users with **`farsight-admin`** or **`admin`** realm roles bypass project membership for access and can manage settings that apply to the whole deployment.

If you change the **`farsight-backend`** client secret in Keycloak, keep it aligned with **`KEYCLOAK_CLIENT_SECRET`** in `.env` and with [keycloak/import/farsight-realm.json](keycloak/import/farsight-realm.json) as described in [.env.example](.env.example).

---

## Further reading

- [backend/README.md](backend/README.md) — risky port policy and backend-oriented notes  
- [frontend/README.md](frontend/README.md) — frontend scripts and layout  

No `LICENSE` file is present in this repository; add one if you distribute the project.
