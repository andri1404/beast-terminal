# HFM gRPC-web real-time feed (from VPS, no MT5 terminal)

Proven 2026-08. Gets REAL HFM candles/ticks over plain HTTP POST, authenticated by a walletSession Bearer token.

## Endpoints (grpc-web over POST)
- Host: `https://wt-proxy.mtp-hfm.com`
- Proxy: DataImpulse (`gw.dataimpulse.com:823`, user:pass auth in URL). Some egress IPs hit Indonesian "Internet Positif" block → retry rotation (~7x, backoff). Always use `cr.us` egress for Indonesian targets.
- MUST use `curl_cffi` `impersonate="chrome"` (Cloudflare TLS fingerprint; plain urllib/requests fails).
- Headers: `Content-Type: application/grpc-web+proto`, `X-Grpc-Web: 1`, `Accept: application/grpc-web+proto`, `X-User-Agent: grpc-web-javascript/0.1`.
- Body framing: `\x00` + 4-byte big-endian length + protobuf message.

## Auth chain (3 steps)
1. `session.Session/AuthEmailPwd` — fields 1=email, 2=wallet password. Returns walletAuth UUID (field 1) + walletSession JWT (field 2) + country/wallet meta.
2. `session.Session/SendEmail2faOtp` — fields 1=walletId, 2=wallet pwd, 6=email. Returns `{1:2, 2:60, 3:6}` = sent / 60s TTL / 6-digit.
3. `session.Session/Validate2faOtp` — fields 1=walletId, 2=OTP, 6=email. Returns tokens. **grpc-status "7" = Invalid otp** — almost always because the OTP expired (60s TTL): re-trigger SendEmail2faOtp and ask the user for the FRESHEST code immediately.

## CRITICAL gotchas
- **Token dict keys are INTs, not strings.** After `decode(payload)`, access with `f.get(2)` / `f.get(1)` — NOT `f.get("2")`. The string-key lookup silently returns empty, giving `wallet_session len 0` and zero candles with no error. (After `json.dump` to disk the keys become strings — that's fine; only the in-memory dict is int-keyed.)
- **field 1 = walletAuth UUID** (used to refresh), **field 2 = walletSession JWT** (the Bearer token for data calls). Do not mix them up.
- Token refresh: `session.Session/AuthWallet` fields 1=walletId, 3=walletAuth → returns fresh walletSession (field 2). Trigger when `jwt_exp < 600s`.

## Data endpoints
- `pricing.Pricing/CandlesData` — fields 1=symbol, 2=timeframe ("M5"/"M15"), 3=serverId. Auth header `authentication: Bearer <walletSession>` + `wallet` + `account` headers. Returns ~2000 candles. **Intraday only (M1–M30)** — H1/H4/D1 are NOT served by this endpoint; fall back to Binance PAXGUSDT klines proxy for higher timeframes.
- `pricing.Pricing/TicksStream` — fields 1=symbol, 2=serverId. Stream of live tick frames.

## Candle protobuf field map
`t`=1 (varint, unix seconds), `vol`=8 (varint), `o`=3, `l`=4, `h`=5, `c`=6 (all fixed64/double, wire type 1).

## Account facts (user's own)
walletId=1245855, account=235053869 (demo, main practice), serverId=503, symbol=XAUUSD, email=andrimuhammad330@gmail.com, wallet pwd=@Andri14, 2FA=EMAIL.

## Working scripts
- `~/.hermes/scripts/hfm_cron_push.py` — push candles+quote to dashboard `/api/push_quote` (silent on success).
- `~/.hermes/scripts/hfm_ai_signal.py` — AI signal (Claude opus-5) from HFM feed + gold news.
- `~/.hermes/scripts/hfm_push_signal.py` — rule-based signal from HFM feed.
- `~/trading/hfm_final.py <otp>` — interactive full chain (Validate2faOtp → AuthAccount → TicksStream), useful for debugging.
