# HFM Telegram Bot

Location: `~/trading/hfm_telegram_bot.py` (22KB)

Full command-center Telegram bot for HFM trading via gRPC-Web. All endpoints use the same auth chain and gRPC helpers as the existing scripts.

## Commands

| Command | Handler | gRPC Service | Token Type |
|---------|---------|-------------|------------|
| `/start` | Welcome + menu | — | — |
| `/price` | Live XAUUSD bid/ask/spread | `pricing.Pricing/CandlesData` (M1) | walletSession |
| `/candles M5` | OHLC table (M1/M5/M15) | `pricing.Pricing/CandlesData` | walletSession |
| `/account` | Balance, equity, margin | `trading.Trading/GetAccountData` | **accountToken** |
| `/positions` | Open positions (SL/TP) | `trading.Trading/GetOpenTrades` | **accountToken** |
| `/signal` | Latest AI Claude signal | reads `/tmp/hfm_ai_result.json` | — |
| `/trade BUY` | Execute 0.01 lot XAUUSD | `trading.Trading/OpenTrade` | **accountToken** |
| `/close` | Close position | `trading.Trading/CloseTrade` | **accountToken** |
| `/status` | Connection + uptime | — | — |
| `/dashboard` | Web dashboard link | — | — |

## Token Type Split (critical)

- **Pricing** (read): `walletSession` JWT — used for CandlesData, TicksStream, SymbolsData
- **Trading** (read+write): `accountToken` JWT — used for GetAccountData, GetOpenTrades, OpenTrade, CloseTrade, etc.

Using walletSession on trading endpoints → `grpc-status 16 Invalid Token`.

## Setup

```bash
# Get token from @BotFather
export HFM_BOT_TOKEN="123456:ABCdef..."

# Run (needs curl_cffi + python-telegram-bot)
/usr/bin/python3 ~/trading/hfm_telegram_bot.py
```

## Test Results (2026-08-15)

All core functions verified working:
- ✅ Price: XAUUSD $4,376.43 (real HFM gRPC)
- ✅ Candles: M5 OHLC table, 10 candles
- ✅ Account: Demo #235053869 $121,452.33, leverage 1:1000
- ✅ Signal: AI Claude opus-5, WAIT, confluence 2/5
- ✅ Positions: Clean, no open trades
- ✅ Status: gRPC connected via DataImpulse proxy