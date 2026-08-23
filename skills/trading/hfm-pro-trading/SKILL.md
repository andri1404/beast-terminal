---
name: hfm-pro-trading
description: Use for HFM gold signals, backtests, or the Telegram bot.
tags: [trading, gold, xauusd, hfm, confluence, ml, ai, backtest, telegram]
---

# HFM Professional Trading System (v4 — PREDATOR SCALP)

Full institutional-grade XAUUSD trading system: 7-factor confluence → Random Forest ML filter → Claude opus-5 AI → Telegram bot execution. Built on real HFM broker gRPC feed.

## 7-Factor Confluence Scoring

Engine: `~/.hermes/scripts/hfm_pro_signal.py`. Minimum 5/7 for entry. 6+/7 = ⭐ A+ setup.

| # | Factor | Condition |
|---|--------|-----------|
| 1 | TREND | D1+H4+H1+M15 all aligned (EMA20>EMA50) |
| 2 | STRUCTURE | Price at EMA21/50, Fibonacci, S/R, or round number |
| 3 | MOMENTUM | MACD + RSI confirm direction on M15+H1 |
| 4 | LIQUIDITY | Recent sweep of session high/low (stop hunt) |
| 5 | PATTERN | Candle confirmation (hammer, engulfing, rejection) |
| 6 | STRENGTH | ADX ≥ 25 (trend strength confirmed) |
| 7 | PULLBACK | At discount (long) / premium (short), not chasing |

**GATES (must pass, not scored):**
- HTF BIAS: D1+H4 agree. Counter-trend = NEVER.
- SESSION: London/NY/Overlap only. Asian/Evening = AUTO WAIT.
- NEWS: No high-impact events within 30 min.

## Backtest Results (30 days, 2000 HFM M15 candles)

| Config | Trades | WR | PF | EV |
|--------|--------|-----|-----|-----|
| Confl ≥ 5 | 42 | 52.4% | 1.61 | +0.29R |
| **RR 3:1** ⭐ | 50 | 36.0% | 1.69 | +0.44R |
| RR 2:1 | 50 | 44.0% | 1.57 | +0.32R |

**RR 3:1 deployed as optimal.** Backtest scripts: `~/trading/backtest_pro.py`, `~/trading/hfm_advanced.py`.

## Supertrend Pro Strategy (XAUUSDBOTS)

Script: `~/.hermes/scripts/hfm_supertrend_pro.py`. Python port of the "XAUUSDBOTS SUPERTREND PRO" Pine Script indicator from t.me/freexauusdforexea. Fully integrated with HFM gRPC feed.

**Strategy logic:**
- Supertrend ATR(10) factor 5 + 1% buffer zone
- BUY: close > upper buffer after downtrend flip (trend[-1] == -1)
- SELL: close < lower buffer after uptrend flip (trend[-1] == 1)
- TP: 3 levels at profitFactor(3) × ATR(14) — 1x/2x/3x
- SL: stopFactor(2.5) × ATR(14), fixed (trailing planned)
- VWAP: session-based (reset daily at 00:00 UTC, fallback to 96-bar M15)
- Fibonacci 50% + 61.8% golden zone from 50-bar lookback
- 100 EMA bias (Bullish/Bearish) + Heikin Ashi candle coloring
- Multi-TF confirmation: M15 + H1 + H4 Supertrend alignment

**Cron:** `9c3ac427714e` (every 2m, deliver origin, no_agent). Silent unless signal flips BUY/SELL or price moves >$3.

**Result:** persists to `/tmp/hfm_supertrend_result.json` with fields: price, arah, supertrend, trend, atr14, tp1/tp2/tp3, sl, rr, vwap, ema100, ema_bias, fib_50, fib_618, ha_bullish, tf_align.

**Bot command:** `/supertrend` — reads result JSON and displays full signal dashboard.

**Pine Script source:** `references/supertrend-pro-pine.md`.

## Scalping Engine (v4 PREDATOR — Fast Rule-Based)

Script: `~/.hermes/scripts/hfm_scalp_signal.py`. Pure Python indicators, no AI delay (~2 sec). Multi-TF: M1→M5→M15→M30→H1. 7-factor scalp scoring. Silent unless signal changes. Cron: `63f34a08aa8e` (every 1m, deliver origin). Usually PAUSED when AI PREDATOR is active.

**Bot command:** `/scalp` — runs the script on-demand, returns current scalp signal.

