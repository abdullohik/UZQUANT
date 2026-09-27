# UZQUANT Research-Ready Closure

Audit date: 2026-09-28 (Asia/Tashkent)  
Scope: the unchanged `RESEARCH_READY` rubric in `docs/readiness.md`  
Conclusion: **RESEARCH_READY — LIMITED MINIMUM-VIABLE COHORT (IPKY)**

This conclusion is about the ability to produce a source-traceable, appropriately qualified company-research output. It is not an investment signal, portfolio admission, paper-trading claim, or authorization to use capital. IPKY remains `DATA_INSUFFICIENT` for the ranking engine and is not portfolio-eligible.

## What changed in this closure

A normal due production cycle completed successfully on 2026-09-27 UTC. All 17 monitored pipelines are `HEALTHY`; 15 ran because ownership and security-rights were still inside their weekly freshness windows. The run processed the current source chain through signals with no anomaly and no signal transition. A justified second `FULL_FREEZE_V1` snapshot was then captured. The existing IPKY valuation workflow independently reconciled the current residual-income result with maximum absolute difference `0E-26`.

One genuine traceability defect was fixed. Momentum previously reported `MARKET_HISTORY_BELOW_60_OBSERVATIONS` unconditionally. IPKY has 73 raw observations, so the truthful reason is now `NO_VERIFIED_CORPORATE_ACTION_ADJUSTED_RETURN_SERIES`. Momentum remains unavailable; no score, threshold, gate, or recommendation changed.

## Existing rubric decision

| # | Requirement from `docs/readiness.md` | Status | Evidence and interpretation |
|---|---|---|---|
| 1 | Legitimate current market/security source and stable fresh cycles | PASS | Public RSE path is operational; the database contains two complete 17-pipeline healthy cycles on 2026-09-26 and a normal due cycle on 2026-09-27. All 17 health rows are current and `HEALTHY`. |
| 2 | Complete source-traceable research packs for a minimum viable cohort | PASS, LIMITED | IPKY is the minimum viable cohort: verified identity/class/shares, current observed market data, audited consolidated IFRS inputs, valuation assumptions, valuation, liquidity, macro reference, lineage, and explicit unknowns. The rubric specifies no larger numeric cohort. Breadth remains a higher-tier limitation. |
| 3 | Resolve units and perimeter for every statement used in valuation | PASS | IPKY valuation uses the audited 2023 consolidated IFRS PDF; every used financial value is normalized to UZS from the document's stated million-UZS basis. |
| 4 | Authoritative rights for any preferred security being valued | NOT_EVALUABLE / NOT REQUIRED | IPKY is verified `COMMON`. No preferred security is included in the minimum cohort and no preferred valuation is claimed. |
| 5 | Explicit, sourceable, consistent assumptions and independent reconciliation | PASS | Nine versioned assumptions are stored. The model is nominal UZS throughout. The CBU curve is authoritative; ROE is source-derived; beta/ERP/CRP and terminal growth are identified as assumptions. Reconciliation passed exactly. |
| 6 | Exact signal lineage and breaking-schema evidence in a real post-hardening cycle | PASS | `FULL_FREEZE_V1`, source-schema contracts/checks, immutable normalized versions, exact observation lineage, and healthy post-hardening cycles are present. |
| 7 | No unresolved defect capable of silently contaminating security conclusions | PASS | Prior critical/high findings are closed, foreign-key check is clean, missing evidence fails closed, and the momentum misdescription found here was corrected without creating a score. |
| 8 | Independent audit against current database/source state | PASS | This closure and its evidence outputs use the refreshed production database and current health state. |

The phrase “minimum viable cohort” is qualitative in the canonical rubric. Treating it as three securities would import an earlier audit recommendation as a new threshold. One fully traceable common security is sufficient to prove the research workflow; it is not sufficient to prove broad universe coverage, strategy validity, or investability.

## Research readiness versus investment eligibility

`RESEARCH_READY` does not require a `BUY`, `ACCUMULATE`, or `HOLD`; portfolio eligibility; high confidence; validated historical performance; a mature paper sample; or a generated position. Those belong to analytical conclusions or later maturity levels. A valid research system may conclude “valuation available, evidence limited, no action.”

IPKY remains `DATA_INSUFFICIENT` because only three positively weighted factors are available while aggregation requires four. There is no triggered hard risk gate. This fail-closed classification is correct and does not invalidate its available valuation or its research report.

## Production and prospective proof

- Pipeline health: 17 `HEALTHY`, 0 failed, 0 degraded, 0 stale.
- Current due run: 15 due pipelines completed; 2 weekly pipelines remained fresh and were not artificially rerun.
- Successful valuation: IPKY residual income, `AVAILABLE`, model `sector-valuation/3.2.0`.
- Current research chain: factors, confidence, risk gates, and signals completed.
- `FULL_FREEZE_V1`: 2 snapshots, 51 securities per snapshot, 102 frozen security states.
- Elapsed full-freeze interval: about 24 hours 25 minutes.
- Frozen states: 96 `DATA_INSUFFICIENT`, 2 `HOLD`, 4 `LIQUIDITY_TRAP`; all 102 were ineligible.
- Paper orders/fills/positions/outcomes: 0/0/0/0.

This is enough operational evidence for limited research use. It is explicitly insufficient for `PAPER_TRADING_READY`.

## Mandatory answers

1. IPKY remains `DATA_INSUFFICIENT` because factor aggregation has 3 available positively weighted factors and requires 4.
2. The blocking condition is `INSUFFICIENT_FACTOR_COVERAGE`; unavailable factors are Quality, Growth, Momentum, Dividend, Governance, Catalyst, and Balance-Sheet Risk. No hard gate fired.
3. These block an aggregate investment classification and portfolio admission, not `RESEARCH_READY`.
4. Yes. The residual-income valuation remains `AVAILABLE`, executable, fully denominated in nominal UZS, and independently reconciled.
5. Confidence is `LOW` because the valuation relies on 2023 financials at a 2026 valuation date and uses external/model-estimated beta, ERP, and country-risk inputs. These are supporting uncertainty, not missing mandatory inputs.
6. Yes, for IPKY, with explicit limitations and no recommendation.
7. Yes. A current end-to-end due cycle completed and all 17 monitored pipelines are healthy.
8. No. `RESEARCH_READY` does not require a positive or actionable signal.
9. No. Portfolio eligibility is a separate downstream standard.
10. No. Historical validation is required for strategy claims and higher maturity, not basic company research.
11. No. It is required for paper-trading maturity, not research readiness.
12. Yes, narrowly: `RESEARCH_READY — LIMITED MINIMUM-VIABLE COHORT (IPKY)`.
13. No launch-critical blocker remains for this limited research classification. Breadth and investment eligibility remain limited.
14. New data are required for ownership/free float, verified adjusted-return evidence, richer bank factors, and market-depth/execution evidence where public sources do not supply them.
15. Repeated prospective snapshots, elapsed outcomes, and observed no-fill/partial-fill evidence require time.
16. Backtest/model validation, paper execution evidence, wider issuer coverage, security controls, backups, alert delivery, and operating governance belong to higher tiers.

## Formal status

- `BUILD_STATUS`: `BUILD_COMPLETE_BUT_EVIDENCE_LIMITED`
- `RESEARCH_READY`: `PASS_LIMITED_IPKY_COHORT`
- `PAPER_TRADING_READY`: `FAIL`
- `LIMITED_CAPITAL_READY`: `FAIL`
- `PRODUCTION_READY`: `FAIL`

No investment gate or readiness criterion was weakened. No position, order, or recommendation was forced. Autonomous live trading remains disabled.
