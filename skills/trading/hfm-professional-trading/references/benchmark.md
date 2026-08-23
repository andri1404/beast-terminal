# GitHub XAUUSD Trading System Benchmark

Compiled from Exa search across GitHub, HuggingFace, and academic papers. All metrics verified from source repositories.

## Full Benchmark Table

| Rank | System | WR | PF | EV | Sharpe | DD | Period | Notes |
|------|--------|-----|------|-----|--------|-----|--------|-------|
| 🥇 | algo-trading (TanvirCCC) | 39.4% | 4.74 | +2.13R | 2.8 | 5.4% | 2020-2026 | SMC + RF + WFV, 622 OOS trades |
| 🥈 | RL PPO Gold (JonusNattapong) | 69.0% | — | N/A | 7.56 | 12.0% | 2004-2025 | PPO RL, 1M timesteps, $51/day |
| 🥉 | DRL Bot (zero-was) | 60-65% | 2.5-3.0 | N/A | 3.5-4.5 | <8% | 2015-2023 | PPO+Dreamer, 140+ features |
| 4 | Ai-XAUUSD (JonusNattapong) | 58.3% | 2.0+ | N/A | 2.0+ | <5% | 2015-2025 | Ensemble RL, 10yr, $45/day |
| 5 | xaubot (andywarui) | 66.2% | 1.96 | N/A | — | 19.5% | Apr-Nov 2025 | LightGBM, 68 features, 2332 trades |
| 6 | DQN Gold (Academic) | 58-72% | 2.0-2.4 | N/A | 1.0-1.4 | 1.3% | 2025 | ATR-MACD best, Price-Only 58% |
| 7 | pullback-XAU (ilahuerta) | 55.4% | 1.64 | N/A | 0.89 | 5.8% | 2020-2025 | State machine, 175 trades |
| 8 | Quantitative-XAU (soloshun) | 55.0% | 1.37 | N/A | 1.46 | — | 2024-2025 | XGBoost+LSTM, 398 trades |
| 9 | **HFM PRO v3 (OURS)** | **52.4%** | **1.61** | **+0.29R** | — | — | Jul-Aug 2026 | 7-factor + ML + CUSUM, 42 trades |
| 10 | DRL-WFO (kennycornellius) | N/A | N/A | +24.65% | — | 11% | 2025 | SAC walk-forward |
| 11 | Kalman-PPO (Academic) | N/A | N/A | N/A | 12.10 | 0.48% | 2017-2025 | Kalman filter + PPO |
| 12 | Gold-Predictive (BeanBagData) | 53-55% | — | — | — | — | 2025 | Ollama-guided genetic search |

## Key Insights

1. **algo-trading is KING** — 39.4% WR but PF 4.74 because of massive winners. Uses Random Forest ML filter + Walk-Forward Validation. This is our target architecture.

2. **RL systems dominate WR** (58-72%) but need massive training data (1M+ timesteps, 2004-2025). Not viable for us with limited data.

3. **SMC/ICT + ML = sweet spot** — algo-trading and xaubot both prove this combination works on gold.

4. **Our edge**: Real HFM broker gRPC feed + Claude opus-5 AI reasoning. No other system has this. The LLM layer adds context that pure indicators miss.

5. **Sweet spot targets** (from BeanBagData research): M5: 53.5-55% WR, 25-45 signals/day. Below 12 signals/day = overfitted "ghost hunter."

## Methodology Notes

- Walk-Forward Validation is the gold standard — prevents lookahead bias
- algo-trading uses 5 independent WFV windows, 622 OOS trades
- R-multiples (not dollar amounts) for fair comparison across account sizes
- Monte Carlo simulation for path-dependent risk (FTMO pass rates)