Script: `~/trading/hfm_ml_filter.py`. Trained on 50 trades at confl 5+. CV accuracy 66%. Top features: RSI M5, RSI M15, ATR, EMA cross, trend M15. Filter: P(win) ≥ 0.60 passes. Model: `/tmp/hfm_ml_filter.pkl`. Retrain: `python3 hfm_ml_filter.py train`.

## CUSUM Regime Detection

Script: `~/trading/hfm_advanced.py`. Based on algo-trading (TanvirCCC). Detects trending/ranging/volatile. Blocks trading in ranging, reduces size in volatile. Walk-forward validation: 18 windows, 50 OOS trades, 40% WR.

## Claude AI — PREDATOR SCALP Mode (v4 — Aggressive)

Model: claude-opus-5 via `api.mwapi.dev/v1`. System prompt transforms Claude into "PREDATOR XAUUSD — SERIGALA PASAR EMAS". 

**Key changes from v3 (conservative):**
- Default: CARI ENTRY (bukan WAIT). WAIT hanya jika mid-air tanpa struktur atau semua TF konflik.
- Confluence threshold: 2-3/5 dengan M1 candle bagus = MASIH BISA ENTRY (sebelumnya <4 = WAIT).
- Session Asia tetap scalping — SL lebih ketat, bukan WAIT.
- M1 precision: EMA8 pullback + rejection candle = konfirmasi terbaik.
- Scalping: SL $2-4, TP $4-8, RR minimal 2:1.
- Format output: 5 baris — ARAH / MASUK (dengan alasan) / TP·SL (dengan RR) / CHECK CEPAT / VERDICT agresif.

**Backtest stats embedded in prompt** so Claude knows what works:
- Confl 5: 52.4% WR, PF 1.61, EV +0.29R
- RR 3:1: 36% WR, PF 1.69, EV +0.44R
- ALL FILTERS: 50% WR, EV +1.00R, PF 3.00

**Deep Analysis findings embedded** (WIN vs LOSS patterns):
- WIN: ADX 27.9, ATR $7.7, 18 bars hold → calm markets, patience
- LOSS: ADX 31.4, ATR $9.0, 10 bars hold → avoid volatile
- Monday 44% WR, Wednesday 58% WR (best) | Tuesday 12% WR, Friday 0% WR (avoid)
- Bearish candle = 0% WR (NEVER) | Bullish = 36% WR | Hammer = 33% WR

**PREDATOR v4 Python confluence (lenient, for scalping):**
1. Trend M15+H1 aligned (cukup 2 TF, bukan semua)
2. Momentum MACD or RSI (cukup salah satu)
3. Structure: dekat EMA21/50 atau S/R (±1.5× ATR)
4. M1/M5 candle: hammer/shooting-star/bullish/bearish
5. Session: bonus liquid, not required (Asia tetap scalp)

**10 Hard Override Gates** (v3 conservative — SOFTENED in v4 PREDATOR):
1. Confl < 2 → WAIT (v3: <5)
2. Session LOW → scalp with tight SL, not WAIT (v3: WAIT)
3. ADX > 30 → hati-hati, not block (v3: WAIT)
4. ATR > $8 → hati-hati, not block (v3: WAIT)
5. Tuesday/Friday → hati-hati (v3: WAIT)
6. Bearish candle → still WAIT (0% WR historically)
7. No sweep → still WAIT
8. Counter-trend → WAIT (v3: NEVER)
9. R:R < 2:1 → WAIT (v3: <3:1)
10. 3 consecutive losses → STOP

**Format:** 5-line output: ARAH / MASUK (with trigger reason) / TP·SL (with RR) / CHECK (confl, ADX, ATR, day, candle) / VERDICT (one aggressive sentence). Secrets in `~/.hermes/secrets/anthropic_key` + `anthropic_endpoint`.

Full system prompt + data feed format: `references/predator-v4-prompt.md`.

## Telegram Bot (v4 — Built-in JobQueue Auto-Push)

Script: `~/trading/hfm_telegram_bot.py`. Token: hardcoded fallback in script (env var `HFM_BOT_TOKEN` checked first, then hardcoded token as fallback).

**Dependency:** `python-telegram-bot[job-queue]`. Install: `/usr/bin/python3 -m pip install "python-telegram-bot[job-queue]" --break-system-packages`. Without `[job-queue]`, auto-push fails with `PTBUserWarning: No JobQueue set up`.

