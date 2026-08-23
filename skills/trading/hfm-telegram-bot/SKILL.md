---
name: hfm-telegram-bot
description: Use when building or deploying the HFM Telegram trading bot.
tags: [hfm, trading, telegram, bot, xauusd, gold, grpc, realtime]
---

# HFM Telegram Trading Bot

Full real-time HFM trading command center via Telegram. Self-contained auth (login + OTP), live pricing, account management, trade execution, AI signals.

## Script

`~/trading/hfm_telegram_bot.py` (~23KB). Single-file bot using `python-telegram-bot` + `curl_cffi` + raw gRPC-Web protobuf.

## Commands

### Auth (self-contained, no manual scripts)
- `/login email password` — AuthEmailPwd → trigger OTP email
- `/otp 123456` — Validate2faOtp → simpan walletAuth + walletSession ke `/tmp/hfm_state.json`
- `/auth` — Cek status login

### Signals & Analysis
- `/signal` — AI Claude opus-5 signal from `/tmp/hfm_ai_result.json`
- `/supertrend` — Supertrend Pro signal (ATR buffer-zone, 3-level TP, VWAP, Fib, HA)
- `/scalp` — Fast scalping engine (M1-M5-H1, rule-based)
- `/pro` — Full PRO analysis (7-factor confluence + AI)
- `/confluence` — Live 7-factor scoring
- `/checklist` — Pre-trade checklist

### Trading
- `/price` — Live XAUUSD bid/ask/spread (HFM gRPC CandlesData M1)
- `/candles M5` — OHLC table (M1/M5/M15)
- `/account` — Demo balance/equity/margin + live account summary
- `/positions` — Open positions
- `/trade BUY|SELL` — Execute 0.01 lot, auto SL/TP dari signal (fallback: ±$3 SL / ±$4.5 TP)
- `/close [ID]` — Close position

### System
- `/status` — Bot uptime + gRPC connection status
- `/dashboard` — Web dashboard URL

## Market Closed Detection

`is_market_open()` checks:
- Saturday/Sunday → closed
- Friday after 07:00 WIB → closed
- Monday before 00:00 WIB → closed

When closed: shows `🔴 MARKET CLOSED` + "Last Close" label. Tick stream gracefully handled (falls back to last candle data).

## Deployment

```bash
# Start detached
export HFM_BOT_TOKEN="your_token"
/usr/bin/python3 ~/trading/hfm_telegram_bot.py &

# Restart
pkill -f hfm_telegram_bot
sleep 2
HFM_BOT_TOKEN="token" /usr/bin/python3 ~/trading/hfm_telegram_bot.py &

# Health check
pgrep -f hfm_telegram_bot
tail -f /tmp/hfm_bot.log
```

From `execute_code` (detached from parent):
```python
proc = subprocess.Popen(
    ["/usr/bin/python3", "/home/ubuntu/trading/hfm_telegram_bot.py"],
    env={"HFM_BOT_TOKEN": token, **os.environ},
    start_new_session=True,  # survives parent exit
    stdout=open("/tmp/hfm_bot.log", "w"),
    stderr=subprocess.STDOUT
)
```

## Dependencies

- `python-telegram-bot` — `pip install --break-system-packages python-telegram-bot`
- `curl_cffi` — already installed in `/usr/bin/python3`
- Run with `/usr/bin/python3` (NOT deep-eye venv, NOT gateway python)

## Token Metadata Split (CRITICAL)

gRPC endpoints use different auth tokens:

| Category | Token | Source | Endpoints |
|----------|-------|--------|-----------|
| **Pricing/Read** | `walletSession` JWT | `AuthWallet` refresh | CandlesData, TicksStream, SymbolsData |
| **Trading/Write** | `accountToken` JWT | `AuthAccountPwd` | GetAccountData, GetOpenTrades, OpenTrade, CloseTrade |

**Pitfall:** Using `walletSession` for `GetAccountData` → grpc-status 16 "Invalid Token". Must use `accountToken` from `AuthAccountPwd` for all trading endpoints.

Functions:
- `get_wallet_md()` — returns pricing metadata (Bearer walletSession)
- `get_account_md()` — returns trading metadata (Bearer accountToken)

## Auth Flow (via bot)

1. User sends `/login email password`
2. Bot calls `AuthEmailPwd` → detects 2FA type (EMAIL=2)
3. Bot calls `SendEmail2faOtp` → stores pending state in `_pending_otp` dict (60s TTL)
4. Bot replies: "📧 OTP dikirim ke email! Balas: `/otp 123456`"
5. User sends `/otp 123456`
6. Bot calls `Validate2faOtp` → saves `walletAuth` + `walletSession` to `/tmp/hfm_state.json`
7. Bot replies: "✅ Login sukses!"

Token auto-refresh: `refresh_wallet_session()` re-authenticates with `walletAuth` UUID when `walletSession` expires (no 2FA needed after initial setup).

## Bot Lifecycle

- Token persists across restarts via `/tmp/hfm_state.json`
- `walletSession` auto-refreshed when < 600s to expiry
- `_pending_otp` is in-memory only — lost on restart
- Logs: `/tmp/hfm_bot.log`

## Pitfalls

- **AccountToken vs WalletSession**: Using wrong token for trading endpoints → "Invalid Token". Always use `get_account_md()` for trading.
- **Weekend**: Tick stream times out (no data). Bot gracefully falls back to last candle data + shows MARKET CLOSED.
- **Proxy flakiness**: DataImpulse sometimes returns empty candles. Retry logic in `get_candles()`.
- **OTP expiry**: 60 second window. User must respond fast. Re-trigger with new `/login` if expired.
- **Python path**: Must use `/usr/bin/python3` — gateway python and deep-eye venv may lack `curl_cffi` or `python-telegram-bot`.