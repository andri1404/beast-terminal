# TokenHarbor — Post-Auth Top-up / Billing / Admin Recon (2026-08-10)

Post-login audit of the billing, top-up, referral, and admin surface. Complements the
account-creation notes elsewhere in this skill. Goal class: payment-bypass + privilege-escalation
recon on an AI gateway (Stripe/PayPal credits model).

## Login (note: NO Turnstile on login)

- `/login` (no invite param) is the SIGN-IN page — form has email + password, **no Turnstile**.
  Only the signup page (`/login?invite=...`) renders the Cloudflare checkbox.
- Login is a React server action / session cookie flow. On success you land on `/dashboard`.
- Session is held in cookies: `th_sid`, `sb-auth-auth-token.0` (base64-JWT Supabase session),
  `th_did` (device id), plus `th_cookie_consent`. The `sb-auth-auth-token.0` value is
  `base64-<base64url of JSON>`; the console masks long credential-looking strings, so reading
  it back for offline decode is unreliable — decode in-browser or don't exfil.
- A normal account's Supabase JWT `role` is `authenticated`; no admin claim present.

## Welcome gift claim (validated)

- `POST /api/welcome/claim` (empty JSON body) → `{"ok":true,"rewardUsd":5,"newTrialBalance":5}`.
  Credits +$5.00 to balance.
- **Anti-replay solid:** second call returns `409 {"error":{"code":"nothing_pending","message":
  "No welcome grant is waiting for you right now."}}`. Cannot re-claim.
- This contradicts the earlier recon note that gifts are "not claimable" — the welcome credit
  IS claimable via this endpoint (the gift box button on the dashboard / `POST /api/welcome/claim`).

## Top-up / payment endpoints (extracted from JS bundle `12ncd8d2epnde.js`)

```javascript
POST /api/stripe/create-checkout   body: {package_id, coupon_code?}
POST /api/paypal/create-order      body: {package_id, coupon_code?}
POST /api/paypal/capture-order     body: {order_id, package_id, coupon_code?}
```

- Stripe returns `{"url":"https://checkout.stripe.com/c/pay/cs_live_..."}` → browser redirects to
  Stripe hosted checkout. Amount shown on Stripe = package price, locked server-side.
- `package_id` is validated against a server-side catalog. `starter` is valid; `community`,
  `harbor`, `STARTER`, and arbitrary ids return `400 {"error":{"code":"bad_request",
  "message":"Unknown package."}}`.
- **Rate limit:** rapid repeated `create-checkout` calls (package_id or coupon_code brute)
  trigger `429 {"error":{"code":"rate_limited","message":"Too many top-up ..."}}`. Cooldown is
  long (minutes). Do NOT brute coupon codes here — you'll lock the account/IP.

## Defense analysis (why top-up bypass failed)

| Attack | Result |
|--------|--------|
| Amount tamper in Stripe URL | Blocked — package price is server-set; Stripe hosted checkout is authoritative |
| package_id injection (`pro`,`free`,`0`,`admin`) | `400 Unknown package` — server fetches price from DB by id |
| coupon_code brute (21 common codes) | `429 rate_limited` before any coupon validation runs |
| Welcome claim replay | `409 nothing_pending` — idempotent/replay-guarded |
| `/api/me`, `/api/credits`, `/api/orders` etc. GET | `403 AccessDenied` (CloudFront XML) — hidden/not present; don't guess API routes |

Conclusion: the paid-credit enrichment path is well-guarded. The only soft surface is the
**referral program** (below) and the fact that **coupon_code is accepted as a field** (a leaked/
guessable promo code could discount a top-up — but brute is rate-limited).

## Referral program

- Route: sidebar "Invite friends" → `/dashboard/invites`.
- Reward: **$2 per referred friend** once the friend has been signed up for 24h AND has actually
  used Token Harbor.
- Invite link format: `https://tokenharbor.ai/login?invite=TH-FDAW-5C6Y` (reusable; a new code is
  minted per account — the `TH-XXXX-XXXX` pattern).
- Self-referral is the natural abuse (create accounts, refer yourself) but is gated by the same
  server-side signup block as normal registration.

## Admin surface

- `/admin` appears in the client route-guard list (`c=["/admin","/login","/auth","/oauth",
  "/unlock"]`) but returns `404` for a normal user (Next.js not-found, not a redirect) — the
  admin panel is not reachable as a non-admin and the route is client-side gated.
- Probing `/admin`, `/admin/dashboard`, `/admin/users`, `/internal`, `/staff`, etc. all return
  404 (CloudFront default deny). Supabase admin REST endpoints (`/admin/users`, `/admin/generate_link`)
  exist in the JS SDK bundle but require the service_role key — not obtainable from the client.

## Operational notes

- `fetch('/api/...')` from the browser console 403s for speculative routes (CloudFront default
  deny). Only real endpoints (e.g. `/api/welcome/claim`, `/api/chat/unread-count`) resolve 200.
  Extract real endpoints from the JS chunks instead of guessing.
- To find API routes server-side, fetch each `/dashboard/*` page's script chunks via the page
  origin (`fetch(scriptSrc, {credentials:'include'})`) and grep for `"/api/..."` string literals.
  The billing chunk `12ncd8d2epnde.js` is where the payment endpoints live.
- Console masks long credential-looking strings (the Supabase session cookie) on read-back; store
  it in a window global and decode in-browser, or don't exfil at all.