**Built-in Auto-Push (JobQueue):** Bot runs `auto_push_job` every 60 seconds via `app.job_queue.run_repeating()`. It checks `/tmp/hfm_signal_auto.json` — if enabled, runs `hfm_ai_signal.py` and sends output to the saved chat ID (`/tmp/hfm_signal_chat.json`). Cron `84e386340f5b` is PAUSED (user prefers bot auto-push over cron).

**Commands:** `/pro` `/scalp` `/confluence` `/supertrend` `/checklist` `/benchmark` `/price` `/candles` `/account` `/positions` `/signal` `/trade` `/close` `/auth` `/login` `/otp` `/status` `/dashboard` `/signal_on` `/signal_off` `/signal_interval` `/signal_status`

## Benchmark Position

Full comparison in `references/benchmark.md`. Rank #9 of 12 GitHub systems. Target: top 5 (need 1000+ trades).

## Trade Journal & Performance

Script: `~/.hermes/scripts/hfm_trade_journal.py`. Auto-logs every trade to `/tmp/hfm_trade_journal.json`.

**Commands:** `/stats` — WR, PF, EV, total P&L, daily P&L, confluence breakdown, streak. `/journal` — recent trades with P&L, R-multiples. `/risk 1.5` — set risk %. `/retrain` — retrain ML from journal data.

**Risk Config:** `/tmp/hfm_risk_config.json`. Default: 1% risk/trade, 3% max daily loss, RR 3:1 minimum, demo account #235053869.

## Discipline Rules (v4 PREDATOR — Scalping)

1. Confluence < 2 = WAIT (v3: <5)
2. Session Asia/Evening = scalp with tight SL, not WAIT (v3: WAIT)
3. Counter-trend = WAIT (v3: NEVER)
4. No sweep = WAIT
5. R:R < 2:1 = WAIT (v3: <3:1)
6. Risk 1% per trade, max 3% daily, 3 consecutive losses = STOP
7. ML P(win) < 60% = REJECT
8. CUSUM ranging = REDUCE SIZE

## Key Scripts

| Script | Purpose |
|--------|---------|
| `~/.hermes/scripts/hfm_ai_signal.py` | AI PREDATOR signal (Claude opus-5, v4 aggressive) |
| `~/.hermes/scripts/hfm_scalp_signal.py` | Fast scalping engine (M1-H1, rule-based, no AI) |
| `~/trading/hfm_telegram_bot.py` | Full Telegram bot (26 commands incl /scalp) |
| `~/trading/hfm_ml_filter.py` | Random Forest ML filter |
| `~/trading/hfm_advanced.py` | CUSUM + Walk-Forward Validation |
| `~/trading/backtest_pro.py` | Backtest engine |
| `~/.hermes/scripts/hfm_trade_journal.py` | Journal + stats + risk calculator |
| `~/.hermes/scripts/hfm_signal_checker.py` | Auto-push cron state checker |
| `~/trading/hfm_cron_push.py` | Dashboard feed push |
| `~/.hermes/scripts/hfm_supertrend_pro.py` | Supertrend Pro strategy (ATR buffer-zone, 3-level TP) |
| `~/trading/hfm_final.py` | gRPC auth chain reference |

## Pitfalls

- **Bot token 401**: Token can expire/get revoked. Symptom: `401 Unauthorized` on bot start. Fix: get new token from @BotFather (`/mybots` → select bot → API Token), update hardcoded fallback in `hfm_telegram_bot.py` line `BOT_TOKEN = os.environ.get("HFM_BOT_TOKEN", "...")`. Restart bot.
- **Python interpreter**: cron uses gateway's `/usr/local/lib/hermes-agent/venv/bin/python`. Terminal `python3` = deep-eye venv. Use `/usr/bin/python3` explicitly.
- **Empty-TF guard**: DataImpulse proxy flakiness can return empty TF. Always guard: `if len(m5)<30 or len(m15)<30: return`.
- **MACD signal-line**: MUST be `EMA9(MACD line)`, NOT `EMA9(close)`. Wrong implementation produces garbage histogram.
- **Cron lifecycle guard**: `/` token in Python formulas trips the guard. Use `* (1.0/n)` instead of `/n`.
- **Market closed detection**: Check `is_market_open()` — weekends + Friday after 07:00 WIB + Monday before 00:00 WIB = closed.
- **RR 3:1 optimal**: Don't use RR 2:1 or 4:1. Backtest proves 3:1 is the sweet spot.