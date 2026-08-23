---
name: hfm-professional-trading
description: Use when running HFM XAUUSD pro signals, backtests, or bot.
tags: [hfm, trading, gold, xauusd, professional, confluence, ml, backtest, telegram]
---

# HFM Professional Trading System

Complete professional trading pipeline for XAUUSD on HFM broker. Covers 7-factor confluence scoring, Random Forest ML filtering, CUSUM regime detection, walk-forward validation, Claude AI integration, and Telegram bot command center.

## Architecture

```
HFM gRPC Feed (wt-proxy.mtp-hfm.com)
  → 7-Factor Confluence Engine (hfm_pro_signal.py)
    → Random Forest ML Filter (hfm_ml_filter.py)
      → CUSUM Regime Gate (hfm_advanced.py)
        → Claude opus-5 AI Reasoning
          → Telegram Bot (/pro, /confluence, /trade, etc.)
```

## 7-Factor Confluence Scoring

**Minimum 5 to trade, 6+ = ⭐ A+ setup.** Based on institutional SMC/ICT research.

| # | Factor | Score Condition |
|---|--------|----------------|
| 1 | TREND | D1+H4+H1+M15 all aligned (EMA20>EMA50) |
| 2 | STRUCTURE | Price at EMA, Fibonacci, or S/R zone (not mid-air) |
| 3 | MOMENTUM | MACD + RSI confirm direction |
| 4 | LIQUIDITY | Recent sweep of session high/low (stop hunt) |
| 5 | PATTERN | Candle confirmation (hammer, engulfing, rejection) |
| 6 | VOLATILITY | ADX ≥ 25 confirming trend strength |
| 7 | PULLBACK | Price at discount (long) / premium (short) |

**GATE CHECKS** (must pass, not scored):
- HTF BIAS: D1+H4 agree. Counter-trend = NEVER.
- SESSION: London/NY/Overlap only. Asian/Evening = AUTO WAIT.
- NEWS: No red-flag (FOMC/NFP/CPI) within 30 min.

## R:R Optimization

RR 3:1 is optimal (EV +0.44R, PF 1.69). Backtest: 2000 M15 HFM candles, walk-forward.

| RR | WR | PF | EV | Deployed |
|----|-----|------|------|----------|
| 2.0:1 | 44% | 1.57 | +0.32R | — |
| 2.5:1 | 40% | 1.67 | +0.40R | — |
| **3.0:1** | **36%** | **1.69** | **+0.44R** | ✅ |
| 4.0:1 | 18% | 0.88 | -0.10R | ❌ |

## ML Filter (Random Forest)

- Script: `~/trading/hfm_ml_filter.py` (commands: `train`, `predict`)
- Model: 100 trees, 20 features, 66% CV accuracy
- Top features: RSI M5, RSI M15, ATR, EMA cross, trend M15
- Training: 50 trades at confl 5+, grows with each backtest
- Model: `/tmp/hfm_ml_filter.pkl`
- Features: `/tmp/hfm_ml_features.json`

## CUSUM Regime Detection

- Script: `~/trading/hfm_advanced.py`
- Regimes: TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE
- Trade gate: only trending regimes (30-bar warmup)
- Size multiplier: 1.0x trending, 0.5x ranging, 0.25x volatile
- Walk-Forward Validation: 18 windows, 50 OOS trades

## Key Scripts

| Script | Purpose |
|--------|---------|
| `~/.hermes/scripts/hfm_pro_signal.py` | MAIN: 7-factor confluence + Claude AI |
| `~/trading/hfm_ml_filter.py` | Random Forest ML signal filter |
| `~/trading/hfm_advanced.py` | CUSUM regime + Walk-Forward Validation |
| `~/trading/backtest_pro.py` | R:R optimization backtester |
| `~/trading/hfm_telegram_bot.py` | Full Telegram bot (15 commands) |
| `~/trading/hfm_cron_push.py` | Dashboard feed push (1m cron) |

## Telegram Bot Commands

| Command | Function |
|---------|----------|
| `/pro` | Professional AI signal (7-factor + Claude) |
| `/confluence` | Live 7-factor scoring |
| `/checklist` | 10-step pre-trade checklist |
| `/benchmark` | GitHub system comparison |
| `/price` | Live XAUUSD bid/ask |
| `/candles TF` | OHLC candles (M1/M5/M15) |
| `/account` | Demo + live balances |
| `/positions` | Open positions |
| `/signal` | Quick AI signal |
| `/trade BUY\|SELL` | Execute trade (0.01 lot) |
| `/close` | Close position |
| `/auth` | Login status |
| `/login email pass` | Trigger OTP |
| `/otp 123456` | Validate OTP |
| `/status` | Bot connection |
| `/dashboard` | Web dashboard link |

## Claude AI Prompt Pattern

The system prompt includes backtest validation data so Claude knows the statistical edge:
- Confluence 4: 176 trades, 42% WR, PF 1.11 (NOT tradeable)
- Confluence 5: 42 trades, 52.4% WR, PF 1.61 (SNIPER MODE)
- RR 3:1 optimal: EV +0.44R, PF 1.69

Claude is instructed to use SMC/ICT framework, 5-bar output format, Bahasa Indonesia.

## GitHub Benchmark

Our system ranks #9 of 12 GitHub XAUUSD systems. Full benchmark with 12 systems, methodology notes, and key insights in `references/benchmark.md`.

## Professional Trading Framework

Complete SMC/ICT entry framework, session timing, risk management rules, and gold-specific gotchas in `references/professional-framework.md`.

## Pitfalls

- **Token-type split**: `pricing.Pricing` uses `Bearer <walletSession>`. `trading.Trading` uses `Bearer <accountToken>`. Wrong token → grpc 16.
- **Cron Python**: gateway's `sys.executable` = `/usr/local/lib/hermes-agent/venv/bin/python`. Must have `curl_cffi` installed there.
- **Empty-TF guard**: DataImpulse proxy can return empty TF → `min()/max()` crash. Guard: `if len(m5)<30 or len(m15)<30: return`.
- **MACD signal-line**: Must be `EMA9(MACD line)`, NOT `EMA9(close)`. Verify histogram is ~±2, not thousands.
- **Market closed detection**: Weekend = MARKET CLOSED label. Tick stream timeout is normal.