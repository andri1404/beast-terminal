---
name: hfm-api-reference
description: Use when working with HFM APIs or platform REST feeds.
tags: [hfm, trading, api, gold, xauusd, platform, broker, mt5, webtrader]
---

# HFM (HF Markets) API Reference

Internal API architecture reference for HFM's trading platform. Discovered via JS bundle analysis of the Next.js WebTrader at `my.hfm.com`.

## Architecture Overview

HFM uses a Next.js frontend (`my.hfm.com`) that proxies to internal microservices behind Cloudflare. All backend API base URLs are stored in HashiCorp Vault (`hfprojectskv`) and resolved at build time — not directly accessible from outside.

## Platform REST API (MT5 Gateway)

The core trading API that connects to MT5 servers:

```
Demo: https://platforms-rest-api-demo.hfmarkets.com  (internal IP: 10.10.101.200, Apache/2.4.41)
Live: https://platforms-rest-api-live.hfmarkets.com
```

- Both behind Cloudflare
- Auth: basic auth (`PLATFORM-REST-API_AUTHENTICATION_USER` / `_PASSWORD` in Vault)
- Demo variant has separate credentials (`PLATFORM-DEMO-REST-API`)
- Accessible ONLY via DataImpulse proxy + curl_cffi (when egress IP not blocked by Internet Positif)

## Portal API Endpoints (my.hfm.com)

These require session cookies (`__cf_bm`, `login_session`, `masteraccount`, `walletHash`, `_masteraccount`, `login_prefix`) from a logged-in browser session:

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/trader/my-accounts` | GET | 200 | Account list + balances |
| `/api/trader/wallet-balance` | POST | 200 | Wallet balance |
| `/api/trader/symbols` | GET | 401 | **REAL** — needs auth |
| `/api/trader/quotes` | GET | 401 | **REAL** — needs auth |
| `/api/trader/market` | GET | 403 | WAF-blocked |
| `/api/trader/stream` | GET | 403 | WebSocket feed |
| `/api/trader/orders` | GET | 403 | Order management |
| `/api/trader/available-bonus` | GET | 200 | Bonus info |
| `/api/trader/currency-conv` | GET | 200 | Currency conversion |

## 26 API Services (from JS bundle `89067-112fa225fdaded66.js`)

Full list of HFM microservices, each with a `BASE_URL` in Vault:

`ACCOUNT-HF-API`, `AFFILIATES-INT-HF-API`, `AUTHENTICATION-HF-API`, `APP-HF-API`, `ASSISTANT-HF-AFFILIATES-API`, `ASSISTANT-HF-API`, `BIG-REPORTS-HF-API`, `SEMINAR-QR-HF-API`, `COPY-HF-API`, `CMS-HF-API`, `ELASTIC-HF-API`, `MAILER-HF-API`, `MANAGER-HF-API`, `MONGO-INTERNAL-HF-API`, `ONBOARDING-HF-API`, `PAMM-HF-API`, `PAYMENTS-HF-API`, `PAYMENTS-INT-HF-API`, `PAYMENTS-EXT-HF-API`, `PSP-HF-API`, `REGISTRATION-HF-API`, `VAULT-HF-API`, `WALLET-HF-API`, `PLATFORM-REST-API`, `PLATFORM-DEMO-REST-API`, `WEBS-API`

## Real-time quote feed (gRPC-Web) — REVERSE-ENGINEERED 2026-08

The live quote stream is NOT REST and NOT a plain WebSocket. Confirmed architecture:

- **`https://wt-proxy.mtp-hfm.com`** = the real-time feed host. An **Envoy proxy** fronting a **gRPC-Web** service. Every path returns `content-type: application/grpc` (len 0) — it's gRPC, not HTTP.
- The WebTrader page (`my.hfm.com/id/webtrader?wt=<token>`) RSC payload sets `envoyUrl: "https://wt-proxy.mtp-hfm.com"` and loads `static.hfm.com/assets/myhf/charting-library/charting_library.js` (TradingView lib) wrapped by a `WTProvider` component.
- The gRPC client lib (`RpcError`, `MethodDescriptor`, `getMethodDescriptor`) is bundled in Next.js chunk `25195-*.js`. The HFM-specific proto messages + service method paths are in a **dynamically-loaded datafeed** (not in static chunks) — full reversal still needs that datafeed JS + the gRPC metadata auth token.
- `static.hfm.com/assets/myhf/charting-library/charting_library.js` (55KB) is directly fetchable (no proxy, no CF); directory listing is 403.
- **Auth for the feed is the blocker** — not yet determined (likely signed from the `wt` token `base64(accountId:serverId).hexsig`, e.g. `MjM1MDUzODY5OjUwMw.4b8d9291a8a0d2e5` = account 235053869:server 503).
- Old `/api/trader/quotes` and `/api/trader/symbols` now return **404** (removed). Don't chase them.

