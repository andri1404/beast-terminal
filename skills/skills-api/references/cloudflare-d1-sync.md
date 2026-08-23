# Cloudflare D1 Sync — Public API Architecture

## Dual Architecture

```
┌─────────────────────────────────────────────────────┐
│ LOCAL (Hermes)                                      │
│ skills-hub.db (514MB SQLite)                        │
│ → MCP v2 (mcp_server_v2.py)                         │
│ → Used by sniff-exploit, web-pentest-recon, etc.    │
└─────────────────────────────────────────────────────┘
                        │
                   sync_to_api.py
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│ PUBLIC API (Cloudflare)                             │
│ skills-api.anzanesia.uk                             │
│ → Cloudflare Workers + D1                           │
│ → Hono framework (TypeScript)                       │
│ → D1 database: skills-api-db                        │
│   ID: 135e8d4b-56db-4b48-94e6-0e018dd7cd42         │
│ → Account ID: 13529a61662c0aaebf9bf91c9fc0537e      │
└─────────────────────────────────────────────────────┘
```

## Worker Code

**Location:** `/home/ubuntu/skills-api-worker/skills-api/src/index.ts`
**Framework:** Hono
**Deploy:** `npx wrangler deploy` (requires `CLOUDFLARE_API_TOKEN`)

### Sync Endpoints (added 2026-08-10)

- `POST /sync/cves` — Bulk CVE insert (JSON array, batch_size param)
- `POST /sync/skills` — Bulk skill insert/replace (JSON array)

Both require `X-API-Key: hermes-logs-2026` header.

## Sync Script

**Location:** `/home/ubuntu/.hermes/skills-api/sync_to_api.py`

```bash
python3 ~/.hermes/skills-api/sync_to_api.py
```

Flow:
1. Checks remote stats at `GET /stats`
2. Pulls new CVEs (since last sync date) from local `skills-hub.db`
3. POSTs them to `/sync/cves` in batches of 50
4. Optionally syncs skills if local count > remote

## Auth: Global API Key (NOT API Token)

**PITFALL — `CLOUDFLARE_API_TOKEN` vs `CLOUDFLARE_API_KEY`:** This account uses a **Global API Key**, not an API Token. Using `CLOUDFLARE_API_TOKEN` with a Global API Key will fail with `Authentication failed (status: 400) [code: 9106]`. The correct env vars are `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL` for wrangler, and `X-Auth-Email` + `X-Auth-Key` headers for HTTP API calls.

- **Cloudflare Email:** `andrimuhammad330@gmail.com` (GitHub email)
- **Account ID:** `13529a61662c0aaebf9bf91c9fc0537e`
- **Database ID:** `135e8d4b-56db-4b48-94e6-0e018dd7cd42`

### Wrangler Deploy (correct)
```bash
cd /home/ubuntu/skills-api-worker/skills-api
CLOUDFLARE_API_KEY="<global-key>" CLOUDFLARE_EMAIL="andrimuhammad330@gmail.com" npx wrangler deploy
```

### D1 HTTP API (direct — bypasses worker)
```python
import urllib.request, json, ssl

CF_KEY = "<global-key>"
CF_EMAIL = "andrimuhammad330@gmail.com"
ACCOUNT_ID = "13529a61662c0aaebf9bf91c9fc0537e"
DB_ID = "135e8d4b-56db-4b48-94e6-0e018dd7cd42"

def d1_query(sql, params=None):
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DB_ID}/query"
    body = {"sql": sql}
    if params: body["params"] = params
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method="POST",
        headers={"Content-Type": "application/json", "X-Auth-Email": CF_EMAIL, "X-Auth-Key": CF_KEY})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        return json.loads(resp.read())
```

## D1 Batch Insert Limits

**PITFALL — "too many SQL variables" (error 7500):** D1 has a limit of ~50 SQL variables per query. When doing multi-row INSERTs with 9 columns, a batch of 50 rows (9 × 50 = 450 params) WILL fail. Use batch size of 5-10 for multi-row INSERTs, or insert one-by-one.

**Recommended fallback:** When batch INSERT fails, retry with individual INSERT statements. The `sync_to_api.py` script uses the worker's `/sync/cves` endpoint which handles batching internally. For direct D1 API access, use one-by-one inserts.

## Deploy Updated Worker

## Full Update Pipeline

```bash
# 1. Pull latest CVEs from NVD → local DB
python3 ~/.hermes/skills-api/update_cves.py

# 2. Enrich with Exploit-DB
curl -skL "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv" -o /tmp/exploitdb.csv
python3 ~/.hermes/skills-api/enrich_exploitdb.py

# 3. Deploy updated worker (if endpoints changed)
cd /home/ubuntu/skills-api-worker/skills-api
CLOUDFLARE_API_TOKEN="<token>" npx wrangler deploy

# 4. Sync to public API
python3 ~/.hermes/skills-api/sync_to_api.py
```

## Verification

```bash
# Check public API stats
curl -sk "https://skills-api.anzanesia.uk/stats" | python3 -m json.tool

# Check local stats
python3 -c "
import sqlite3
c = sqlite3.connect('$HOME/.hermes/skills-hub.db').cursor()
c.execute('SELECT COUNT(*), MAX(date_published) FROM cves')
print(f'CVEs: {c.fetchone()[0]:,} | Latest: {c.fetchone()[1]}')
"
```