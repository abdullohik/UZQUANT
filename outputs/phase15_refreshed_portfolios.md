# Phase 15 Refreshed Portfolios

## Summary

- Runs created: **9**
- Styles: **CONSERVATIVE, BALANCED, HIGH_CONVICTION**
- AUM scenarios: **UZS 20 million, UZS 1 billion, UZS 20 billion**
- Eligible securities: **0**
- Positions created: **0**
- Cash weight: **100% in all 9 runs**
- Portfolio model: `transparent-portfolio/1.1.0`
- Phase 14 input: `UNRELIABLE / C_INSUFFICIENT_HISTORY`

| Style | UZS 20m | UZS 1bn | UZS 20bn |
|---|---:|---:|---:|
| CONSERVATIVE cash | 100% | 100% | 100% |
| BALANCED cash | 100% | 100% | 100% |
| HIGH_CONVICTION cash | 100% | 100% | 100% |

## Security-level admission blockers

| Ticker | Current signal | Main binding blockers |
|---|---|---|
| AGMK | LIQUIDITY_TRAP | model not validated; signal ineligible; low confidence; valuation/capacity unavailable; liquidation horizon; incomplete risk, macro, and factor evidence |
| AGMKP | DATA_INSUFFICIENT | model not validated; signal ineligible; low confidence; valuation/capacity unavailable; liquidation horizon; incomplete risk, macro, and factor evidence |
| IPKY | DATA_INSUFFICIENT | model not validated; signal ineligible; low confidence; valuation/capacity unavailable; incomplete risk, macro, and factor evidence |
| KASU | DATA_INSUFFICIENT | model not validated; signal ineligible; low confidence; valuation/capacity unavailable; incomplete risk, macro, and factor evidence |
| KASUP | DATA_INSUFFICIENT | model not validated; signal ineligible; low confidence; valuation/capacity unavailable; incomplete risk, macro, and factor evidence |
| QZSM | DATA_INSUFFICIENT | model not validated; signal ineligible; low confidence; valuation/capacity unavailable; incomplete risk, macro, and factor evidence |
| UZTL | HOLD | model not validated; signal ineligible; low confidence; valuation/capacity unavailable; incomplete risk, macro, and factor evidence |

Sector, concentration, correlation, capacity-weight, and portfolio-risk constraints do not become the binding numeric allocation limit because every candidate fails the admission gate first. They remain implemented and tested for future eligible candidates.

## Stored output

Each refreshed run is linked to validation run `61726e93-8bc4-49c6-b8f8-e1905479de98`. Portfolio metrics were stored as `UNAVAILABLE / NO_ELIGIBLE_POSITIONS`; no zero-position portfolio was given fabricated exposure or risk statistics.
