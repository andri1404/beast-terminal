# AI vs rule-based trading — validated findings (HFM XAUUSD, 2026-08)

Condensed from this session's research + backtests. Use to guide signal design.

## The core lesson
Rule-based indicator voting on gold M15 has NEGATIVE expectancy. The edge is
LLM reasoning + discipline, not more indicators. Confluence score is a VETO
(block entry < threshold), NOT a trigger.

## Backtest evidence (real HFM gRPC data, walk-forward, no lookahead)
| Config | Trades | WR | PF | Net |
|---|---|---|---|---|
| Confluence>=4 + hammer + TP1.5x | 13 | 30.8% | 0.50 | -$48 |
| Confluence>=3 + hammer + TP1.5x | 28 | 25.0% | 0.39 | -$144 |
| Old multi-TF align | 15 | 26.7% | — | -$29 |

AI sampling (36 → 15 usable points, `backtest_ai_sampling.py`): Claude said
**WAIT 14/15** (93%) — extremely selective, only 1 trade. Too few trades to
prove profit statistically, but the discipline (refusing bad entries) is the
real value. HFM CandlesData caps at ~2000 bars/TF (~20 days) so a
statistically meaningful AI backtest needs a grown local dataset
(`hfm_collect.py` hourly → SQLite `~/.hermes/data/hfm_dataset.sqlite`).

## Academic backing (Exa research)
- 2026 thesis (diva-portal): LLM-assisted strategy **33.1–61.2% total return**
  vs best indicator baseline 17.5% (MACD). All LLM strats Sharpe >1.0, baselines
  <1.0. **Temperature 0.5 = sweet spot.**
- `MayurBhavsar/xauusd-agent`: confluence scoring 0-5 + multi-LLM + circuit
  breaker + SQLite trade journal.
- `josercp/EA_SCALPER_XAUUSD`: 10-gate SMC (session→regime→H1→structure→MTF→
  confluence→entry), target 65-75% WR, RR 2-2.5.
- `andywarui/xauusd-ai-trading-bot`: LightGBM 68 features → 66.2% WR, PF 1.96.
- Pro-scalper: London/NY only, M5 trend + M1 entry, candle must CLOSE first,
  SL 15-20 pips, stop after 3 losses, spread <0.5 pip.

## Confluence score recipe (deployed in hfm_ai_signal.py)
0-5, one point each: (1) trend all-TF aligned D1+H4+H1+M15; (2) momentum
MACD>signal AND RSI>50 (bull) / mirrored (bear); (3) ADX>=25 (trend strength);
(4) pullback to EMA21 (not chase); (5) liquid session (London/Overlap/NY).
Threshold: <4 = WAIT. Claude cross-checks and can override with its own score.

## MACD signal-line bug (regressed twice — always verify)
Signal = `EMA9(MACD line)`, NOT `EMA9(close)`. Wrong version gives hist ~±$4361
on gold (garbage) and flips votes. Verify hist is ~±2, not thousands.
```python
e12=ema_series(c,12); e26=ema_series(c,26)
mac=[e12[i]-e26[i] for i in range(len(c))]
sig=ema_series(mac,9); hist=mac[-1]-sig[-1]
```
