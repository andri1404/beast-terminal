# Backtest Deep Analysis — WIN vs LOSS Patterns

30 days, 2000 HFM M15 candles, walk-forward, no lookahead.

## RR Optimization

| RR | Trades | WR | PF | EV |
|----|--------|-----|-----|-----|
| 2.0:1 | 50 | 44.0% | 1.57 | +0.32R |
| 2.5:1 | 50 | 40.0% | 1.67 | +0.40R |
| **3.0:1** | **50** | **36.0%** | **1.69** | **+0.44R** ⭐ |
| 4.0:1 | 50 | 18.0% | 0.88 | -0.10R |

## Filter Impact

| Filter | Trades | WR | PF | EV |
|--------|--------|-----|-----|-----|
| Baseline (confl≥5) | 50 | 32.0% | 1.41 | +0.28R |
| + ADX < 30 | 31 | 32.3% | 1.43 | +0.29R |
| + ATR < $8 | 23 | 39.1% | 1.93 | +0.57R |
| + Mon/Wed only | 21 | 52.4% | 3.30 | +1.10R |
| + Bullish candle | 41 | 36.6% | 1.73 | +0.46R |
| **ALL FILTERS** | **8** | **50.0%** | **3.00** | **+1.00R** |

## WIN vs LOSS Characteristics (RR 3:1)

| Metric | WIN avg | LOSS avg | Diff |
|--------|---------|----------|------|
| ADX | 27.9 | 31.4 | -3.5 |
| ATR | $7.7 | $9.0 | -$1.3 |
| MACD hist | -1.3 | -0.4 | -0.9 |
| Bars held | 18.0 | 10.4 | +7.6 |
| RSI M15 | 52.4 | 52.5 | -0.1 |

## Day-of-Week Pattern

| Day | Trades | WR |
|-----|--------|-----|
| Monday | 9 | 44.4% |
| Tuesday | 17 | 11.8% |
| Wednesday | 12 | 58.3% |
| Thursday | 9 | 33.3% |
| Friday | 3 | 0.0% |

## Candle Pattern

| Pattern | Trades | WR |
|---------|--------|-----|
| Bullish | 27 | 29.6% |
| Hammer | 3 | 33.3% |
| Bearish | 6 | 0.0% |
| Shooting-star | 1 | 0.0% |

## Benchmark Comparison

| System | WR | PF | EV |
|--------|-----|-----|-----|
| algo-trading (SMC+ML) | 39.4% | 4.74 | +2.13R |
| xaubot (LightGBM) | 66.2% | 1.96 | N/A |
| nixie-gold-bot | 65-75% | >1.8 | >0.8R |
| HFM PRO (confl=5) | 52.4% | 1.61 | +0.29R |
| HFM PRO (ALL FILTERS) | 50.0% | 3.00 | +1.00R |