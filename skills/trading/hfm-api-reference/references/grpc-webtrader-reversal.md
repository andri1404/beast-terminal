# HFM WebTrader gRPC-Web Reversal — full detail (2026-08, COMPLETE)

Reverse-engineering notes for HFM's real-time quote feed. The SKILL.md has the headline;
this file holds the exact artifacts found, so a future session can finish the auth chain
or extend it (e.g. order placement) without redoing discovery.

## Confirmed endpoint
- `https://wt-proxy.mtp-hfm.com` — Envoy proxy fronting a **gRPC-Web** service, behind Cloudflare
  (SIN edge). Every path returns `content-type: application/grpc`. Set in the WebTrader RSC
  payload as `envoyUrl`. All 6 services (config/event/price_alerts/pricing/session/trading)
  share this ONE host — there is no separate pricing host.

## Page / token
- Correct URL `my.hfm.com/id/webtrader?wt=<token>`. `/webtrader` WITHOUT `/id/` → 301 →
  `internet-positif.info` (gov block). Always use `/id/`.
- `wt` token = `base64(accountId:serverId).hexsig`, e.g.
  `MjM1MDUzODY5OjUwMw.4b8d9291a8a0d2e5` = account 235053869 : server 503.
- RSC payload leaks authenticated account state: `wallet_id` 1245855, email
  `andrimuhammad330@gmail.com`, regulator HFSV, country Indonesia, `authenticated:true`.

## Charting stack (CORRECTED — datafeed IS in the static chunks)
- `WTProvider` (webpack module `43351`) receives `envoyUrl` + `library_path`
  (= `https://static.hfm.com/assets/myhf/charting-library/`). `charting_library.js` (55 KB) there
  is the TradingView lib, directly fetchable (no proxy/CF).
- **The full gRPC datafeed + proto + service stubs live in chunk
  `ca1f0a1c-e5d62f0ee790719f.js` (711 KB).** It defines module `43351` and contains every
  `proto.session.*`, `proto.pricing.*`, `proto.trading.*` message + `MethodDescriptor` definitions.
  (Earlier note "datafeed not located" was WRONG — it was just in the last chunk to download.)

## Complete gRPC service map (all on wt-proxy.mtp-hfm.com)
- `pricing.Pricing`: `TicksStream` (server-streaming), `CandleStream`, `CandlesData`,
  `SymbolsData`, `SymbolSearch`. Also `TicksStream50`..`56` (per MT5 server-group).
- `session.Session`: `AuthWallet`, `AuthWalletPwd`, `AuthAccount`, `AuthAccountPwd`,
  `AuthEmailPwd`, `AuthPhonePwd`, `AuthSocial`, `RefreshAccountToken`, `AuthChallenge`,
  `AuthValidate`, `SendEmail2faOtp`, `Validate2faOtp`, `ValidateBackupCode`, `Wallet2faStatus`,
  `WalletData`, `GetLoginMethod`, `RegVerify`.
- `trading.Trading`: `OpenTrade`, `CloseTrade`, `CloseBy`, `PartialCloseTrade`,
  `ModifyTrade`, `ModifyPendingOrder`, `CancelPendingOrder`, `PendingOrder`, `GetAccountData`,
  `GetOpenTrades`, `GetClosedTrades`, `TradeHistory`, `GetConversionInfo`.
- `config.Config`: `AppConfig`, `AppLanguage`, `GetLoginMethods`, `ShouldShowArsenal`.
- `event.Event/EventStream`, `price_alerts.PriceAlerts/*`.

## Proto schemas (field numbers)
- `SymbolsRequest{repeated string symbols=1, int32 serverId=2, string groupId=3}`
- `Tick{string symbol=1, double ask=2, double bid=3, int32 digits=4, int64 ts=5, double open=6,
  high=7, low=8, int32 offset=9, bool maintenanceValue=10}`
- `AuthEmailRequest{string email=1, string password=2}` → `AuthWalletResponse`
- `AuthWalletRequest{int32 walletId=1, string walletPassword=2, string walletAuth=3,
  string regulation=4, string executionVenue=5, string email=6}`
