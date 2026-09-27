# IPKY Research Gate Trace

As of: 2026-09-28 Asia/Tashkent  
Security ID: `9922a46f-208e-50f4-a367-4930fa116e60`  
Latest signal: `DATA_INSUFFICIENT`, confidence `58.75`, triggered hard gates `[]`

## Decision path

| Layer/gate | Current value | Requirement | Result | Evidence / reason |
|---|---:|---:|---|---|
| Identity | IPKY / common equity | Verified security | PASS | RSE security master and effective identifier evidence |
| Source freshness | 17/17 monitored pipelines healthy | No failed/stale dependency | PASS | `pipeline_health`; normal cycle 2026-09-27 UTC |
| Market price | 211 UZS, 2026-09-25 close | Positive observed price | PASS | `market_observations` ID `523f036c-fed5-5aa3-9912-3da7bff2475c` |
| Market history | 73 observations/dates, 2024-09-27 to 2026-09-25 | 60 observations for weak-history penalty | PASS for count | Raw history is sufficient for description, not an adjusted momentum series |
| Shares | 60,239,945,264 common shares | Verified class shares | PASS | Official RSE issue record; verified 2026-09-14 |
| Financial inputs | Audited consolidated IFRS, 2022/2023 comparatives | Perimeter/unit/currency resolved | PASS | Document `7c1e86df-7f87-57b0-9d62-3f92b0f7634a`; UZS; source stated million-UZS basis |
| Valuation | Residual income `AVAILABLE` | Mandatory inputs complete | PASS | Bear 57.6099; base 66.0940; bull 78.3093 UZS/share |
| Valuation confidence | LOW | No minimum required for valuation availability | PASS WITH LIMITATION | Stale financial year and external/model-estimated beta/ERP/CRP |
| Valuation factor | 0 | Available valuation and price | AVAILABLE | Base value implies -68.6758% versus 211 UZS; transformation is capped at 0 |
| Liquidity | INVESTABLE; confidence LOW | Not `LIQUIDITY_TRAP`/`UNASSESSABLE` | PASS WITH LIMITATION | 10,000-share research case, 10% participation; no hard flags; depth/spread/free float unknown |
| Data quality | 90 | Critical gate if below 50 | PASS | Only scored penalty is unknown ownership (-10) |
| Overall confidence | 58.75 | Below 50 only constrains BUY/STRONG_BUY | PASS | Not the cause of `DATA_INSUFFICIENT` |
| Preferred rights | Not applicable | High confidence only for preferred class | NOT REQUIRED | IPKY is common; `rights_unknown` is false |
| Governance hard gate | No severe event stored | Severe issue would gate | PASS | No governance event was asserted; absence is not evidence of good governance |
| Stale-price gate | False | No extreme staleness/unreliable-price flag | PASS | No applicable liquidity hard flag |
| Factor coverage | 3 available | Minimum 4 positively weighted factors | **FAIL** | Available: Valuation, Liquidity, Data Quality |
| Aggregate attractiveness | NULL | Requires factor coverage | **BLOCKED** | `INSUFFICIENT_FACTOR_COVERAGE` |
| Tentative signal | NULL | Requires aggregate attractiveness | **BLOCKED** | No recommendation state can be formed |
| Final state | DATA_INSUFFICIENT | Fail closed when tentative state is null | CORRECT | `apply_risk_gates`; no hard gate needed to produce this result |

## Factor inventory

| Factor | Status | Score | Exact reason when unavailable |
|---|---|---:|---|
| Valuation | AVAILABLE | 0 | Base value 66.094 versus observed price 211 |
| Liquidity | AVAILABLE | 60 | `INVESTABLE`, capped by LOW liquidity confidence |
| Data Quality | AVAILABLE | 90 | Unknown ownership is the sole scored penalty |
| Quality | UNAVAILABLE | — | `NO_SUPPORTED_FUNDAMENTAL_METRIC` |
| Growth | UNAVAILABLE | — | `NO_SUPPORTED_FUNDAMENTAL_METRIC` |
| Balance-Sheet Risk | UNAVAILABLE | — | `NO_SUPPORTED_FUNDAMENTAL_METRIC` |
| Momentum | UNAVAILABLE | — | `NO_VERIFIED_CORPORATE_ACTION_ADJUSTED_RETURN_SERIES` |
| Dividend | UNAVAILABLE | — | `NO_DATE_COMPATIBLE_DIVIDEND_SCORE` |
| Governance | UNAVAILABLE | — | `NO_DIRECTIONALLY_SUPPORTED_GOVERNANCE_EVIDENCE` |
| Catalyst | UNAVAILABLE | — | `NO_DIRECTIONALLY_SUPPORTED_CATALYST` |

The minimum-factor rule is an investment-ranking requirement. It is not one of the eight `RESEARCH_READY` requirements. It was not changed.

## Confidence construction

| Component | Input | Weight | Contribution |
|---|---:|---:|---:|
| Data quality | 90 | 30% | 27.00 |
| Reporting history | 100 | 15% | 15.00 |
| Liquidity evidence | 25 | 15% | 3.75 |
| Ownership transparency | 0 | 10% | 0.00 |
| Share-right certainty | 0 | 10% | 0.00 |
| Valuation stability/availability | 100 | 10% | 10.00 |
| Model coverage | 30 | 10% | 3.00 |
| **Total** | | | **58.75** |

This signal confidence is distinct from the valuation record's `LOW` confidence. Neither converts an otherwise complete valuation to `VALUATION_INSUFFICIENT`.
