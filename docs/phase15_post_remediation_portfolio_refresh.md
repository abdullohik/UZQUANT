# Phase 15 Post-Remediation Portfolio Refresh

## Outcome

The existing Phase 15 engine was refreshed against the repaired research engine and the accepted Phase 14 result. It created nine new append-only portfolio runs: three existing styles across three AUM scenarios.

**Result: 0 eligible securities, 0 positions, 100% cash in every run.**

This is a research-system eligibility outcome, not personalized advice. No admission gate, confidence threshold, liquidity rule, risk gate, or validation requirement was weakened.

## Compatibility review

The existing deterministic engine continues to use or fail closed on:

- valuation-derived expected upside and downside;
- signal confidence and minimum confidence by style;
- liquidity position capacity and liquidation horizon;
- observed volatility and correlations only when usable;
- sector, single-name, correlated-group, factor, government, commodity, and FX caps;
- governance and Data Quality evidence;
- free-float capacity when verified;
- signal/thesis lineage and execution constraints;
- the latest Phase 14 validation classification.

Unknown inputs remain unavailable rather than zero. Missing correlation is conservatively treated as fully correlated for allocation capacity and prevents covariance-risk claims. Unknown macro exposures, factor exposures, governance, or capacity block admission rather than becoming neutral assumptions.

One concrete compatibility defect was fixed: production refreshes previously defaulted to the old fixed date `2026-09-15` even when they consumed a Phase 14 validation run created on `2026-09-16`. New runs now use the execution date and portfolio model `transparent-portfolio/1.1.0`.

## Refreshed portfolios

Generated as of 2026-09-16.

| Style | AUM (UZS) | Eligible | Positions | Cash weight | Status |
|---|---:|---:|---:|---:|---|
| CONSERVATIVE | 20,000,000 | 0 | 0 | 100% | DATA_INSUFFICIENT |
| CONSERVATIVE | 1,000,000,000 | 0 | 0 | 100% | DATA_INSUFFICIENT |
| CONSERVATIVE | 20,000,000,000 | 0 | 0 | 100% | DATA_INSUFFICIENT |
| BALANCED | 20,000,000 | 0 | 0 | 100% | DATA_INSUFFICIENT |
| BALANCED | 1,000,000,000 | 0 | 0 | 100% | DATA_INSUFFICIENT |
| BALANCED | 20,000,000,000 | 0 | 0 | 100% | DATA_INSUFFICIENT |
| HIGH_CONVICTION | 20,000,000 | 0 | 0 | 100% | DATA_INSUFFICIENT |
| HIGH_CONVICTION | 1,000,000,000 | 0 | 0 | 100% | DATA_INSUFFICIENT |
| HIGH_CONVICTION | 20,000,000,000 | 0 | 0 | 100% | DATA_INSUFFICIENT |

## Admission findings

The current seven market-covered securities are AGMK, AGMKP, IPKY, KASU, KASUP, QZSM, and UZTL. Every security fails `MODEL_NOT_VALIDATED` because Phase 14 is `UNRELIABLE — INSUFFICIENT EVIDENCE`. None has an eligible STRONG_BUY/BUY/ACCUMULATE signal: UZTL is HOLD, AGMK is LIQUIDITY_TRAP, and the remaining five are DATA_INSUFFICIENT.

All confidence scores are below even the HIGH_CONVICTION minimum of 55. No security has a validated valuation range or an AVAILABLE Phase 11 final position capacity. Governance/Data Quality evidence, macro exposures, and factor exposures are incomplete under the portfolio admission contract. AGMK and AGMKP additionally fail liquidation-horizon requirements in the current execution evidence.

The Phase 14 state is treated correctly: its `UNRELIABLE` classification is preserved as an evidence limitation, but the documented portfolio rule admits only `ROBUST` or `PROMISING_BUT_UNPROVEN`. Therefore all securities remain excluded.

## AUM and capacity

Because admission fails before allocation, all three AUM scenarios remain 100% cash; no real security capacity curve can be claimed. Existing deterministic tests confirm that, for an otherwise eligible candidate, fixed liquidity capacity produces a smaller maximum weight as AUM rises. This mechanical test is not substituted for a real position.

## Difference versus the previous Phase 15 run

Allocation outcome is unchanged: previous and refreshed runs both contain zero positions and 100% cash. The refreshed runs differ by using current post-Remediation-C signals, explicit Phase 14 `C_INSUFFICIENT_HISTORY` lineage, the corrected as-of date, and portfolio model version 1.1.0. UZTL now has a HOLD research state rather than DATA_INSUFFICIENT, but HOLD is not portfolio-admissible and does not override missing valuation, low confidence, or UNRELIABLE validation.

Prior portfolio rows were not overwritten. The database now contains 27 portfolio runs in total, with the latest 9 belonging to this refresh; all historical runs remain intact.
