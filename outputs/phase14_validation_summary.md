# Phase 14 Validation Summary

| Measure | Result |
|---|---|
| Phase 13 classification | BACKTEST_INSUFFICIENT |
| Phase 14 classification | UNRELIABLE |
| Evidence outcome | C_INSUFFICIENT_HISTORY |
| Validation status | DATA_INSUFFICIENT |
| Validation version | walk-forward-validation/1.1.0 |
| Strategy version | pit-liquidity-backtest/1.0.0 |
| Experiments registered | 17 |
| Experiments completed | 0 |
| Experiments unavailable | 17 |
| Walk-forward windows | 0 |
| OOS observations | 0 |
| Stress-test results available | 0 |
| Model-risk findings | 7 |

## Blocking evidence

- `INSUFFICIENT_MARKET_HISTORY`
- `INSUFFICIENT_POINT_IN_TIME_FINANCIALS`
- `INSUFFICIENT_HISTORICAL_SIGNALS`
- `HISTORICAL_UNIVERSE_INSUFFICIENT`
- `TOTAL_RETURN_HISTORY_INSUFFICIENT`
- `EXECUTION_HISTORY_INSUFFICIENT`
- `BENCHMARK_UNAVAILABLE`
- `NO_COMPLETED_POINT_IN_TIME_BACKTEST`

## Interpretation

The strategy was **not actually tested**. No train/validation/OOS split or perturbation result was computed. The outcome is insufficient historical evidence, not a failed strategy and not a software failure.

All 17 variants remain registered, including the unsuccessful-to-run experiments; there was no best-result selection and no parameter search.