### Path quirks
- `my.hfm.com/webtrader` (no `/id/`) → 301 to `internet-positif.info` (blocked). MUST use `/id/webtrader`.
- The WebTrader page RSC payload leaks authenticated account data: `wallet_id`, email, regulator, country (found `wallet_id 1245855`, `andrimuhammad330@gmail.com`, `HFSV`, `Indonesia`).
- Static `/_next/static/chunks/*.js` download via cr.id proxy is stochastic (Internet Positif); ~32/43 chunks retrievable, the `(auth)/webtrader/page` chunk is a 1167-byte loader stub (real logic is in shared chunks).

### Real HFM data WITHOUT reversing gRPC (the reliable path)
Run a bridge on the user's MT5 machine (Windows/Mac where HFM MT5 is logged in): `MetaTrader5.symbol_info_tick("XAUUSD")` gives real bid/ask/spread, then POST to the web UI. See `trading/hfm_bridge.py`. This avoids the gRPC reversal entirely and gives TRUE broker prices.

### gRPC-Web client WORKS (verified) + full auth chain
Full reversal done 2026-08. `hfm_grpc2.py` is the working client skeleton. Key facts:

- **Host:** `https://wt-proxy.mtp-hfm.com` (Envoy, behind Cloudflare SIN edge). All 6 services share this ONE envoyUrl.
- **Content-type:** `application/grpc-web+proto` over HTTP/1.1, `X-Grpc-Web: 1`, body = `\x00 + u32be(len) + protobuf`.
- **VERIFIED:** `config.Config/AppConfig` (unary, NO auth) returns 229KB — client framing is correct.
- **Service methods (complete):**
  - `pricing.Pricing`: `TicksStream` (server-streaming, req `SymbolsRequest` → resp `Tick`), `CandleStream`, `CandlesData`, `SymbolsData`, `SymbolSearch`. Also `TicksStream50`..`56` (per server-group).
  - `session.Session`: `AuthWallet`, `AuthAccount`, `AuthAccountPwd`, `AuthEmailPwd`, `RefreshAccountToken`, `AuthChallenge`, `AuthValidate`, `WalletData`, etc.
  - `trading.Trading`: `OpenTrade`, `CloseTrade`, `GetAccountData`, `GetOpenTrades`, `GetClosedTrades`, `ModifyTrade`, `CancelPendingOrder`, `PartialCloseTrade`, `CloseBy`, `GetConversionInfo`, `TradeHistory`.
  - `config.Config`, `event.Event/EventStream`, `price_alerts.PriceAlerts`.
- **Proto (fields):**
  - `SymbolsRequest{repeated string symbols=1, int32 serverId=2, string groupId=3}`
  - `Tick{string symbol=1, double ask=2, double bid=3, int32 digits=4, int64 ts=5, double open=6, high=7, low=8, int32 offset=9, bool maintenanceValue=10}`
  - `AuthAccountRequest{int64 account=1, string accountSecret=2, int32 serverId=3}` → `AuthAccountResponse{string accountAuth=1, string token=2, int32 refreshIn=3}`
  - `AuthWalletRequest{int32 walletId=1, string walletPassword=2, string walletAuth=3, string regulation=4, string executionVenue=5, string email=6}`
- **Metadata (account mode):** `device-id:web`, `authentication:"Bearer <accountAuth>"`, `account:"<acctId>"`, `is-testing:"false"`. Wallet mode uses `authentication:"Bearer <walletToken>"` + `wallet:"<walletId>"`.
- **Auth chain:** portal `/api/webterminal/init?account=<acct>&wallet=<wallet>` (or `/init-latest`) → returns `accountToken`+`walletToken`+`initAutologin`. Then `AuthAccount` (walletToken in metadata + MT5 accountSecret) → `accountAuth` → pricing stream. `accountAuth` is encrypted to cookie `wt_<acct>_<serverId>` via `/api/webterminal/cookie/encrypt`.

