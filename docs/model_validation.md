# Model Validation and Robustness

## Validation design

UZQUANT validation version `walk-forward-validation/1.0.0` uses chronological train, validation, and out-of-sample partitions or rolling walk-forward equivalents. The final out-of-sample partition is marked locked. Any experiment declaring that it used the locked period for tuning is rejected. A new strategy or materially distinct parameter set must be registered before its result is evaluated.

The experiment registry stores the variant name, family, complete parameters, hypothesis, baseline parent, registration time, status, and result—even when unsuccessful or data-insufficient. It prevents reporting only the best variant while hiding the number of trials.

## Perturbations

The declared robustness suite changes factor weights, liquidity thresholds, confidence thresholds, holding period, rebalance frequency, valuation dispersion, and position size. Stress variants apply higher fees, double slippage, three-day execution delay, worse fills, a 20% valuation error, alternate weights, half observed liquidity, removal of the best security, and removal of the best period.

These are predeclared stress tests, not tuned strategy parameters. Production results are stored for every variant. When the underlying point-in-time backtest is unavailable, each variant is `DATA_INSUFFICIENT`; no proxy return is manufactured.

## Statistical gates

Bootstrap confidence intervals require at least 20 observations and default to a deterministic 1,000-resample procedure. Factor monotonicity requires at least 10 paired observations and three distinct scores. Subperiod stability, parameter sensitivity, and turnover stability require eligible completed results across multiple partitions/experiments. Unsupported tests remain unavailable.

The `ROBUST` label requires all of the following minimum conditions:

- positive baseline return;
- at least three out-of-sample periods;
- at least 80% of declared stress results available;
- at least 75% stress survival;
- at least 67% positive subperiods;
- no single security contributing more than 35% under the tested concentration measure.

These thresholds are conservative model-validation policy, not claims of statistical significance. A positive result with incomplete stability evidence is at most `PROMISING_BUT_UNPROVEN`. Negative or concentrated results are `FRAGILE`. Missing baseline/OOS evidence or fewer than three available stresses is `UNRELIABLE`.

## Model-risk review

The framework records dependence on one security, period/year, sector, illiquid event, threshold/parameter, and valuation assumption. Removal tests measure whether results survive the best security and best period. No dependence is deemed absent merely because it cannot be tested.

## Current production status

Phase 13 produced no completed point-in-time backtest. The market sample has only 18 dates, no historical signal sequence or reconstructable universe snapshots, no verified total-return series, and no verified historical benchmark. Phase 14 therefore classifies the current strategy evidence as `UNRELIABLE` and records all dependence categories as untestable/high risk.

Run with `python3 -m uzquant validate-model` after the point-in-time backtest registry has eligible completed runs.
