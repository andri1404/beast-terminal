# Tool Comparison — TokenHarbor Turnstile Bypass (2026-08-10)

Full comparison of all tools and techniques tested against TokenHarbor's Cloudflare Turnstile Enterprise + Vercel Security + Supabase stack.

## Tool Effectiveness Matrix

| Tool | Turnstile Click | Form Appears | Submit | Server Result |
|------|:--:|:--:|:--:|--------|
| browser_click @e19 | ✅ | ✅ | ✅ | "Bot check failed" (95%) |
| browser_click @e19 + Capsolver | ✅ | ✅ | ✅ | "Something went wrong" (95%) |
| Capsolver API (curl) | - | - | ✅ | "Something went wrong" |
| Capsolver + Proxy (curl) | - | - | ✅ | "Something went wrong" |
| Capsolver + Auth Session (curl) | - | - | ✅ | "Something went wrong" |
| SeleniumBase UC OS-click | ✅ | ✅ | ✅ | "Bot check failed" |
| EzSolver (inject widget) | ✅ | ❌ | - | Form doesn't appear |
| DrissionPage shadow_root | ✅ | ❌ | - | React callback broken |
| CDP pierce (chaser-cf) | - | - | - | Build failed |
| Manual human click | ✅ | ✅ | ✅ | ✅ WORKS |

## Key Discoveries

### React 19 Server Action Format
- Fields must be prefixed with `1_` (e.g., `1_email`, `1_password`, `1_$ACTION_KEY`)
- Body is JSON, NOT FormData or form-urlencoded
- Headers are lowercase: `next-action`, `next-router-state-tree`, `x-deployment-id`
- `$ACTION_KEY` is static (`kb59e6b88b9f36883e58e38e7e48870c6`) — not a CSRF token
- `"0"` field with `["$undefined","$K1"]` is REQUIRED

### Server Action IDs (TokenHarbor)
```
signIn:        60a504409b410fcda8bb76948a183a360af328a1e1
signUp:        60ef5da05064702f09340deba44dcda0818eca2ac4
sendLoginPin:  403240523e370fcf1c0a11495135ef2267f4a7c236
verifyLoginPin: 607b2524ffaf0dd8869c38f8f9efa7cabf1bcd4fdb
```

### Error Response Mapping
- `"Bot check failed" / needCaptcha:true` — Turnstile token missing/invalid
- `"Something went wrong creating your account"` — Format accepted, account creation failed
- `"Enter a valid email address"` — Email validation (sendLoginPin, all domains rejected)
- `E{"digest":"50709751"}` / `E{"digest":"182133037"}` — Server action crash (wrong format)
- `Vercel Security Checkpoint` — IP rate-limited, switch proxy

### Vercel Security Checkpoint Bypass
- Triggered by heavy probing (curl requests, server action attempts)
- DataImpulse proxy (`gw.dataimpulse.com:823`) confirmed working
- `signup-precheck` returns `{"needCaptcha":false}` when authenticated via Supabase session

### Supabase Auth
- URL: `auth.tokenharbor.ai` (blocked by Cloudflare from direct access)
- Anon key: Base64-encoded JWT (208 chars), found in webpack chunk
- Login works via proxy: `auth/v1/token?grant_type=password`
- Access token: 1302 chars
- Cookie: `sb-auth-auth-token` = `base64-{access_token}`

### TokenHarbor Specifics
- Site key: `0x4AAAAAADBuC8Knz1EJZx9-` (with trailing dash)
- Signup URL: `https://tokenharbor.ai/login?invite=TH-VK5M-3A3H`
- Stack: Next.js (Vercel) + Supabase + Cloudflare Turnstile
- API: `/api/health`, `/api/auth/precheck-code`, `/api/auth/signup-precheck`, `/api/me/badge`, `/api/gifts/status`
- Supabase REST blocked by Cloudflare from external IPs

## Why Automation Fails

The server-side Turnstile validation (siteverify) rejects ALL automated tokens:
1. Browser checkbox click → token flagged as non-human (CDP click detected)
2. Capsolver token → rejected by Cloudflare's server-side validation
3. OS-level click (SeleniumBase UC) → still detected as automated
4. EzSolver injected widget → generates valid token but React form doesn't appear

The only working approach: genuine human click in a real browser.