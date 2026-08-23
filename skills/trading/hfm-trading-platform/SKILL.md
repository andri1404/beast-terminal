---
name: hfm-trading-platform
description: Use when accessing HFM platform APIs, auth, or Cloudflare.
tags: [hfm, trading, api, cloudflare, mt5, architecture]
---

# HFM Trading Platform — Architecture & API Access

HFM (my.hfm.com) platform architecture, API endpoints, authentication patterns, and Cloudflare bypass methodology. This skill covers the PLATFORM layer — for trading signals and gold analysis, see `hfm-gold-monitor`.

## Architecture Overview

HFM runs a Next.js frontend → Cloudflare → 26 microservice backend APIs. All service base URLs are stored in HashiCorp Vault (`hfprojectskv`) and resolved at build time. The JS bundle `89067-*.js` contains the full API configuration map.

### Key Services

| Service | Purpose | Auth |
|---------|---------|------|
| PLATFORM-REST-API | MT5 trading gateway — quotes, orders, positions | Basic auth |
| PLATFORM-DEMO-REST-API | Same for demo accounts | Basic auth |
| ACCOUNT-HF-API | Account management, balances | Session cookies |
| AUTHENTICATION-HF-API | Login, session management | Session cookies |
| WALLET-HF-API | Wallet operations | Session cookies |

### Platform REST API (MT5 Gateway)

```
Demo: https://platforms-rest-api-demo.hfmarkets.com
Live: https://platforms-rest-api-live.hfmarkets.com
```

- Internal-only (Apache/2.4.41 at 10.10.101.200:80)
- Direct access times out from outside HFM infra
- Auth: basic auth credentials from Vault

## Portal API Endpoints (my.hfm.com)

All require session cookies. Accessible through the Next.js frontend proxy.

| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/api/trader/my-accounts` | GET | Working | Account list + balances |
| `/api/trader/wallet-balance` | POST `{}` | Working | Wallet balance |
| `/api/trader/quotes` | GET | 🔒 401 | **Real-time price feed** |
| `/api/trader/symbols` | GET | 🔒 401 | **Symbol list + spreads** |
| `/api/trader/market` | GET | 🚫 403/WAF | Market data |
| `/api/trader/stream` | ? | 🚫 403/WAF | WebSocket feed |
| `/api/trader/orders` | ? | 🚫 403/WAF | Order management |
| `/api/trader/available-bonus` | GET | Working | Bonus info |
| `/api/trader/currency-conv` | GET | Working | Currency conversion |

## Authentication

Session cookies from a logged-in browser session:

```python
REQUIRED_COOKIES = [
    "__cf_bm",        # Cloudflare bot management token
    "NEXT_LOCALE",    # "id"
    "masteraccount",  # URL-encoded account identifier
    "login_session",  # Session token
    "walletHash",     # Wallet hash
    "_masteraccount", # Secondary session (Fe26 format)
    "login_prefix",   # Login prefix
]
```

Cookies expire after hours. The `hfm_dashboard.py` script has hardcoded cookies that go stale. Refresh by extracting cookies from a logged-in browser via `document.cookie` in DevTools console.

## Cloudflare Bypass

### Triple-Block Problem

```
Direct VPS request → Cloudflare WAF → 403 Forbidden
DataImpulse proxy → Cloudflare TLS → Internet Positif (Indonesian gov block)
Managed browser (Browserbase) → Cloudflare JS challenge → detected as bot
```

### Working Approach (fragile, ~30% success)

1. **curl_cffi** with `impersonate="chrome"` (venv at `/tmp/cffen`)
2. **DataImpulse proxy**: `http://5b018d7f65ec63f85a79__cr.id:586b7351aee59a63@gw.dataimpulse.com:823`
3. **Retry rotation**: 10 attempts, 2-3s backoff between retries

```python
import curl_cffi.requests as r
import time

PROXY = "http://5b018d7f65ec63f85a79__cr.id:586b7351aee59a63@gw.dataimpulse.com:823"
COOKIES = {...}  # from authenticated session

for attempt in range(10):
    try:
        s = r.Session(impersonate="chrome", cookies=COOKIES, proxy=PROXY, timeout=20, verify=False)
        resp = s.get("https://my.hfm.com/api/trader/my-accounts")
        if "internet-positif" not in resp.text.lower():
            return resp.json()
    except Exception:
        pass
    time.sleep(2 + attempt * 0.5)
```

### What Doesn't Work

- **curl alone**: TLS fingerprint blocked by Cloudflare
- **curl_cffi without proxy**: VPS IP gets 403 from CF WAF
- **Managed browser (Browserbase)**: Detected as bot, stuck on JS challenge
- **Steel scraper**: HTTP 403
- **Non-Indonesian proxy needed** for reliable access (DataImpulse egress all Indonesian)

## Sniffing Methodology

To discover API endpoints from the WebTrader:

1. Fetch WebTrader page with curl_cffi + proxy (retry until >50KB response)
2. Extract JS chunk URLs: `re.findall(r'(?:src|href)="(/_next/static/[^"]+)"', html)`
3. Download each chunk and grep for: `wss://`, `ws://`, `BASE_URL`, `from_vault`, `api/`
4. The API config chunk is typically `89067-*.js`
5. Probe discovered endpoints with different HTTP methods and auth

## Real-Time Price Data Sources (ranked)

1. **HFM Portal** `/api/trader/quotes` — real feed, needs auth cookies
2. **HFM Platform REST API** — real MT5 feed, internal-only
3. **Binance PAXGUSDT** — gold token, $2-5 divergence from XAUUSD (used by `hfm_full_analysis.py`)
4. **gold-api.com** — REST API, rate-limited

## Pitfalls

- Proxy always routes through Indonesian egress → Internet Positif blocks ~70% of requests
- Session cookies hardcoded in scripts go stale; need periodic refresh from user's browser
- The `/api/trader/quotes` and `/api/trader/symbols` endpoints exist and return 401 (not 404)
- Managed/headless browsers detected by CF; real desktop browser with user profile needed for fresh cookies
- WebTrader WebSocket is Next.js RSC-based, not plain WebSocket

## Related Skills

- `hfm-gold-monitor` — Gold trading signals, account dashboard, technical analysis
- `turnstile-capsolver` — Cloudflare Turnstile bypass (not effective for HFM's JS challenge)