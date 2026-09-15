# Point-in-Time Liquidity-Aware Backtesting

## Purpose

The Phase 13 framework tests realizable historical behavior, not retrospective price selection. Version `pit-liquidity-backtest/1.0.0` prioritizes rejection over performance whenever decision-time data, historical membership, total-return adjustments, or execution evidence is insufficient.

## Decision-time snapshot

Each snapshot is security-level and filters information by the field that establishes when it could be known:

- listings and identifiers: `known_at`, with listing/delisting validity dates;
- prices: `trade_date` and `first_seen_at`, raw observed series only;
- financial reports and restatements: publication date; the latest eligible version is selected within reporting perimeter and accounting standard;
- ownership and rights: disclosure date and effective date where applicable;
- events: publication timestamp;
- corporate actions and dividends: announcement date before effective/payment treatment;
- macro: `vintage_known_at` and observation period end;
- signals and model versions: generation timestamp.

Snapshot records preserve all eligible IDs and model versions. Data published, disclosed, announced, retrieved, or generated after the decision timestamp is excluded.

## Historical universe

Universe membership uses listing records known by the decision date and applies listing/delisting validity for that date. It does not filter against current active status, so later-delisted securities remain in earlier snapshots when reconstructable. Renames remain attached to stable security IDs through identifier history. Unresolved delistings remain explicit unresolved positions rather than disappearing or being assigned an invented recovery value.

The production database currently lacks a sequence of historical universe snapshots. Its current security-master snapshot cannot safely establish past membership, including failed, merged, converted, or delisted securities. This blocks the real strategy run.

## Returns and corporate actions

Cash dividends are included only for the correct security when announcement and payment evidence is eligible. Split factors are applied only when verified and announced before the decision cutoff. The framework has explicit extension points for other verified actions. Unknown merger consideration, rights economics, conversions, tenders, or delisting recovery are not estimated. No verified total-return series currently exists, which is a production readiness failure.

## Execution simulation

Orders begin after a configurable delay (default one day), use only actual `TRADE_REPORTED` observations, and cap each fill at observed volume × participation rate. Zero-volume/no-trade rows cannot fill. Orders may fill across multiple days, partially fill, expire, or be rejected. A later quoted price rise contributes no profit for unfilled shares.

Each fill stores the signal date through its order, decision price, fill date, reference and fill prices, shares, observed volume, participation, transaction/broker/exchange/depository fees, slippage, source observation, and model version. Spread and slippage apply adversely by side. Fee inputs must be verified or explicitly modeled assumptions before a production performance run.

## Strategies and benchmarks

The registered initial strategies are Equal Weight Universe, Value, Quality, Value + Quality, Top Overall Ranking, Overall Ranking + Liquidity Gates, and Overall Ranking + Confidence Threshold. Parameters are fixed and interpretable; no optimization is performed.

Potential benchmarks are the Uzbek market benchmark, equal-weight universe, market-cap-weight universe, and cash/risk-free proxy. A benchmark is reported only if its point-in-time membership, weights, values, and currency are verified. No eligible historical benchmark series currently exists.

## Metrics

The framework calculates total return, CAGR, annualized volatility, Sharpe, Sortino, maximum drawdown, Calmar, win rate, average winner/loser, profit factor, turnover, transaction costs, slippage, average holding period, liquidity-adjusted return, and capacity. Unsupported metrics remain NULL with a reason. Risk-free rate is not silently assumed; Sharpe/Sortino require an explicit eligible assumption in a full run.

Run the production gate with `python3 -m uzquant run-backtests`.
