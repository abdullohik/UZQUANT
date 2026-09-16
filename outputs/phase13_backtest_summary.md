# Phase 13 Backtest Summary

| Item | Result |
|---|---|
| Final classification | BACKTEST_INSUFFICIENT |
| Observed raw-market range | 2026-08-17 to 2026-09-15 |
| Usable historical test window | None |
| Raw market dates | 20 |
| Market observations | 140 |
| Securities with market rows | 7 |
| Underlying analytical signal dates | 1 (2026-09-15) |
| Legitimate historical signals | 0 |
| Strategies registered | 7 |
| Completed strategies | 0 |
| Orders | 0 |
| Fills | 0 |
| Unfilled orders | 0 (no eligible orders could be created) |
| Turnover / returns / risk metrics | Unavailable |
| Official benchmark | BENCHMARK_UNAVAILABLE |

## Strategy eligibility

All registered strategies are `DATA_INSUFFICIENT`. The production gate records:

`INSUFFICIENT_MARKET_HISTORY; INSUFFICIENT_POINT_IN_TIME_FINANCIALS; INSUFFICIENT_HISTORICAL_SIGNALS; HISTORICAL_UNIVERSE_INSUFFICIENT; TOTAL_RETURN_HISTORY_INSUFFICIENT; EXECUTION_HISTORY_INSUFFICIENT; BENCHMARK_UNAVAILABLE`

The two signal generation dates in storage are post-remediation reruns of one analytical as-of date. They are not a historical signal sequence. Similarly, two security-master ingestion dates are repeated current snapshots and cannot establish historical membership.

## Compatibility result

The existing simulation, point-in-time filters, corporate-action handling, and fill ledger remain usable. The readiness gate was corrected so repeated current runs cannot satisfy historical coverage checks. No redesign or new strategy was introduced.
