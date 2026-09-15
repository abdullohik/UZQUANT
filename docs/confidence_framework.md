# UZQUANT confidence framework

Confidence is separate from Investment Attractiveness and cannot be increased by estimated upside.

## Evidence components

Confidence is a transparent 0–100 weighted result:

| Component | Weight |
|---|---:|
| Data Quality | 30% |
| Reporting history | 15% |
| Liquidity evidence | 15% |
| Ownership transparency | 10% |
| Share-right certainty | 10% |
| Valuation stability | 10% |
| Model coverage | 10% |

Inputs must themselves be 0–100. In the real run, fewer than three compatible reports gives reporting-history evidence 0; LOW Phase 7 liquidity confidence gives 25; unknown exact ownership and non-HIGH rights give 0; unavailable valuation gives valuation stability 0; model coverage is ten points per available factor. This conservative mapping is versioned and deterministic.

## Data Quality Score

Data Quality begins at 100 and subtracts documented evidence penalties:

- missing statements: 30; otherwise fewer than three documents: 15;
- late reports: 5 each, capped at 15;
- conflicting values: 10 each, capped at 20;
- OCR dependence: 5;
- unverified shares outstanding: 15;
- fewer than 60 market observations: 15;
- unknown exact ownership: 10;
- unknown/non-HIGH share rights: 10;
- unavailable valuation: 5.

The raw evidence and penalty list are stored alongside the score. The mapping is an analytical policy, not source data. A score below 50 is a critical gate.

## Current evidence

All seven real cases have Data Quality 30. After the Phase 9 versioned Catalyst integration, overall Confidence is 14.75–15.75 because event-covered securities have one additional model component; the event does not improve source-data quality. Confidence remains driven by short financial and market history, unverified total shares, unknown exact ownership/rights and unavailable valuation—not by estimated upside.
