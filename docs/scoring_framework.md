# UZQUANT scoring framework

Model version: `research-ranking/1.0.0`  
Scoring version: `factor-scoring/1.0.0`

## Principles

Factor scores never replace or modify raw values. Every factor record stores its raw metric/evidence, named transformation, 0–100 score or explicit unavailable state, source record IDs, snapshot, date and scoring version. Missing factors are not assigned an average score.

The supported components are Valuation, Quality, Growth, Momentum, Dividend, Liquidity, Governance, Catalyst, Balance-Sheet Risk and Data Quality. Catalyst is deliberately an unavailable placeholder in this phase.

## Construction

Cross-sectional percentiles require at least five comparable peers within a defensible sector group. The transformation uses the empirical rank without winsorizing source values. Smaller groups return `SMALL_PEER_GROUP`. Absolute mappings may be used only when documented.

Sector routes are explicit:

- General: ROIC/margins, revenue/EBIT growth, leverage and interest coverage.
- Bank: ROE/NIM/cost-income, loan/deposit growth, NPL and capital adequacy.
- Insurance: combined ratio/ROE, premium growth, solvency and reserves.
- Mining: ROIC/operating leverage, production/revenue growth and leverage.

The current peer groups and histories cannot support defensible sector rankings. These scores remain unavailable rather than borrowing metrics from another sector.

Liquidity uses the documented Phase 7 absolute state mapping: `INVESTABLE` 80, `LIMITED_LIQUIDITY` 50, `HIGH_LIQUIDITY_RISK` 20 and `LIQUIDITY_TRAP` 0. LOW evidence confidence caps the score at 60. `UNASSESSABLE` remains unavailable.

## Investment attractiveness

Default configurable weights are valuation 25%, quality 15%, growth 10%, momentum 5%, dividend 5%, liquidity 15%, governance 10%, balance-sheet risk 10% and data quality 5%. Catalyst has zero weight until implemented. Weights were not optimized against returns.

At least four positively weighted factors must be available. Available weights are renormalized; unavailable factors are never converted to neutral scores. The tentative 0–100 mapping supports all research states: ≥80 `STRONG_BUY`, ≥70 `BUY`, ≥60 `ACCUMULATE`, ≥45 `WATCH`, ≥35 `HOLD`, ≥20 `REDUCE`, otherwise `AVOID`. Hard gates then override this tentative state.

## Real-run status

The supportable universe is the seven securities with verified Phase 2 histories. Only Data Quality and, except for AGMK, Liquidity can currently be scored. All valuation records are insufficient, financial history is one period, and market history is 18 observations. Consequently investment attractiveness is unavailable for every real case.
