# Sample uploads

Small CSVs you can use after creating a project (replace `PROJECT_ID` and send a valid bearer token).

1. **Asset registry** — upload first so rule IPs can enrich from the registry:

   `POST /api/v1/projects/PROJECT_ID/assets/upload-csv`  
   Multipart field `file` → `asset_registry_sample.csv`

2. **FAR request** — firewall rule CSV:

   `POST /api/v1/projects/PROJECT_ID/far`  
   Form fields: `title` (string), `file` → `far_request_sample.csv`

Host IPs in `far_request_sample.csv` match rows in `asset_registry_sample.csv` where applicable. The CIDR row is for structure demos only.
