# Remediation Phase B — Valuation Readiness Closure

## Outcome

Remediation B closed the class-share-count and issuer-assignment software blockers, but produced no validated valuation. This is the accuracy-preserving result: the remaining gaps are unresolved financial scale/perimeter, incomplete normalized model inputs, unavailable defensible peer/discount-rate assumptions, and (for AGMKP and KASUP) incomplete preferred-share legal rights.

No Phase 13, 14, or 15 process was run. No threshold, confidence rule, liquidity gate, factor minimum, or `DATA_INSUFFICIENT` rule was changed.

## Exact pre-change blocker audit

| Security | Routed model family | Mandatory evidence present | Pre-change failure |
|---|---|---|---|
| AGMKP | Mining scenario DCF / relative | price, issuer financial rows | no verified class shares; source unit and perimeter unknown; OCF, CapEx and valid D&A expense absent; preferred rights incomplete; no sourced discount/peer assumptions |
| KASUP | Insurance P/B, P/E, residual income, DDM | price; misassigned reports only | no verified preferred shares; Kafolat reports were incorrectly attached to Kapital Sug'urta; preferred rights incomplete; no defensible valuation assumptions |
| IPKY | Bank P/B, P/TBV, P/E, residual income, DDM | price; misassigned reports only | no verified shares; Ipoteka Bank reports were incorrectly attached to Ipak Yo'li; no valid bank inputs or assumptions |
| UZTL | Industrial DCF / relative | price, issuer financial rows | no verified shares; source unit and perimeter unknown; OCF, CapEx and D&A absent; no sourced discount/peer assumptions |
| QZSM | Industrial DCF / relative | price, issuer financial rows | no verified shares; source unit and perimeter unknown; OCF, CapEx and D&A absent; no sourced discount/peer assumptions |

The audit distinguishes observed market inputs from estimated or user-configurable assumptions. DCF methods require sourceable discount-rate inputs; relative methods require a documented peer set and multiple. Neither is silently invented. Country risk therefore blocks DCF, but does not automatically block P/B or P/E; those methods are rejected for their own missing evidence.

## Implemented corrections

- Parsed official RSE security-detail snapshots into effective-dated, class-specific share observations with source-document lineage. All five targets now have a verified class count as observed on 2026-09-14.
- Reconciled class, ticker, ISIN, quantity, nominal value, and source security-master identity. No target conflict was detected.
- Corrected the production Openinfo report list to Ipak Yo'li report IDs 289, 354, 387 and Kapital Sug'urta report IDs 39, 208, 650.
- Preserved, but quarantined, five Phase A reports belonging to Ipoteka Bank or Kafolat. They no longer feed metrics or valuations.
- Added persistent financial-document entity checks, metadata-evidence support, and per-model execution/rejection records.
- Added an explicit financial-scale conversion validator for UZS, thousand UZS, million UZS, and billion UZS. Unknown scales are rejected.
- Added a real point-in-time valuation input assembly path which filters quarantined documents, retrieves effective-dated shares and rights, attempts every sector-permitted method, and records each rejection.
- Connected an available validated valuation to the Valuation factor path. No target reached that state, so no artificial factor was generated.

## Source evidence and limitations

The share counts come from stored raw RSE pages (`uzse.uz`) and are snapshots as of the observation date; they are not represented as original issuance dates. Correct issuer reports were retrieved from the official Openinfo disclosure portal. Portal HTML was stored immutably.

Openinfo spreadsheet headers reviewed during remediation explicitly describe statement values as thousand soums for inspected templates. That fact was sufficient to implement and test scaling, but the production observations were not rewritten because spreadsheet files and their exact document-to-observation lineage were not yet ingested into the immutable raw-document store. Scale therefore remains unresolved in production rather than being asserted from analyst inspection alone.

The legal charters linked by RSE were located for AGMKP and KASUP, but the existing source corpus does not yet contain a complete, machine-verified extraction of dividend, cumulative, voting, liquidation, participation, conversion, and redemption terms. Historical dividends are not treated as legal rights.

## Before and after

| Measure | Before | After |
|---|---:|---:|
| Financial documents | 11 | 17 |
| Normalized observations | 207 | 279 |
| Available fundamental metrics | 20 | 18 |
| Verified target class-share counts | 0 | 5 |
| Valuation-ready targets | 0 | 0 |
| Completed valuations | 0 | 0 |
| Target attractiveness scores | 0 | 0 |
| Target final signals | 5 DATA_INSUFFICIENT | 5 DATA_INSUFFICIENT |

The available-metric count fell because five wrongly assigned reports were excluded; this is a correctness improvement, not data loss. Current factor coverage is AGMKP 4, KASUP 2, IPKY 2, UZTL 4, and QZSM 3 available components. The four-factor aggregation minimum was not relaxed; raw availability alone does not make a defensible attractiveness score.

## Manual reconciliation

No target produced a valuation, so a fair-value reconciliation was not applicable. The share-capital arithmetic was independently reconciled from source quantity × nominal value. Examples: QZSM `447,516,900 × 1,570 = 702,601,533,000 UZS`; Kapital Sug'urta's two displayed classes total 8 trillion shares and reconcile to 80 billion UZS at 0.01 UZS nominal value. Decimal arithmetic is exact; no floating-point tolerance was needed.

## Blocker classification

### Fixed software blockers

- missing effective-dated class-share integration;
- hardcoded unavailable class shares despite exchange evidence;
- wrong bank/insurance issuer routing caused by misassigned reports;
- valuation runner attempting only a primary label without persistent method-level rejection evidence;
- factor path hardcoding Valuation unavailable even if a validated valuation exists.

### Fixed data-ingestion blockers

- official IPKY and KASUP issuer reports are now retrieved and stored;
- five unrelated financial reports are explicitly quarantined;
- exchange share quantities and nominal values are stored with provenance.

### Remaining source-dependent blockers

- complete authoritative preferred-right provisions for AGMKP and KASUP;
- production-ingested evidence for statement scale and reporting perimeter;
- defensible peer sets/multiples for relative valuation;
- sourceable country-risk and discount-rate components for DCF/residual-income methods;
- verified ownership for four targets and limited ownership coverage for UZTL.

### Remaining fundamental limitations

- insufficient historical market depth and low liquidity confidence;
- incomplete cash-flow concepts for industrial DCF;
- correct IPKY reports did not yield normalized bank concepts with the current deterministic parser;
- KASUP lacks Equity and Net Income in the normalized usable concept set;
- all targets remain below the evidentiary standard for a validated valuation.

## Verification

The complete suite passed: **124 tests passed**. Coverage includes effective dates, class parsing, unknown-unit rejection, thousand/million scaling, currency and perimeter checks, sector routing, preferred-right gating, and preservation of the critical data-quality risk gate.