### ⚠️ Auth resolution (2026-08, VERIFIED AuthEmailPwd + 2FA discovered)
`/api/webterminal/init` returns the JWT **redacted** (`eyJhbG...MB8s`) — full token never exposed via portal API. But the gRPC auth is fully mapped now:

- **`AuthEmailPwd`** (req `AuthEmailRequest{email=1,password=2}`, resp `AuthWalletResponse`) = the real email+password login. **REQUIRES `device-id:web` metadata** (else grpc-status 7 `No device ID present`). VERIFIED: returns grpc-status 0 + wallet data (`walletId` field 5) + `wallet2faStatus` field 9.
- Account has **EMAIL 2FA**: `wallet2faStatus={authType:2,resendCounter:60,otpDigits:6}`; enum `TwoFactorAuthType{NONE:0,GOOGLE_AUTH:1,EMAIL:2}`. `AuthWallet` called with password returns `WALLET_AUTH_NOT_FOUND` (its field-3 `walletAuth` is an existing token, NOT password).
- Remaining chain (VERIFIED through 2FA): `SendEmail2faOtp` (req `AuthWalletRequest{walletId,walletPassword,email}`) → 6-digit OTP to email → `Validate2faOtp` (req `AuthWalletRequest`, **OTP in `walletPassword` field 2**, + `walletId` field 1 + `email` field 6) → `AuthWalletResponse`. **The Bearer token is `walletSession` (field 2, a JWT `eyJhbG...`), NOT `walletAuth` (field 1, which is a UUID `ff7b949f-...`).** Sending the UUID as `Bearer` to `AuthAccount` → grpc-status 2 "Internal server error". Then — NOT yet achieved (blocked on the account password, see ⚠️ LAST BLOCKER below) — `AuthAccount` (metadata `authentication:Bearer <walletSession>` + `wallet:<id>`) → `accountAuth` (field 1) → `TicksStream` (metadata `Bearer <accountAuth>` + `account:<id>`).
- **gRPC-Web response-parsing pitfall:** over HTTP/1.1 (curl_cffi) the real `grpc-status` is NOT an HTTP header — it lives in the **trailers frame** (last body frame, flag `0x80`, payload `grpc-status:N\r\ngrpc-message:...\r\n`). Checking only headers makes every call look like `grpc-status "?"`. Parse the body into 5-byte-prefixed frames: data frame flag `0x00`, trailers flag `0x80`.
- **OTP expires fast** (~60s, `resendCounter:60`). Each `SendEmail2faOtp` mints a fresh OTP and invalidates the prior one, but old emails linger in the inbox — the user MUST read the LATEST email. Hold the session open with the stdin-wait pattern (`hfm_wait.py`) so the OTP is validated the instant it's typed, instead of the slow trigger→reply→re-trigger loop.
- Scripts: `trading/hfm_otp.py` (AuthEmailPwd + trigger OTP), `trading/hfm_final.py <otp>` (validate→account→stream), `trading/hfm_wait.py` (stdin-wait full chain), `trading/hfm_grpc3.py`, `trading/hfm_acct.py`, `trading/hfm_refresh.py`, `trading/hfm_sid.py`. MT5 bridge (`hfm_bridge.py`) stays the no-2FA fallback.

### ✅ RESOLVED — the "blocker" was a method-name bug, NOT the password. `@Haha123` IS the correct demo MT5 password; the failing call was `AuthAccount` when the WebTrader actually uses `AuthAccountPwd` (see ✅ SOLVED below). The bullets below are the pre-resolution debug log — ignore their "stale password / get the correct password" wording, it was wrong.
2FA → `walletSession` (field 2 JWT, ~201 chars) is **VERIFIED working** — but the account-level step was NOT completed. Session ended here:

