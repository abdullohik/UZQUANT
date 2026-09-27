# IPKY Complete Company Research View

Research date: 2026-09-28 Asia/Tashkent  
Issuer: AITB “Ipak Yo'li”  
Security: IPKY common equity, nominal currency UZS  
Research conclusion: **DATA_INSUFFICIENT / NO ACTION**

This is a reproducible company-research output, not personalized advice or an executable order.

## Evidence completeness

| Item | Classification | Current evidence / limitation |
|---|---|---|
| Identity | VERIFIED | Stable security and issuer IDs; official ticker linkage |
| Security class | VERIFIED | Common equity; no preferred-right prerequisite applies |
| Market price | VERIFIED | Observed close 211 UZS on 2026-09-25 |
| Shares outstanding | VERIFIED | 60,239,945,264 common shares; nominal value 10 UZS; official RSE issue page |
| Financial period | VERIFIED | Audited IFRS 2023 with 2022 comparatives |
| Reporting perimeter | VERIFIED | Consolidated for valuation inputs |
| Currency and unit | VERIFIED | UZS; source statement in millions converted deterministically to UZS |
| Book equity | VERIFIED | 2.817695tn UZS (2023); 2.133021tn UZS (2022) |
| Net income | VERIFIED | 731.342bn UZS (2023); 522.935bn UZS (2022) |
| ROE | VERIFIED, SOURCE-DERIVED | 29.5449% (2023), 28.8540% (2022), normalized base 29.1995% |
| Capital information | PARTIAL | Equity/share capital available; regulatory capital adequacy is unavailable |
| Dividends | UNKNOWN | No date-compatible, class-specific scored dividend history |
| Ownership/free float | UNKNOWN | No verified current ownership position stored |
| Governance | UNKNOWN | No adverse event is stored, but absence is not a positive-governance finding |
| Liquidity | PARTIAL / RESEARCHABLE | Descriptive history exists; execution depth, spread, free float, and ownership concentration are unavailable |
| Valuation | VERIFIED MODEL OUTPUT | Residual income available and independently reconciled; confidence LOW |
| Macro inputs | VERIFIED/PARTIAL | Official nominal UZS CBU curve and inflation target; external beta/ERP/CRP remain model inputs |
| Factor inputs | PARTIAL | 3 of 10 factors available; minimum 4 required to aggregate |
| Material risks | VERIFIED AS LIMITATIONS | Old financial period, assumption sensitivity, ownership/governance opacity, incomplete factor coverage, and limited market microstructure evidence |

## Current market state

- Raw observed history: 73 dates from 2024-09-27 through 2026-09-25.
- Latest close: 211 UZS; latest reported share volume: 23,592.
- Source-date trading frequency: 1.0; zero-trade ratio: 0.0. These use source-reported dates and must not be interpreted as a complete exchange-calendar frequency.
- Average/median daily share volume: 30,948 / 17,014.
- Average/median daily trading value: about 3.023m / 1.934m UZS.
- Days since last trade at the 2026-09-28 quality calculation: 3.

The existing standardized 10,000-share, 10% participation assessment is `INVESTABLE` with `LOW` confidence and an estimated 3.17-day liquidation horizon. Its uncertainty band is deliberately wide because bid/ask spread, book depth, free float, and ownership concentration are unknown. This supports `LIQUIDITY_RESEARCHABLE`; it does not establish `CAPACITY_VALIDATED` or portfolio eligibility.

## Financial and valuation view

The valuation uses only the audited consolidated IFRS record and its comparative figures. It does not mix the later local-statutory, unknown-perimeter data into the residual-income calculation.

| Scenario | ROE | Cost of equity | Growth | Value/share |
|---|---:|---:|---:|---:|
| Bear | 28.8540% | 24.2410% | 4.0% | 57.6099 UZS |
| Base | 29.1995% | 22.2410% | 5.0% | 66.0940 UZS |
| Bull | 29.5449% | 20.2410% | 6.0% | 78.3093 UZS |

The model is nominal UZS throughout. The official CBU curve is a reference input, not WACC. Cost of equity is a documented model estimate built from that curve plus external country-risk, ERP, and bank-beta evidence. Independent recalculation matches stored values exactly (`0E-26`).

Valuation confidence is `LOW` because the audited input year is 2023 while the valuation date is 2026 and because beta/ERP/country-risk inputs are externally sourced estimates. These are not missing mandatory model inputs, so the valuation correctly stays `AVAILABLE`.

At the observed 211 UZS price, base-value upside is -68.6758%; the transparent valuation factor is therefore capped at 0. This is thesis-invalidating evidence for undervaluation under the current residual-income assumptions, not a sell recommendation.

## Macro context

The nominal UZS government curve is stored point-in-time from the official CBU API. The reference 10-year continuously compounded zero rate for 2026-09-23 is 16.96054015902%. The residual-income engine applies nominal UZS consistency and records the curve date and assumption provenance. Macro context informs risk and assumptions; it does not generate a signal independently.

## Thesis evidence

Supporting evidence:

- Audited consolidated IFRS equity and net income are preserved with source locations and exact units.
- Source-derived 2022/2023 ROE is high relative to the modeled cost of equity.
- Verified class shares enable a per-share valuation.
- The valuation is independently reproducible.
- Current raw market observations and descriptive liquidity statistics exist.

Invalidating or confidence-limiting evidence:

- All valuation scenarios are below the current observed market price.
- The most recent audited consolidated valuation year is stale.
- Ownership/free float and affirmative governance evidence are unavailable.
- Bank quality, growth, and balance-sheet-risk factor metrics are not currently supported in the scoring record.
- No verified corporate-action-adjusted series supports momentum.
- Dividend and catalyst factors are unavailable.
- Order-book depth and spread are unavailable, preventing precise capacity claims.
- Phase 14 remains `UNRELIABLE — INSUFFICIENT EVIDENCE`; no strategy-performance inference is permitted.

## Final research state

`DATA_INSUFFICIENT / NO ACTION` is the correct output. The report is usable for evidence review and model inspection, but it does not establish investment eligibility, portfolio eligibility, or executable capacity.
