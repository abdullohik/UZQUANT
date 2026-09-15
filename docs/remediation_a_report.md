# Remediation Phase A report

## Outcome

Remediation A materially improved real financial coverage and repaired two structural pipeline defects: share capital is now effective-dated and independently verifiable, and scoring no longer hardcodes shares as unavailable or ignores all stored fundamental metrics. The production result remains conservative: no target valuation is ready and all signals remain `DATA_INSUFFICIENT`.

No dashboard, backtest, validation classification, portfolio, threshold, or risk gate was changed. Phases 13–15 were not rerun.

## Implemented work

- Added `share_capital_observations` with issuer total versus class-specific shares, effective/disclosure dates, source lineage, and `VERIFIED`, `PARTIAL`, `CONFLICT`, or `UNAVAILABLE` status.
- Added `source_coverage_audits` and stored the failed historical RSE access attempt instead of bypassing the source.
- Added `security_rights_assessments` with the required `RIGHTS_VERIFIED`, `RIGHTS_PARTIAL`, and `RIGHTS_UNAVAILABLE` states.
- Expanded the verified Openinfo report set from 5 to 11 reports. All five target issuers now have multiple stored reports.
- Persisted explicit document currency, accounting-standard, audit-status, and perimeter metadata where the source evidence supports it; uncertain units and perimeters remain visibly unknown.
- Expanded the multilingual taxonomy for bank and insurance concepts and D&A.
- Replaced the valuation assembler's unconditional shares failure with an as-of query of verified, class-specific share capital. It now stores its available concepts and exact missing inputs.
- Connected stored sector-appropriate fundamentals to Quality, Growth, and Balance-Sheet Risk factor construction. The minimum four-factor rule and data-quality threshold of 50 remain unchanged.

## Real sources used

All production documents came from the official Openinfo corporate disclosure portal:

- AGMK annual 2023: `https://openinfo.uz/en/reports/jsc/annual/5218`
- AGMK Q1 2026: `https://openinfo.uz/en/reports/jsc/quarter/18364`
- Kafolat annual 2023: `https://openinfo.uz/en/reports/insurance/annual/168`
- Kafolat Q2 2023: `https://openinfo.uz/en/reports/insurance/quarter/361`
- Kafolat Q3 2025: `https://openinfo.uz/en/reports/insurance/quarter/692`
- Ipoteka Bank annual 2022: `https://openinfo.uz/en/reports/bank/annual/296`
- Ipoteka Bank Q1 2026: `https://openinfo.uz/en/reports/bank/quarter/1257`
- Uzbektelecom annual 2024: `https://openinfo.uz/en/reports/jsc/annual/5548`
- Uzbektelecom annual 2025: `https://openinfo.uz/en/reports/jsc/annual/6116`
- Qizilqumsement annual 2023: `https://openinfo.uz/en/reports/jsc/annual/5176`
- Qizilqumsement Q1 2026: `https://openinfo.uz/en/reports/jsc/quarter/18437`

The official RSE dated-results URL `https://uzse.uz/trade_results?date=02.02.2018` returned HTTP 403 to a compliant automated request on 2026-09-15. No evasion or unofficial substitute was used.

## Before and after

| Measure | Before | After |
|---|---:|---:|
| Financial documents | 5 | 11 |
| Target issuers with at least two reports | 0 | 5 |
| Normalized observations | 88 | 207 |
| Canonical concepts observed | not previously reported | 27 |
| Fundamental metric records | 142 | 303 |
| Available fundamental metrics | 9 | 20 |
| Effective-dated share-capital assessments | 0 | 5 |
| Verified class-specific share counts | 0 | 0 |
| Explicit preferred-rights assessments | 0 | 2 `RIGHTS_PARTIAL` |
| Real market observations / dates | 126 / 18 | 126 / 18 |
| Available target valuations | 0 | 0 |
| Latest non-`DATA_INSUFFICIENT` signals | 0 | 0 |

## Target production results

- AGMKP: two reports, 42 observations, six available metrics, Quality factor now available. DCF remains blocked by class shares, OCF, CapEx, D&A, unit, perimeter, and incomplete preferred rights.
- KASUP: three reports and 72 observations. The historical disclosure provides only an issuer-total security count, so preferred-class shares remain unavailable. Insurance metrics remain insufficient and rights are partial.
- IPKY: two reports and nine observations. Assets and Equity metrics remain available; class shares, consistent source unit, and reporting perimeter block P/B.
- UZTL: two annual reports, 42 observations, six available metrics, and an available Quality factor. DCF inputs remain incomplete.
- QZSM: two reports, 42 observations, six available metrics, and an available Quality factor. DCF inputs remain incomplete.

## What remains genuinely incomplete

### Fixable with current verified sources

- Parse and validate attached audited PDFs/XLS files where they explicitly state units, reporting perimeter, cash-flow lines, and sector-specific concepts.
- Extend deterministic report-table recognition for the annual bank and insurance templates.
- Add class-share counts if an already-linked issue document or charter explicitly supplies the class denominator.
- Ingest more ownership, dividends, and corporate events from already verified Openinfo disclosures after exact issuer/security resolution.

### Requires a new legitimate or newly accessible source

- Complete class-specific shares outstanding for all five securities.
- Full authoritative preferred-share legal rights for AGMKP and KASUP.
- Longitudinal exchange trading history beyond the rolling 18-date security pages while the official dated endpoint blocks automation.
- Exact free float and ownership history where issuer disclosures provide only threshold relationships.

### Not promoted because evidence is insufficient

- The KASUP issuer-total count was deliberately stored as `PARTIAL`, never as preferred shares outstanding.
- A paid preferred dividend demonstrates an event, not the complete legal rights of a preferred class; AGMKP and KASUP remain `RIGHTS_PARTIAL`.
- Currency was recorded as UZS for the local statutory tables, but source units remain unspecified wherever the page did not explicitly state them.
- No valuation assumptions, peer multiples, country-risk inputs, cash-flow values, ownership percentages, free float, or market observations were fabricated.

## Tests and production rerun

- `python3 -m pytest -q`: 116 passed.
- Real Openinfo ingestion: 11/11 documents succeeded; 1,300 raw table rows and 207 normalized observations processed.
- Fundamentals recalculated for 11 documents: 20 available and 283 unavailable metric records.
- Valuation assembler rerun for five targets: 0 available, 5 `VALUATION_INSUFFICIENT`.
- Liquidity rerun for seven market-covered securities; existing low-confidence states were retained from real observations.
- Ranking rerun for seven securities: all remain `DATA_INSUFFICIENT`; no gate was weakened.

## Migrations and production files

Migrations: `020_remediation_a.sql`, `021_rights_assessments.sql`.

Production modules changed or added: `uzquant/remediation.py`, `uzquant/financial_documents.py`, `uzquant/financial_taxonomy.py`, `uzquant/valuation.py`, `uzquant/scoring.py`, and `uzquant/cli.py`.

The exact target matrix is in `outputs/remediation_dependency_matrix.md`.

