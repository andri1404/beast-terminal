# XAUUSD Trading System Benchmark Comparison

Full comparison of 12 GitHub XAUUSD trading systems vs our HFM PRO v3. Data collected August 2026.

## Full Ranking

| Rank | System | WR | PF | EV | DD | Notes |
|------|--------|-----|-----|-----|-----|-------|
| 🥇 | algo-trading (TanvirCCC) | 39.4% | 4.74 | +2.13R | 5.4% | SMC + RF ML, 622 OOS, 6yr WFV |
| 🥈 | RL PPO Gold (JonusNattapong) | 69.0% | 7.56* | N/A | 12.0% | PPO, 15min, 2004-2025 data |
| 🥉 | DRL Bot (zero-was-here) | 60-65% | 2.5-3.0 | N/A | <8% | PPO+Dreamer, 140+ features |
| 4 | Ai-XAUUSD (JonusNattapong) | 58.3% | 2.0+* | N/A | <5% | Ensemble RL, 10yr backtest |
| 5 | xaubot (andywarui) | 66.2% | 1.96 | N/A | 19.5% | LightGBM, 68 features, 2332 trades |
| 6 | DQN Gold (Academic) | 58-72% | 2.0-2.4 | N/A | 1.3% | Price-Only DQN: 58% WR, PF 2.01 |
| 7 | pullback-XAU (ilahuerta) | 55.4% | 1.64 | N/A | 5.8% | State machine, 5yr, 175 trades |
| 8 | Quantitative-XAU (soloshun) | 55.0% | 1.37 | N/A | N/A | XGBoost+LSTM, 398 trades |
| 9 | **HFM PRO v3 (confl=5)** | **52.4%** | **1.61** | **+0.29R** | N/A | 7-factor + ML + Claude AI |
| 10 | DRL-WFO (kennycornellius) | N/A | N/A | +24.65% | 11% | SAC walk-forward |
| 11 | Kalman-PPO (Academic 2025) | N/A | N/A | N/A | 0.5% | Kalman filter + PPO |
| 12 | Gold-AutoResearch (BeanBag) | 53-55% | N/A | N/A | N/A | Ollama genetic optimization |

## Our System Details

**HFM PRO v3** — 7-factor confluence + Random Forest ML + Claude opus-5 AI

| Config | Trades | WR | PF | EV |
|--------|--------|-----|-----|-----|
| Confl ≥ 4 (rule only) | 176 | 42.0% | 1.11 | +0.06R |
| Confl ≥ 5 (SNIPER) | 42 | 52.4% | 1.61 | +0.29R |
| + ML Filter (RF) | 42+ | 52.4%+ | 1.61+ | +0.29R+ |
| RR 2:1 | 50 | 44.0% | 1.57 | +0.32R |
| **RR 3:1 (deployed)** | 50 | 36.0% | 1.69 | +0.44R |

**Unique advantages:**
- Real HFM broker gRPC feed (not yfinance/MT5 export)
- Claude opus-5 AI reasoning layer
- Full Telegram bot with 15+ commands
- 7-factor confluence + ML filter + CUSUM regime
- Walk-forward validated (18 windows)
- Auto-push signal with on/off control

## Key Insights

1. **algo-trading is the gold standard**: 39.4% WR but EV +2.13R because of massive winners. Uses Random Forest ML filter + walk-forward. Their approach is our target.

2. **RL systems dominate WR** (58-72%) but require massive training data (2004-2025, millions of timesteps). Not feasible for us yet.

3. **SMC/ICT + ML = sweet spot**: algo-trading and xaubot both prove this combination works. We're on the right track.

4. **Our edge**: Claude AI + real HFM data. No other system has this combination.

5. **Target**: Top 5 with 1000+ trades of training data for ML filter.