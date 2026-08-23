# Cloudflare gated authenticated API access (proxy + TLS impersonation)

The working combination to reach an API/portal behind aggressive Cloudflare from a
plain server where a browser "Just a moment" challenge and plain `curl` both fail.

## Stack
- **`curl_cffi`** with `impersonate="chrome"` — clones a real Chrome TLS/JA3 fingerprint. Plain curl is blocked on TLS fingerprint alone.
- **A residential/rotating proxy** (here DataImpulse `http://USER:PASS@gw.dataimpulse.com:823`) for a clean egress IP. Cloudflare challenges the datacenter IP.
- **The account holder's real session cookies** (including `__cf_bm`) from a successful browser login — replayed to reach AUTHENTICATED content (uses own account, authorized).

## Pattern (works, verified)
```python
from curl_cffi import requests as cr
PROXY="http://user:pass@gw.dataimpulse.com:823"
cookies={ "NEXT_LOCALE":"id", "my.session.cookie":"...", "__cf_bm":"...", ... }
s=cr.Session(impersonate="chrome", cookies=cookies, proxy=PROXY, timeout=30, verify=False)
r=s.get("https://host/protected/path")
```
- `verify=False` needed because the proxy MITMs the TLS (cert subject mismatch).
- Retry loop (7x, backoff) — the proxy rotates egress IPs and some are blocked.

## Pitfalls
- **Some proxy egress IPs are flagged by an upstream country filter** (here Indonesian "Internet Positif" gov-blocked ISPs) and return a block page (HTTP 200 with a `<title>Internet Positif</title>` doc). Detect by string, retry on another rotation.
- Only the login/session cookies are replayed — you do NOT need `cf_clearance` if the protected app accepts the session cookie on the impersonated-TLS + clean-IP request (works here). If it still challenges, you'd need `cf_clearance` (from solving the challenge in a real browser on the proxy IP).
- Cookies expire quickly; captures from the user's live session degrade within minutes-to-hours. Re-request fresh cookies when a 401/redirect appears.
- Do NOT put real credentials in the replay; use the holder's own session and only for accessing their authorized account data.
- Keep the curl_cffi venv python (`/tmp/cffen/bin/python`) as the interpreter.

## When to use vs plain curl
Use this only when `curl -skI` and even browser automation fail on Cloudflare. If the API host is NOT Cloudflare-gated a plain request is faster — check headers first (`server: cloudflare` / `cf-ray`).