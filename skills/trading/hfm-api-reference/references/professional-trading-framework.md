# Professional XAUUSD Trading Framework — Research Synthesis

Condensed from institutional trading research (Aug 2026). Sources: pro-scalper.com, tradingnx.com, grandalgo.com, akprotraders.com, oyamori.com, liquidityscan.io, completetradersedge.com, snappchart.app, chartwhisperer.ca, fxnx.com.

## Multi-Timeframe Discipline (the core edge)

| TF | Role | Rule |
|----|------|------|
| D1 | Bias | Sets direction. NEVER trade against it. |
| H4 | Structure | Identifies swing points, S/R zones, liquidity pools |
| H1 | Setup | Finds POI (Order Block, FVG, Fibonacci zone) |
| M15 | Trigger | Confirms entry with CHoCH/BOS + candle pattern |
| M5 | Execution | Precision entry after candle CLOSE (not wick) |

**Key insight:** D1/H4 bias is a GATE, not a factor. Counter-trend trades have statistically lower win rates.

## 7-Factor Confluence Scoring (deployed in `hfm_pro_signal.py`)

| # | Factor | Weight | Description |
|---|--------|--------|-------------|
| 1 | TREND | 1pt | D1+H4+H1+M15 all aligned (EMA20>50) |
| 2 | STRUCTURE | 1pt | Price at EMA, Fibonacci, S/R zone (not mid-air) |
| 3 | MOMENTUM | 1pt | MACD histogram + RSI confirm direction |
| 4 | LIQUIDITY | 1pt | Recent sweep of session high/low confirmed |
| 5 | PATTERN | 1pt | Candle confirmation (hammer, engulfing, rejection) |
| 6 | VOLATILITY | 1pt | ADX ≥ 25 confirming trend strength |
| 7 | PULLBACK | 1pt | Price at discount (long) / premium (short), not chasing |

**Verdict thresholds:**
- < 4 = STAND DOWN (WAIT) — no exceptions
- 4 = TRADEABLE — enter with standard size
- 5+ = A+ SETUP — full size, highest conviction

## Gatekeeper (hard gates, must pass)

1. **HTF BIAS**: D1+H4 must agree on direction. Neutral = no trade.
2. **SESSION**: London (07:00-10:00 UTC), Overlap (12:00-16:00 UTC), or NY. Asia = avoid breakouts.
3. **NEWS**: No red-flag events (NFP, CPI, FOMC, GDP) within 30 minutes.
4. **DXY**: Correlation ~-0.85. Gold long = DXY bearish. Conflict = skip or reduce size.

## SMC/ICT Entry Framework

1. **Sweep**: Price takes out liquidity at session high/low
2. **Displacement**: Strong impulsive move away from sweep
3. **FVG/OB**: Fair Value Gap or Order Block left by displacement
4. **Retest**: Price returns to FVG/OB zone
5. **Entry**: Candle CLOSE confirmation (not wick, not mid-candle)
6. **Stop**: Beyond sweep wick (not at swing — gold over-extends 20-50 pips)

## Gold-Specific Rules

- 60-70% of breakouts are fake — wait for retest + candle close
- Gold over-extends 20-50 pips before reversing — stops must account for this
- Minimum R:R 2.5:1 nominal (2:1 after spread on gold)
- 1% risk per trade, 3% daily loss cap
- 3 consecutive losses = stop trading for the day
- Asian session: fade extremes only, no breakout trades
- News: NFP, CPI, FOMC = no trade ±30 min

## Risk Management

| Parameter | Value |
|-----------|-------|
| Per-trade risk | 1% max |
| Daily loss limit | 3% |
| 3-loss rule | Stop after 3 consecutive losses |
| Minimum R:R | 2.5:1 nominal (gold spread) |
| Stop placement | Beyond structural invalidation + buffer |
| Position sizing | Lot = (account × risk%) / (SL distance × pip value) |
| Partial exits | 50% at 1:1R → BE, 50% to target |

## Session Timing (WIB)

| Session | UTC | Quality | Behavior |
|---------|-----|---------|----------|
| ASIAN | 00:00-07:00 | LOW | Range-bound, fade extremes |
| LONDON | 07:00-10:00 | PRIME | Asia sweep, trend establishment |
| LONDON_MID | 10:00-12:00 | MEDIUM | Continuation or consolidation |
| OVERLAP | 12:00-16:00 | PRIME | Highest volume, NY+London |
| NY | 16:00-21:00 | MEDIUM | Directional but slower |
| EVENING | 21:00-00:00 | LOW | Thin liquidity, avoid |

## Pre-Trade Checklist (11-step)

1. ☐ HTF Bias confirmed (D1+H4 agree)
2. ☐ Session liquid (London/NY/Overlap)
3. ☐ No red-flag news within 30 min
4. ☐ Liquidity swept (stop hunt confirmed)
5. ☐ Displacement confirmed (impulsive move)
6. ☐ Structure shift (CHoCH/BOS on M15)
7. ☐ Retest to OB/FVG zone
8. ☐ Candle confirmation (close, not wick)
9. ☐ Invalidation defined (structural stop)
10. ☐ Target defined (next liquidity pool)
11. ☐ Risk calculated (1% max, R:R ≥ 2:1)

## Claude AI Prompt Pattern (professional)

```
System: Institutional gold trader, 15+ years. SMC/ICT framework.
Rules: HTF bias = gate. Confluence < 4 = WAIT. Counter-trend = NEVER.
Format: ARAH / MASUK / TP·SL / CHECKLIST / CATATAN (5 lines, Bahasa Indonesia)
```

## Scripts Architecture

```
hfm_pro_signal.py     → Professional 7-factor engine (replaces hfm_ai_signal.py)
hfm_telegram_bot.py   → Full Telegram bot: /pro, /confluence, /checklist, /trade, etc.
hfm_cron_push.py      → Dashboard feed (1m cron)
smart_signal.py       → Rule-based backup signal
autotrade_bot.py      → Auto-trade engine (DRY/LIVE modes)
```

## Key Lessons from Backtesting

- Rule-based M15 gold entry = NEGATIVE expectancy (gold whipsaws SLs)
- Edge is AI (LLM) reasoning, not rule voting
- Confluence = VETO (block entry < 4), not trigger
- Naive alignment-entry chases price; profitable entry needs pullback-to-level + candle confirmation