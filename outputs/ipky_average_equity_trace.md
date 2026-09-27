# IPKY Average-Equity Trace

Assessment date: 2026-09-28

## Result

Average equity is legitimately computable for 2023. The two observations are adjacent annual periods from the same audited consolidated IFRS document, both normalized to UZS with the same unit and perimeter.

| Role | Period | Value (UZS) | Immutable version | Raw evidence location |
|---|---:|---:|---|---|
| Opening equity | 2022-12-31 | 2,133,021,000,000 | `b7da6692-c156-4d54-9839-425306c0efef` | `pdf:audited-statement/Equity/COMPARATIVE` |
| Closing equity | 2023-12-31 | 2,817,695,000,000 | `ede43c2c-5eba-48a8-b899-50ccc968a5ba` | `pdf:audited-statement/Equity/CURRENT` |

`Average Equity = (2,133,021,000,000 + 2,817,695,000,000) / 2 = 2,475,358,000,000 UZS`.

The source document is `7c1e86df-7f87-57b0-9d62-3f92b0f7634a`, published 2024-12-11. Both values use parser `audited-pdf-evidence/1.1.0`, taxonomy `financial-taxonomy/1.0.0`, normalization `million-uzs-explicit/1.0.0`, and were known no later than the 2026-09-28 calculation date.

The engine rejects construction when periods are not adjacent annual dates or when currency, unit, reporting perimeter, accounting standard, or audit status differ. It does not substitute a missing opening balance.

## Related 2022 valuation input

The valuation's two-year normalized ROE also uses audited opening equity at 2021-12-31: 1,491,673,000,000 UZS, immutable version `f0fa4084-dcb6-4f63-9ad8-064a20aa21d4`, raw location `pdf:audited-statement/Equity/OPENING_COMPARATIVE`. It is now a first-class observation rather than a code literal.
