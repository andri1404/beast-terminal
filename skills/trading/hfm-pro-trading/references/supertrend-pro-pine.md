# XAUUSDBOTS SUPERTREND PRO — Pine Script Source

Source: `t.me/freexauusdforexea` | Telegram: `@silentcircletrader`

## Strategy Summary

Supertrend with buffer-zone confirmation, multi-level ATR targets, optional trailing SL, VWAP, Fibonacci golden zone, Heikin Ashi candle colors, and 100 EMA bias.

## Signal Logic

- **BUY**: price breaks above Supertrend upper buffer after a downtrend
- **SELL**: price breaks below Supertrend lower buffer after an uptrend
- Draws TP1/TP2/TP3 and SL lines + labels on each signal
- Table shows live SL/TP prices
- Optional VWAP line and Fib 50%/61.8% levels

## Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| ATR Period | 10 | Supertrend ATR |
| Factor | 5.0 | Supertrend multiplier |
| ATR Length | 14 | TP/SL ATR |
| Profit Factor | 3.0 | TP multiplier (1x/2x/3x) |
| Stop Factor | 2.5 | SL multiplier |
| Buffer % | 1.0 | Signal buffer zone |
| Fib Level 1 | 0.618 | Golden ratio |
| Fib Level 2 | 0.500 | Half retracement |
| Lookback | 50 | Fibonacci swing |

## Python Implementation

See `~/.hermes/scripts/hfm_supertrend_pro.py` for the full Python port using HFM gRPC feed.

Key differences from Pine Script:
- VWAP is session-based (reset daily) instead of cumulative
- Heikin Ashi computed from raw candles per bar
- Multi-TF confirmation includes M15+H1+H4 Supertrend alignment
- Signal persists to `/tmp/hfm_supertrend_result.json`
- Cron delivers on signal flip or >$3 price move