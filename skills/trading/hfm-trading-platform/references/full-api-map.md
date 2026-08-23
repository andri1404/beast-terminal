# HFM Full API Service Map

Discovered Aug 2026 via JS bundle `89067-112fa225fdaded66.js` from the WebTrader Next.js app.

## Complete Service Registry (26 APIs)

All base URLs stored in HashiCorp Vault at `_shared/live/apis` with mount point `hfprojectskv`. Resolved at Next.js build time.

```
ACCOUNT-HF-API              → vault("ACCOUNT-HF-API_BASE_URL")
AFFILIATES-INT-HF-API       → vault("AFFILIATES-INT-HF-API_BASE_URL")
AUTHENTICATION-HF-API       → vault("AUTHENTICATION-HF-API_BASE_URL")
APP-HF-API                  → vault("APP-HF-API_BASE_URL")
ASSISTANT-HF-API            → vault("ASSISTANT-HF-API_BASE_URL")
BIG-REPORTS-HF-API          → vault("BIG-REPORTS-HF-API_BASE_URL")
SEMINAR-QR-HF-API           → vault("SEMINAR-QR-HF-API_BASE_URL")
COPY-HF-API                 → vault("COPY-HF-API_BASE_URL")
CMS-HF-API                  → vault("CMS-HF-API_BASE_URL")
ELASTIC-HF-API              → vault("ELASTIC-HF-API_BASE_URL")
MAILER-HF-API               → vault("MAILER-HF-API_BASE_URL")
MANAGER-HF-API              → vault("MANAGER-HF-API_BASE_URL")
MONGO-INTERNAL-HF-API       → vault("MONGO-INTERNAL-HF-API_BASE_URL")
ONBOARDING-HF-API           → vault("ONBOARDING-HF-API_BASE_URL")
PAMM-HF-API                 → vault("PAMM-HF-API_BASE_URL")
PAYMENTS-HF-API             → vault("PAYMENTS-HF-API_BASE_URL")
PAYMENTS-INT-HF-API         → vault("PAYMENTS-INT-HF-API_BASE_URL")
PAYMENTS-EXT-HF-API         → vault("PAYMENTS-EXT-HF-API_BASE_URL")
PSP-HF-API                  → vault("PSP-HF-API_BASE_URL")
REGISTRATION-HF-API         → vault("REGISTRATION-HF-API_BASE_URL")
VAULT-HF-API                → vault("VAULT-HF-API_BASE_URL")
WALLET-HF-API               → vault("WALLET-HF-API_BASE_URL")
PLATFORM-REST-API           → https://platforms-rest-api-live.hfmarkets.com
PLATFORM-DEMO-REST-API      → https://platforms-rest-api-demo.hfmarkets.com
WEBS-API                    → vault("WEBS-API_BASE_URL")
```

## Platform REST API Internal Details

- Server: Apache/2.4.41 (Ubuntu) at `10.10.101.200:80`
- `/swagger`: 404 (no Swagger UI exposed)
- `/docs`: 200 (internal, blocked through proxy)
- `/api` and `/api/v1`: accessible through proxy
- Auth: HTTP Basic Auth with vault credentials

## Sniffing Session Notes (Aug 2026)

### What Worked
- `curl_cffi` + `impersonate="chrome"` + DataImpulse proxy → got WebTrader HTML (279KB)
- JS chunk extraction and grep → found 26 API configs in `89067-*.js`
- Probing `/api/trader/*` with session cookies → 401 responses (endpoints confirmed real)
- `hfm_dashboard.py` with hardcoded cookies → account data still works

### What Failed
- Direct requests (no proxy) → 403 Cloudflare WAF
- Browserbase managed browser → stuck on Cloudflare JS challenge
- Steel scraper → HTTP 403
- `platforms-rest-api-*.hfmarkets.com` direct → connection timeout
- 10-retry proxy rotation → 70% Internet Positif, 30% Cloudflare, 0% clean API access to `/quotes` or `/symbols`

### Key Insight
The `/api/trader/quotes` and `/api/trader/symbols` endpoints return **401 not 404** — they are real, active endpoints that just need valid auth. The barrier is getting fresh session cookies past the Cloudflare + Internet Positif double-block.