- `AuthAccount` / `AuthAccountPwd` (identical req `AuthAccountRequest{account=1 int64, accountSecret=2, serverId=3}` → resp `AuthAccountResponse{accountAuth=1, token=2, refreshIn=3}`) return **grpc-status 7 "Account credentials not found"** for BOTH `@Haha123` (STALE memory guess) and `@Andri14` (portal pwd), on serverId 503 AND 50. `accountSecret` = the MT5 **master** password (`ta_account_pwd` field from the login form).
- `AuthAccount` WITHOUT `accountSecret` → same "Account credentials not found". `RefreshAccountToken{account,serverId}` with `Bearer <walletSession>` → grpc-status 16 "Authentication column-value missing" (wants an existing `accountToken`, not the wallet token).
- Account identity is CONFIRMED correct via `/api/trader/my-accounts` (exposes `server_id`): demo `#235053869`=server **503** (HFMarketsGlobal-Demo 4), live `#198473092`=65 (Live16), `#223012371`=67 (Live18).
- `walletSession` field 2 IS the full JWT; `eyJhbG...HAHk` in prints/JSON is just `[:30]+"..."` DISPLAY truncation, NOT server redaction. (Only the portal REST `/api/webterminal/init` redacts its tokens; the gRPC `Validate2faOtp` response is full.)
- **To finish:** get the correct MT5 demo master password from the user (or have them reset it in the MyHF portal), then `AuthAccount` → `accountAuth` → `TicksStream`. Until then the MT5 bridge (`hfm_bridge.py`) is the no-password path — do NOT re-guess the password.

### ✅ SOLVED — full working feed (2026-08-14, tested end-to-end)
The gRPC-Web feed is FULLY cracked. Working scripts in `/home/ubuntu/trading/`:
`hfm_final.py` (full chain), `hfm_candles2.py` (candles), `hfm_live.py` (tick stream), `hfm_stream2.py` (symbols).

**Complete auth chain (order matters):**
1. `AuthEmailPwd` — req `AuthEmailRequest{email=1, password=2}`, md `{device-id:web, device-type:web}`. Returns `AuthWalletResponse` with `wallet2faStatus` (field 9) = `{authType:2(EMAIL), resendCounter:60, otpDigits:6}` → 2FA REQUIRED.
2. `SendEmail2faOtp` — req `AuthWalletRequest{walletId=1, walletPassword=2(the portal pwd), email=6}` → sends 6-digit OTP to email. **OTP expires ~60s.**
3. `Validate2faOtp` — req `AuthWalletRequest{walletId=1, walletPassword=2(the OTP!), email=6}` → `AuthWalletResponse`: field 1 = `walletAuth` (UUID), field 2 = `walletSession` (JWT ~201 chars, HS256, sub=walletId, exp 1h), field 3 = refreshIn(5).
4. `AuthAccountPwd` (NOT AuthAccount!) — req `AuthAccountRequest{account=1(int64), accountSecret=2(the MT5 acct pwd), serverId=3}`, md `authentication: Bearer <walletSession JWT>`, `wallet:<walletId>` → `AuthAccountResponse`: field 1 = `accountAuth`(UUID), field 2 = `accountToken`(JWT ~204 chars, sub=accountId, exp 10min), field 3 = refreshIn(5).

**Correct pricing metadata (this is what was missing):**
```python
md = {"device-id":"web", "device-type":"web", "wallet":str(walletId),
      "authentication":"Bearer <walletSession JWT>",  # WALLET token, not account token
      "account":str(accountId)}
```

**Working pricing methods (all on wt-proxy.mtp-hfm.com):**
- `SymbolsData` — req `SymbolsRequest{symbols=1, serverId=2}` → symbol info (trading hours, units, digits). VERIFIED 770 bytes.
- `CandlesData` — req `CandleRequest{symbol=1, type=2("M5"/"M15"/"H1"...), serverId=3}` → 2000 `Candle` bars. VERIFIED 94KB.
- `TicksStream50` (and 51..60 for other server groups; demo server 503 → group 50) — server-streaming `Tick` frames, first frame is `{1:"__ACK__"}`. Use `stream=True` + `iter_content()`; ticks arrive on price change (sparse in Asian session).

**Candle proto:** `{int64 ts=1, string symbol=2, double open=3, double low=4, double high=5, double close=6, string type=7, int64 volume=8}`.
**Tick proto:** `{string symbol=1, double ask=2, double bid=3, int32 digits=4, int64 ts=5, double open=6, high=7, low=8, int32 offset=9, bool maintenanceValue=10}`.

**Account facts (verified):** wallet 1245855, email andrimuhammad330@gmail.com, demo acct 235053869 server_id 503 (HFMarketsGlobal-Demo 4) MT5 pwd `@Haha123`, portal pwd `@Andri14`. Live #198473092 (server 65), #223012371 (server 67). Real HFM XAUUSD ≈ $4325 (Aug 2026) vs PAXG proxy ~$4360 — **proxy diverges $35+**, real feed matters.