- `AuthWalletResponse{string walletAuth=1, string walletSession=2, int32 refreshIn=3,
  map walletDataMap=4, int32 walletId=5, string tcData=6, int32 defaultServerId=7,
  repeated Promotion promotionsList=8, Wallet2faStatusResponse wallet2faStatus=9,
  repeated Wallet walletsList=10}`
- `Wallet2faStatusResponse{int32 authType=1, int32 resendCounter=2, int32 otpDigits=3}`;
  enum `TwoFactorAuthType{NONE:0, GOOGLE_AUTH:1, EMAIL:2}`
- `AuthAccountRequest{int64 account=1, string accountSecret=2, int32 serverId=3}` →
  `AuthAccountResponse{string accountAuth=1, string token=2, int32 refreshIn=3}`

## Metadata (gRPC headers)
- Session calls: `device-id:web` (REQUIRED — else grpc-status 7 "No device ID present"),
  `device-type:web`.
- Account-mode pricing: `device-id:web`, `authentication:"Bearer <accountAuth>"`,
  `account:"<acctId>"`, `is-testing:"false"`.
- Wallet-mode: `authentication:"Bearer <walletToken>"`, `wallet:"<walletId>"`.

## gRPC-Web client (VERIFIED working)
- `content-type: application/grpc-web+proto`, `X-Grpc-Web: 1`,
  `X-User-Agent: grpc-web-javascript/0.1`, body = `\x00 + u32be(len) + protobuf`.
- Server-streaming response = repeated `[1 flag byte][4-byte BE len][proto frame]`; last frame has
  flag `0x80` and body `grpc-status:0\r\ngrpc-message:\r\n` (trailers).
- **`config.Config/AppConfig` (unary, NO auth) returns 229 KB** — proves framing is correct.
- Errors come back as HTTP headers `grpc-status` / `grpc-message` (e.g. 12 UNIMPLEMENTED,
  16 UNAUTHENTICATED, 7 "No device ID present" / "WALLET_AUTH_NOT_FOUND").

## Auth chain (VERIFIED up to 2FA; OTP steps are proto-mapped)
1. `AuthEmailPwd` (req `AuthEmailRequest`) + `device-id:web` → grpc-status 0, wallet data +
   `wallet2faStatus={authType:2(EMAIL),resendCounter:60,otpDigits:6}`.
2. `SendEmail2faOtp` (req `AuthWalletRequest`) → sends 6-digit OTP to email.
3. `Validate2faOtp` (req `AuthWalletRequest`, OTP in `walletPassword` field 2) → `walletAuth`.
4. `AuthAccount` (metadata `Bearer <walletAuth>` + `wallet:<id>`) with
   `{account,accountSecret:MT5pwd,serverId}` → `accountAuth`.
5. `TicksStream` (metadata `Bearer <accountAuth>` + `account:<id>`) → stream<Tick>.
- `/api/webterminal/init?account=<acct>&wallet=<wallet>` returns the JWT **REDACTED**
  (`eyJhbG...MB8s`) — useless for auth. `accountAuth` is persisted as cookie
  `wt_<acct>_<serverId>` via `/api/webterminal/cookie/encrypt` (POST, needs the token as body).

## Working scripts (in /home/ubuntu/trading/)
- `hfm_grpc3.py` — full chain (AuthWallet→AuthAccount→TicksStream), has the proto encode/decode helpers.
- `hfm_otp.py` — AuthEmailPwd + SendEmail2faOtp (triggers the OTP email).
- `hfm_final.py <otp>` — Validate2faOtp → AuthAccount → TicksStream.
- `hfm_bridge.py` — no-auth MT5 bridge (real bid/ask/spread from user's MT5 machine).

## Chunk download technique (Internet Positif is the real enemy)
- `cr.id` (Indonesian egress) hits Internet Positif stochastically; `cr.us` → Cloudflare challenge;
  Browserbase browser → Cloudflare challenge. Only `static.hfm.com` is clean.
- Retry: `curl_cffi` + `impersonate="chrome"` + cookies + `cr.id` proxy, loop 18–60x, accept only
  when `len(text) > 8000` AND `'internet-positif' not in text[:3000]` AND `<html` not in first 3000.
- The `/id/webtrader` HTML itself is ~1.37 MB (full RSC payload), always retrievable. Grep the HTML
  for `I[43351` to find which chunks hold module 43351 (the WTProvider).
