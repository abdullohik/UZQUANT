# Remediation B Dependency Matrix

Production snapshot: 2026-09-15. Values are research-system outputs, not investment advice.

| Field | AGMKP | KASUP | IPKY | UZTL | QZSM |
|---|---|---|---|---|---|
| Security identity | Verified | Verified | Verified | Verified | Verified |
| Share class | Preferred | Preferred | Common | Common | Common |
| Shares outstanding | 8,998,232 | 1,875,000,000,000 | 60,239,945,264 | 818,339,529 | 447,516,900 |
| Shares confidence | VERIFIED RSE snapshot, effective/known 2026-09-14 | VERIFIED RSE snapshot, effective/known 2026-09-14 | VERIFIED RSE snapshot, effective/known 2026-09-14 | VERIFIED RSE snapshot, effective/known 2026-09-14 | VERIFIED RSE snapshot, effective/known 2026-09-14 |
| Price | 24,001 UZS | 0.18 UZS | 185.02 UZS | 17,500 UZS | 1,469 UZS |
| Financial periods | 2023-12-31 to 2026-03-31 | 2017-12-31 to 2025-06-30 | 2022-12-31 to 2024-12-31 | 2024-12-31 to 2025-12-31 | 2023-12-31 to 2026-03-31 |
| Audited report available | Yes (1) | Yes (2) | Yes (3) | Yes (2) | Yes (1) |
| Currency verified | UZS at document level | UZS at document level | UZS at document level | UZS at document level | UZS at document level |
| Units verified | No—production observation lineage unresolved | No—production observation lineage unresolved | No normalized usable observations | No—production observation lineage unresolved | No—production observation lineage unresolved |
| Reporting perimeter verified | No | No | No | No | No |
| Required sector metrics | DCF cash-flow inputs missing | Equity/Net Income missing | normalized bank inputs missing | DCF cash-flow inputs missing | DCF cash-flow inputs missing |
| Preferred rights | RIGHTS_PARTIAL; governing economics incomplete | RIGHTS_PARTIAL; governing economics incomplete | N/A | N/A | N/A |
| Ownership | Missing | Missing | Missing | Partial (2 rows) | Missing |
| Valuation model(s) attempted | Mining scenario DCF; Relative | P/B; P/E; ROE-adjusted P/B; Residual Income; DDM | P/B; P/TBV; P/E; Residual Income; DDM | Industrial DCF; Relative | Industrial DCF; Relative |
| Valuation-ready | No | No | No | No | No |
| Bear / Base / Bull | N/A / N/A / N/A | N/A / N/A / N/A | N/A / N/A / N/A | N/A / N/A / N/A | N/A / N/A / N/A |
| Valuation confidence | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE | UNAVAILABLE |
| Liquidity state | LIQUIDITY_TRAP | INVESTABLE (LOW confidence) | INVESTABLE (LOW confidence) | INVESTABLE (LOW confidence) | LIMITED_LIQUIDITY (LOW confidence) |
| Available factor count | 4 | 2 | 2 | 4 | 3 |
| Attractiveness score | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable |
| Confidence | 21.25 | 38.75 | 38.75 | 21.25 | 20.25 |
| Risk gates | Critical data quality; critical liquidity; unknown rights | Unknown rights | None, but insufficient factor coverage | Critical data quality | Critical data quality |
| Signal | DATA_INSUFFICIENT | DATA_INSUFFICIENT | DATA_INSUFFICIENT | DATA_INSUFFICIENT | DATA_INSUFFICIENT |
| Remaining blocker | unit/perimeter; DCF inputs/assumptions; rights; liquidity | unit/perimeter; normalized equity/earnings; peer/cost-of-equity assumptions; rights | parser normalization; perimeter; peer/cost-of-equity assumptions | unit/perimeter; DCF inputs/assumptions | unit/perimeter; DCF inputs/assumptions |

Every model rejection is stored in `valuation_model_attempts`, including missing inputs, failed validations, reason, source record IDs, and model version. No rejected method silently falls back to a weaker method.