**24/7 auto-refresh (no 2FA after setup):** `walletAuth` (field 1 UUID, long-lived) → `AuthWallet{walletId, walletAuth:UUID}` → fresh `walletSession` (1h). VERIFIED. So the daemon/cron only needs the UUID + MT5 pwd, never the 2FA OTP again. Deployed: cron job `HFM XAUUSD Real Feed Push` (every min) → `~/.hermes/scripts/hfm_cron_push.sh` → `/usr/bin/python3 ~/trading/hfm_cron_push.py` (cron's default python lacks curl_cffi, wrapper uses /usr/bin/python3). Dashboard `/api/push_quote` shows `src:"HFM"`.

**Pitfalls hit:** (1) must add `device-type:web` + `wallet:<id>` to pricing md. (2) pricing `authentication` uses WALLET token, not account token. (3) `AuthAccount` ≠ `AuthAccountPwd` — the WebTrader uses `AuthAccountPwd`. (4) OTP is in `walletPassword` field. (5) TicksStream (no suffix) returns "Method not implemented"; use TicksStream50-60. (6) candle `type` must be "M5"/"M15"/"H1" (not "5"/"5m").

## Trading (auto-trade) gRPC — reversed 2026-08-14

`trading.Trading` service = full order management. Method map (all UNARY, metadata uses `accountToken` — NOT walletSession):

| Method(s) | Request | Response |
|---|---|---|
| OpenTrade, CloseTrade, ModifyTrade, PartialCloseTrade, CloseBy, PendingOrder, ModifyPendingOrder, CancelPendingOrder | `PositionRequest` | `PositionResponse` |
| GetAccountData | `AccountRequest` | `AccountData` |
| GetOpenTrades | `TradesRequest` | `TradesResponse` |
| GetClosedTrades | `ClosedTradesRequest` | `ClosedTradesResponse` |
| TradeHistory | `TradeHistoryRequest` | `Trade` |

**`PositionRequest`** (OpenTrade): positionId=1(int64), account=2(int32), accountCurrency=3(str), quantityType=4(int32), volume=5(double), margin=6, units=7, symbol=8(str), type=9(int32), price=10(double, 0=market), comment=11(str), priceSl=12(double), priceTp=13(double), serverId=14(int32), digits=15(int32).
**`PositionResponse`**: login=1, status=2, statusMessage=3, data=4(Trade), margin=5, freeMargin=9, equity=10, balance=11, floating=12.

**Enums:** `TradeType{BUY:0, SELL:1, BUY_LIMIT:2, SELL_LIMIT:3, BUY_STOP:4, SELL_STOP:5}`; `QuantityType{LOTS:0, MARGIN:1, UNITS:2}`.

**CRITICAL metadata split:** `pricing.Pricing` service (CandlesData, TicksStream, SymbolsData) uses `Bearer <walletSession>`. ALL `trading.Trading` service methods — both read AND write (OpenTrade, CloseTrade, GetAccountData, GetOpenTrades, GetClosedTrades, ModifyTrade, etc.) — use `Bearer <accountToken>` (from `AuthAccountPwd`). Both include `device-id/device-type/wallet/account`. Wrong token → grpc 16 "Authentication column-value missing" or "Invalid Token" or grpc 12 "Method not implemented".

**GetAccountData** verified: `AccountRequest{account=1, serverId=2}` → `AccountData{account=1, serverId=2, leverage=4, balance=5, equity=6, margin=7, freeMargin=8, marginLevel=9, currency=10}`.

**OpenTrade verified WORKING** (demo #235053869): `PositionRequest{account, volume=0.01, symbol, type=0(BUY), priceSl, priceTp, serverId=503, digits=2}` → grpc-status 0, opened a real demo position with SL/TP auto-set.

**Scripts:** `~/trading/autotrade_test.py` (one-shot open+verify), `~/trading/autotrade_bot.py` (DRY default / `LIVE` arg → demo; runs `smart_signal.py` then OpenTrade when BUY/SELL, max 1 position + 3 trades/day, SL=1.2*ATR min $3, TP=2x SL, 0.01 lot).

## Backtest (walk-forward, no lookahead) — honest result 2026-08-14

`~/trading/backtest_hfm.py` runs the smart-signal strategy over REAL HFM candles (2000 M15 + H1/H4/D1), walk-forward with no lookahead (context = candles up to bar i). **Result: simple M15 "enter on multi-TF alignment" = 29% win rate = LOSES** (RR 2:1 break-even is 33%). A pullback filter (buy only below M15 EMA20 in uptrend) did NOT help (25%). Lesson: naive alignment-entry chases price; profitable entry needs pullback-to-level + candle confirmation, or H1 (not M15). `~/trading/smart_signal.py` is the current engine (structure + multi-TF + session + risk); its decision gate correctly returns WAIT when D1/H4 vs H1/M15 diverge or session is illiquid.

## WebTrader Token Format

```
wt=M base64(accountId:serverId) . hex_signature
Example: MjM1MDUzODY5OjUwMw.4b8d9291a8a0d2e5 → 235053869:503
```

The token alone is NOT sufficient for API auth — it only grants WebTrader page access. Real API calls need session cookies.

## Working Access Pattern

```python
import curl_cffi.requests as r

PROXY = "http://5b018d7f65ec63f85a79__cr.id:586b7351aee59a63@gw.dataimpulse.com:823"
COOKIES = { ... }  # from logged-in browser session

s = r.Session(impersonate="chrome", cookies=COOKIES, proxy=PROXY, timeout=30, verify=False)
resp = s.get("https://my.hfm.com/api/trader/my-accounts")
```

## Pitfalls

- **DataImpulse proxy → Internet Positif**: Indonesian egress IPs get blocked by gov firewall. Rotate connections (up to 7x, 2-3s backoff). Some requests succeed, some don't — it's stochastic.
- **Cloudflare double barrier**: Both `my.hfm.com` and `platforms-rest-api-*.hfmarkets.com` sit behind CF. curl_cffi `impersonate=chrome` + proxy is the only working combo.
- **Session cookies expire**: Cookies from `hfm_dashboard.py` may go stale. When endpoints return 401/403, cookies need refresh from a live browser session.
- **Platform API internal**: `platforms-rest-api-demo.hfmarkets.com` times out on direct connection — only accessible via DataImpulse proxy (when not blocked).

## References

- `references/api-architecture.md` — full JS bundle extraction results with all Vault references and API service map
- `references/grpc-webtrader-reversal.md` — continuation notes for the gRPC-Web quote feed reversal (chunk map, module IDs, download technique, remaining gaps)
- `references/grpc-web-client.md` — REUSABLE gRPC-Web client helpers (protobuf framing, varint, trailers parsing, decode) + the JS-bundle reverse-engineering recipe. Verified working.
- `references/telegram-bot.md` — Telegram bot command center: all HFM gRPC endpoints exposed via bot commands.
- `references/professional-trading-framework.md` — 7-factor confluence scoring, gatekeeper system, SMC/ICT entry framework, session timing, risk management, Claude AI prompt pattern. Deployed in `hfm_pro_signal.py` + bot `/pro` command.

## Professional Trading System (2026-08)

The `hfm_pro_signal.py` engine replaces `hfm_ai_signal.py` with a 7-factor institutional confluence scoring system. See `references/professional-trading-framework.md`. Telegram bot exposes: `/pro` (AI + 7-factor), `/confluence` (live scoring), `/checklist` (11-step pre-trade), `/login`/`/otp` (2FA auth), `/price`/`/candles`/`/account`/`/positions` (real-time data), `/trade`/`/close` (execution).

**Token-type split (CRITICAL):** `pricing.Pricing` uses `Bearer <walletSession>`. `trading.Trading` uses `Bearer <accountToken>`. Wrong token → grpc-status 16.

## References

- `references/api-architecture.md` — full JS bundle extraction results with all Vault references and API service map
- `references/grpc-webtrader-reversal.md` — continuation notes for the gRPC-Web quote feed reversal (chunk map, module IDs, download technique, remaining gaps)
- `references/grpc-web-client.md` — REUSABLE gRPC-Web client helpers (protobuf framing, varint, trailers parsing, decode) + the JS-bundle reverse-engineering recipe. Verified working.
- `references/telegram-bot.md` — Telegram bot command center (`~/trading/hfm_telegram_bot.py`): all HFM gRPC endpoints exposed via bot commands with token-type split documentation.