# First Valuation Unlock Sprint Report

Date: 2026-09-27

## Outcome

The official CBU full government-securities curve is now a production, append-only, point-in-time data source. The sprint reassessed 31 methods across IPKY, KASUP, UZTL, QZSM and AGMKP. **No method is yet executable and no valuation was forced.** This is a valid sprint result: the risk-free/reference-rate problem is solved, while the remaining independent blockers are now explicit.

## Implementation

- Migration 035 adds curve vintages, curve points and versioned method-eligibility records.
- The `update-cbu-yield-curve` operator command downloads both public API arrays, validates them, archives immutable raw JSON, and stores every result/point.
- As-of lookup uses both curve date and retrieval timestamp, preventing future-vintage leakage.
- Valuation model version 3.1.0 assesses each method separately. Reporting perimeter and unit checks now attach to the observations a method actually needs rather than to every issuer document.
- The curve is classified `AUTHORITATIVE_SOURCE`; its published points are `OBSERVED`.
- Currency/basis guardrails remain: nominal UZS curve inputs cannot be mixed with real or foreign-currency cash flows without explicit conversion and consistent assumptions.

## Verified production ingestion

- Source curve results: 111
- Source/stored points: 2,544
- Curve dates: 2024-08-21 through 2026-09-23
- Latest curve: 23 tenors from today through ten years
- Latest ten-year zero rate: 16.96054015902%, continuously compounded nominal UZS
- Immutable raw documents: results JSON and points JSON, linked to ingestion run `6981e902-00c7-454e-b031-57746a379f26`

The economic definition follows the official CBU methodology page: a theoretical smoothed national-currency government-securities curve built using Nelson-Siegel from government/CBU securities and relevant money-market/auction inputs. It may differ from actual transaction yields.

## Required questions answered

1. **Was the curve definition verified?** Yes; see `outputs/valuation_assumption_provenance.md`.
2. **Was the full curve integrated?** Yes, 111 vintages and 2,544 points—not only ten years.
3. **Is point-in-time lineage preserved?** Yes: curve date, tenor, rates, basis, currency, URLs, source revision string, raw hashes and retrieval time.
4. **Is 16.96054% treated as WACC?** No.
5. **Which blocker was removed?** `MISSING_AUTHORITATIVE_UZS_RISK_FREE_CURVE` / the former undifferentiated sourceable discount-rate blocker.
6. **Did any target become valuation-ready?** No.
7. **Why not IPKY?** Correct matched Ipak Yuli evidence lacks normalized Net Income and verified perimeter; peer, beta, equity-premium and growth inputs are also absent. Ipoteka Bank report 296 remains quarantined.
8. **Why not KASUP?** Unknown perimeter, unverified preferred rights, no credible insurer peer set, and incomplete cost-of-equity/growth chain.
9. **Why not UZTL?** Unknown perimeter, missing cash-flow/DCF lines, peer set, and the remaining WACC/forecast components.
10. **Why not QZSM?** Same DCF/peer gaps as UZTL plus missing class dividend history for DDM.
11. **Why not AGMKP?** Unknown perimeter, preferred rights, mining operating assumptions/facts, peers, and remaining discount/WACC components.
12. **Were peer multiples fabricated?** No; all peer methods fail `INSUFFICIENT_CREDIBLE_PEER_SET`.
13. **Were research assumptions confused with company facts?** No; the blocker-classification output separates them.
14. **How many valuations succeeded?** Zero of 31; therefore zero manual reconciliations are claimed.
15. **Was historical validation rerun?** No. Only the current research chain was refreshed.
16. **Did readiness change?** No; it remains EXPERIMENTAL under unchanged criteria.

## Current research refresh

Financial-document refresh: succeeded (14 documents in the run; 273 normalized observations). Fundamentals: 64 available, 642 unavailable, no triggered accounting flags. Liquidity: seven cases. Current ranking was regenerated. Historical backtests and model validation were deliberately not run.

## Remaining path to a first valuation

The shortest accuracy-compliant path is not another discount-rate change. It is:

1. establish exact reporting perimeter for one target's compatible financial statements;
2. complete the method-specific company facts (IPKY Net Income/ROE for residual income, or UZTL/QZSM cash-flow lines for DCF);
3. approve a versioned research-assumption policy for equity premium, beta/proxy, growth and—where applicable—cost of debt/capital structure;
4. obtain authoritative preferred-share rights before valuing AGMKP or KASUP at the security level;
5. execute and independently reconcile only after every selected method input passes.

Until then, `VALUATION_INSUFFICIENT` is correct.
