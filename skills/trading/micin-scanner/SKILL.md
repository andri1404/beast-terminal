---
name: micin-scanner
description: Use when trading meme coins. DexScreener+RugCheck+AI scan.
tags: [meme-coin, trading, solana, dexscreener, rugcheck, solsignal, opus-5]
---

# Micin Scanner — Meme Coin Hunter + AI Analysis

DexScreener API → Pair Details → Filters (liq≥$5K, vol≥$2K, age≤24h, mc≤$1M) → RugCheck + SolSignal → Claude opus-5 via mwapi → Trading signals

## Files
- Scanner: `/home/ubuntu/micin_scanner.py`
- Results: `/home/ubuntu/micin_scan_results.json`
- Cron: `b7110a2c82cf` (every 15m, deliver to origin)

## Commands
```bash
python3 /home/ubuntu/micin_scanner.py
python3 /home/ubuntu/micin_scanner.py --quiet  # cron mode
hermes cron pause b7110a2c82cf
```

## Pitfalls
- SolSignal free tier: 10/day. Scanner uses 3/tick.
- RugCheck sometimes returns NO_DATA for non-Solana tokens.
- mwapi needs curl_cffi (impersonate=chrome). Regular urllib gets CF 1010.