# TokenHarbor Recon Data

## Target Info
- **URL:** https://tokenharbor.ai
- **Tech stack:** Next.js 14+, React, Supabase, Vercel, Cloudflare
- **Auth:** Supabase Auth (custom domain: auth.tokenharbor.ai)
- **API style:** OpenAI-compatible + Anthropic-compatible

## Turnstile
- **Site key:** `0x4AAAAAADBuC8Knz1EJZx9-` (trailing dash is part of the key)
- **Type:** Managed (checkbox) — appears after multiple signups from same IP
- **Iframe src:** `challenges.cloudflare.com/turnstile/v0/api.js`
- **Checkbox ref:** `@e19` inside iframe `@e15` (may vary per session)

## Server Action (Signup)
- **Action ID:** `60ef5da05064702f09340deba44dcda0818eca2ac4`
- **Endpoint:** `POST /login?invite=TH-VK5M-3A3H`
- **Header:** `Next-Action: 60ef5da05064702f09340deba44dcda0818eca2ac4`
- **Form fields:** `$ACTION_REF_1`, `$ACTION_1:0`, `$ACTION_1:1`, `$ACTION_KEY`, `device_fingerprint`, `timezone`, `next`, `cf-turnstile-response`, `email`, `password`, `invite_code`
- **Response format:** RSC stream (`text/x-component`)
- **Error response:** `{"error":"Bot check failed. Please refresh and try again.","needCaptcha":true}`

## API Endpoints
| Endpoint | Method | Response |
|----------|--------|----------|
| `/api/auth/precheck-code` | POST | `{"valid":true}` |
| `/api/auth/signup-precheck` | GET | `{"needCaptcha":true}` |
| `/api/health` | GET | `{"ok":true,...}` |
| `/api/keys` | GET | 401 (needs auth) |
| `/api/gifts/status` | GET | `{"claimable":[]}` |
| `/api/me/send-verification-email` | POST | 405 |

## Supabase
- **URL:** `auth.tokenharbor.ai` (Cloudflare-blocked from direct access)
- **Anon key:** JWT token (208 chars), stored in webpack chunk `0.4.dgcznq8y1.js`
- **Decoded payload:** `{"iss":"supabase","ref":"isbnzmwjmtiuipesgmmg","role":"anon","iat":1776765536,"exp":2092341536}`
- **Signup endpoint:** `POST /auth/v1/signup` — returns `signup_ip_required` error
- **Signin endpoint:** `POST /auth/v1/token?grant_type=password` — works (200)

## Webpack Chunks
- Main chunk with Supabase config: `_next/static/chunks/0.4.dgcznq8y1.js`
- Turnstile component: `_next/static/chunks/0975o47lem106.js`
- Site key found in: `0975o47lem106.js` at `let n="0x4AAAAAADBuC8Knz1EJZx9-"`

## Dashboard
- API key format: `thk_live_<43 chars>`
- Balance: shows $5.00 after claiming gift
- Free models: `deepseek-v4-flash`, `mimo-v2.5`, `kimi-k3`
- API base URL: `https://tokenharbor.ai` (not api.tokenharbor.ai)