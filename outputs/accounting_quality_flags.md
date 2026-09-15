# Phase 4 accounting-quality validation

Validation date: 2026-09-14  
Formula version: `fundamental-metrics/1.0.0`

The deterministic engine processed all five real Phase 3 documents. It stored 11 available metrics and 131 explicitly unavailable metric instances. Every result retains source-document and source-observation lineage.

## Real results

- AGMKP issuer: Gross Margin 69.971991%, Net Margin 33.660742%, and Net Debt 11,981,949,795 source units.
- QZSM: Gross Margin 25.587356%, Net Margin 24.000507%, and Net Debt 566,695,233 source units.
- UZTL: Gross Margin 35.986134%, Net Margin 5.620826%, and Net Debt 5,600,814,570 source units.
- IPKY bank: reported Assets 29,023,186,458 and Equity 4,660,152,457 source units.
- KASUP insurer: the required normalized premium, claims, expense, and solvency inputs were unavailable, so no insurance ratio was produced.

Absolute values deliberately say `SOURCE_UNIT_UNSPECIFIED` and have no currency because Phase 3 could not verify those metadata. Ratios only combine values from the same source document.

## Accounting-quality flags

| Flag | Result across five documents |
|---|---|
| `RECEIVABLES_GROWING_FASTER_THAN_REVENUE` | 5 unavailable |
| `POOR_CASH_CONVERSION` | 5 unavailable |
| `RAPID_DEBT_GROWTH` | 5 unavailable |
| `INVENTORY_ANOMALY` | 5 unavailable |

No flag was triggered because the required cash-flow and/or compatible prior-period observations do not exist in the approved normalized dataset. This is `DATA INSUFFICIENT`, not a clean accounting-quality conclusion.

## Historical and TTM coverage

Each real issuer currently has only one approved report. Consequently, YoY, 3Y, 5Y, and TTM metrics are unavailable. The code supports them only when exact compatible periods and known matching metadata exist; it will reject gaps, overlaps, non-quarterly periods, and metadata mismatches.

## Important limitations

Issuer sector fields remain mostly unknown. Bank and insurance routing is supported by explicit Openinfo report categories; mining classification was not inferred from names or tickers. Ambiguous duplicate canonical inputs are treated as missing. No valuation, factor score, recommendation, or investment signal is generated.
