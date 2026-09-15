# Phase 6 valuation validation

## Result

The production valuation engine, persistence schema, CLI route and tests are implemented. The real point-in-time validation ran on 2026-09-15 for AGMKP, KASUP, IPKY, UZTL and QZSM. All five correctly returned `VALUATION_INSUFFICIENT`; no fair value was forced.

The Phase 6 acceptance gate is **not met** because the approved stored data cannot yet support reproducible numerical valuations for several real companies. Declaring the gate passed would conflict with `ACCURACY_RULES.md`.

## Real validation cases

| Security | Route | Stored source document | Outcome |
|---|---|---|---|
| AGMKP | General / industrial DCF | `edbb64a4-e21b-56c2-8ba8-7569eb708c35` | Insufficient; preferred rights also unverified |
| KASUP | Insurance / P/B | `dfb9cafd-5514-533d-9a91-605839bfaca9` | Insufficient; preferred rights also unverified |
| IPKY | Bank / P/B | `b4665b90-8586-5485-a51d-6623b4b87992` | Insufficient |
| UZTL | General / industrial DCF | `d75b0d38-aa9c-5928-ae86-d32768aca0c1` | Insufficient |
| QZSM | General / industrial DCF | `784cabe5-8cbe-571b-9f2e-53c71a6f19dc` | Insufficient |

Common blockers are unverified financial currency/unit/reporting perimeter, one available report per issuer, and no verified total shares outstanding. Industrial cases additionally lack normalized operating cash flow, CapEx and D&A. These checks were reconciled directly against the stored document metadata and normalized concepts.

## Independent numerical reconciliations

Deterministic synthetic inputs were used only to validate formulas, never as real company evidence:

1. One-year DCF: revenue 100, EBIT margin 20%, tax 25%, D&A 3%, CapEx 4%, WACC 10%, zero growth gives FCF 14, terminal value 140, enterprise value 140. With net debt 40 and 10 shares, equity value is 100 and fair value is 10/share. The production engine matches each intermediate value exactly.
2. FX: 2 USD × a dated sourced rate of 12,500 UZS/USD gives 25,000 UZS. Cross-currency valuation without a matching FX record is rejected.
3. Gordon dividend model: dividend 2, cost of equity 12%, growth 2% gives `2 × 1.02 / (0.12 − 0.02) = 20.4`. Cost of equity less than or equal to growth is rejected.

## Tests

`python3 -m pytest -q`: 44 passed.

Coverage includes DCF and terminal-value math, net debt, share count, four-dimensional sensitivity grids, FX conversion, nominal/real consistency, scenario ordering, bank and insurer routing, residual-income and dividend models, negative earnings, mining scenarios, zero shares, invalid terminal growth and missing cash-flow inputs.

## Traceability and limitations

Each real case is stored in `valuation_records` with its security ID, dates, route, model version, assumptions, insufficiency reasons, source-document IDs and source-observation IDs. Sensitivity, peer-set and FX tables are available for future supported cases. No portfolio recommendation or investment signal was created.

To pass the acceptance gate, authoritative sources must establish report currency and unit, reporting perimeter, total shares outstanding by class/date, sufficient compatible history, required cash-flow concepts, and preferred-share rights where applicable. Those inputs must be ingested and verified in their governing upstream phases before Phase 6 is rerun.
