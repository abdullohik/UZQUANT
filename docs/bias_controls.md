# Backtest Bias Controls

## Look-ahead controls

- Financial data is unavailable until publication; later restatements replace earlier versions only after their own publication.
- Macro observations are unavailable until their stored vintage-known timestamp. Modern revised snapshots never populate earlier decisions.
- Ownership, rights, events, dividends, and corporate actions are unavailable before disclosure or announcement.
- Signals and model versions are unavailable before generation.
- Historical prices do not make a security eligible unless the universe record was itself known at the decision timestamp.

## Execution controls

- Only reported trades with positive observed volume can fill.
- Participation limits apply to each daily fill.
- Orders have an execution delay and finite fill window.
- Partial and rejected quantities remain uninvested and receive no later price return.
- Fees, spread, and slippage are recorded separately and reduce realized performance.
- Stale or forward-filled prices cannot execute.
- Missing depth does not become assumed liquidity.

## Universe and event controls

- Membership is reconstructed for each date without requiring current survival.
- Delisted names remain in earlier eligible universes.
- Delisting without verified consideration remains unresolved, visibly preventing a complete return rather than disappearing.
- Corporate actions require verified factors/economics and eligible announcement dates.
- Security-class-specific dividends are never transferred between common and preferred shares.

## Statistical controls

- The initial strategies are declared before testing and are not tuned for historical results.
- Missing benchmarks are unavailable rather than substituted.
- Theoretical mark-to-market return remains separate from liquidity-adjusted return.
- Insufficient history prevents annualized metrics and strategy conclusions.

## Current readiness failures

The real database has only 18 market dates, one current signal generation period, one known security-universe snapshot, no verified total-return series, and no verified historical benchmark. Running strategy selection would necessarily introduce hindsight or produce meaningless annualized statistics. Phase 13 therefore records `DATA_INSUFFICIENT` for all seven strategies.
