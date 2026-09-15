# Phase 14 Robustness Tests

## Result

**Classification: UNRELIABLE**  
**Validation status: DATA_INSUFFICIENT**  
**Experiments registered: 17**  
**Model-risk findings: 7**

This classification does not mean the investment logic has been proven poor. It means there is currently no valid evidence that it generalizes. Phase 13 has no completed point-in-time performance run, so Phase 14 cannot calculate stress survival, confidence intervals, factor monotonicity, subperiod stability, turnover stability, or parameter sensitivity from real strategy returns.

## Complete experiment registry

Every declared experiment is retained; none is omitted based on outcome.

| Experiment | Family | Perturbation | Status |
|---|---|---|---|
| BASELINE | Baseline | Declared reference model | DATA_INSUFFICIENT |
| EQUAL_FACTOR_WEIGHTS | Factor weights | Equal weighting | DATA_INSUFFICIENT |
| LOWER_LIQUIDITY_THRESHOLDS | Liquidity | Threshold multiplier 0.75 | DATA_INSUFFICIENT |
| CONFIDENCE_THRESHOLD_60 | Confidence | Minimum confidence 60 | DATA_INSUFFICIENT |
| DOUBLE_HOLDING_PERIOD | Holding period | 2× holding period | DATA_INSUFFICIENT |
| MONTHLY_REBALANCE | Rebalance | Monthly schedule | DATA_INSUFFICIENT |
| WIDER_VALUATION_SPREAD | Valuation | 1.25× bear/bull dispersion | DATA_INSUFFICIENT |
| HALF_POSITION_SIZE | Position sizing | 0.5× positions | DATA_INSUFFICIENT |
| HIGHER_FEES | Costs | 2× fees | DATA_INSUFFICIENT |
| DOUBLE_SLIPPAGE | Slippage | 2× slippage | DATA_INSUFFICIENT |
| THREE_DAY_DELAY | Execution delay | Three-day delay | DATA_INSUFFICIENT |
| WORSE_FILLS | Fill quality | 0.5× participation and 1.5× slippage | DATA_INSUFFICIENT |
| VALUATION_ERROR_MINUS_20 | Valuation error | 0.8× fair value | DATA_INSUFFICIENT |
| ALTERNATE_FACTOR_WEIGHTS | Factor weights | Lower valuation, higher quality/liquidity weights | DATA_INSUFFICIENT |
| LOWER_LIQUIDITY | Liquidity | 0.5× observed ADV | DATA_INSUFFICIENT |
| REMOVE_BEST_SECURITY | Concentration | Remove best contributor | DATA_INSUFFICIENT |
| REMOVE_BEST_PERIOD | Time concentration | Remove best period | DATA_INSUFFICIENT |

## Walk-forward splits

No production split was created. Eighteen market dates are insufficient for defensible train, validation, and final out-of-sample samples, and there is no historical signal sequence to evaluate. The split engine is covered by deterministic tests using controlled date sequences; those fixtures are not market-performance evidence.

## Statistical tests

| Test | Production result | Reason |
|---|---|---|
| Bootstrap confidence interval | Unavailable | No eligible return sample |
| Factor monotonicity | Unavailable | No point-in-time factor/forward-return panel |
| Subperiod stability | Unavailable | No completed OOS periods |
| Parameter sensitivity | Unavailable | Stress returns unavailable |
| Turnover stability | Unavailable | No completed portfolios |
| Removal of best security | Unavailable | No realized contribution ledger |
| Removal of best period | Unavailable | No eligible return periods |

## Model risks

Data coverage is `CRITICAL`. Dependence on one security, one period/year, one sector, one illiquid event, one parameter threshold, or one valuation assumption is currently untestable and therefore retained as `HIGH` risk—not treated as absent.

## Reasons for classification

- fewer than 60 market dates;
- no historical signal sequence;
- no reconstructable historical universe snapshots;
- no verified total-return series;
- no verified historical benchmark series;
- no completed point-in-time backtest.

No model can receive `ROBUST` until multiple genuine out-of-sample periods and a broad majority of declared perturbations show reasonable stability.
