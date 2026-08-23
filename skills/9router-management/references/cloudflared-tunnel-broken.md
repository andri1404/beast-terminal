# Cloudflared Tunnel: 9Router Incompatibility Evidence

## Summary

Cloudflared quick tunnels connect and forward requests to 9Router's Next.js server, but **all requests return HTTP 404**. This is not a transient issue — it reproduces across multiple tunnel restarts, protocol settings, and URL variations.

## Environment

- 9Router: v0.5.50 (Next.js)
- Cloudflared: 2026.7.3
- 9Router listening: 0.0.0.0:20128
- Cloudflared forwarding: http://127.0.0.1:20128

## Reproduction

1. Start 9Router: `HOME=/home/ubuntu 9router --no-browser --skip-update`
2. Verify local: `curl http://localhost:20128/v1/models` → 200 OK, 15 models
3. Start cloudflared: `cloudflared tunnel --url http://127.0.0.1:20128 --no-autoupdate`
4. Tunnel created: `https://<random>.trycloudflare.com`
5. Test through tunnel: `curl https://<tunnel>/v1/models` → **HTTP/2 404, empty body**

## Metrics Evidence

Cloudflared metrics confirm requests ARE forwarded to origin:

```
cloudflared_tunnel_total_requests 7
cloudflared_tunnel_response_by_code{status_code="404"} 7
cloudflared_tunnel_request_errors 0
```

7 requests, 7 responses, 0 errors — but ALL are 404. The 404 is coming from 9Router's Next.js, not from cloudflared.

## Attempted Fixes (ALL FAILED)

| Attempt | Result |
|---|---|
| `--url http://localhost:20128` | 404 |
| `--url http://127.0.0.1:20128` | 404 |
| `--protocol http2` | 404 |
| `--protocol quic` (default) | 404 |
| Delete `~/.9router/tunnel/state.json` + restart | 404 |
| Clear tunnelUrl from DB + restart | 404 |
| Simulate CF headers locally (CF-Connecting-IP, X-Forwarded-For, etc.) | 200 OK (headers don't cause it) |
| Different Host header locally | 200 OK (Host header doesn't cause it) |

## Root Cause

Likely an HTTP/2 proxy incompatibility between cloudflared and Next.js. Cloudflared connects to the origin via HTTP/2, and Next.js's handling of certain HTTP/2 frames or headers may trigger a 404 response. The exact mechanism is unknown, but the pattern is consistent and reproducible.

## Working Alternative: Bore

`bore` (simple TCP tunnel) works perfectly:

```bash
bore local 20128 --to bore.pub
# → bore.pub:<port>

curl http://bore.pub:<port>/v1/models → 200 OK, 15 models
```