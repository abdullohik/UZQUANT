# Market-Wide Terminal Prototype Report

Generated: 2026-09-29
Baseline: `5f0fac8fca609bfa37028340665501e3b73984b3`

## Outcome

The terminal now uses the latest complete official RSE capture as its current-equity boundary. It exposes exactly **73 current equities** across **52 issuers**: **51 common** and **22 preferred**. Seven canonical historical-only securities remain stored and are explicitly excluded from the current screener. Bonds never enter the equity API.

The prior per-security API query loop was replaced with fixed-count bulk retrieval. The API supplies market observations, observed-endpoint 1M/3M performance where history supports it, all ten stored factors, valuation state and method, confidence, liquidity, research state, component coverage, and machine-readable blocker objects (`code`, approved `taxonomy`, `evidence`). The browser performs display filtering/sorting only; it does not calculate research outputs.

## Current production coverage

| Measure | Count |
| --- | ---: |
| Current equities | 73 |
| Current issuers | 52 |
| Securities with raw market observations | 50 |
| Issuers represented by verified financial documents | 16 securities |
| Securities with available normalized fundamentals | 14 |
| Securities with verified class-share evidence | 40 |
| Securities with rights records | 4 |
| Securities with ownership records | 2 |
| Securities with 4+ factors | 5 |
| Executable valuations | 1 (IPKY) |

Top blocker categories are **PUBLIC_DATA_NOT_YET_COLLECTED (59)** and **METADATA_GAP (14)**. This reflects the actual ceiling: 57 current securities have no verified financial document, 14 are led by unresolved reporting perimeter, one by insufficient credible peers, and one by missing market history.

## Terminal surfaces

- MARKET: breadth, observed turnover, freshness, coverage, health and backfill queue.
- SCREENER: 73 rows; required market, valuation, ten-factor, confidence, state and blocker columns; documented exploration views.
- RESEARCH: raw market history, fundamentals, reports, factors and limitations.
- VALUATION: every stored method record and model attempt, including exact rejection reasons; assumptions are read-only.
- FACTORS: market-wide matrix for all ten factors.
- EVIDENCE: exact signal/factor/financial/assumption lineage.
- COVERAGE: issuer grouping, component coverage and blocker drill-down.
- SYSTEM: pipelines, source freshness, alerts, validation and backfill state.

## Production refresh

A restricted-network attempt failed closed at the RSE route after three bounded retries and propagated staleness correctly. The authorized network run then completed normally: **17/17 pipelines HEALTHY**. It processed 70 security-master items, 133 market-data items, 20 financial-document items and all downstream stages. No manual database edit was used.

## Frozen-result verification

- IPKY: `REDUCE`
- UZTL: `HOLD`
- AGMK and AGMKP: `LIQUIDITY_TRAP`
- Executable valuation securities: IPKY only
- No methodology, factor weight, minimum factor count, confidence threshold, gate, or readiness threshold changed.

## Known limitations

Displayed coverage remains evidence-limited. An observed endpoint return is not a continuous return series and remains unavailable when an adequate prior observation does not exist. The frontend does not imply current market activity for old observations. Most securities still lack valuation-ready public evidence.
