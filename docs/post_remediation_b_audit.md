# Post-Remediation-B Valuation Blocker Audit

## Executive Summary

This was a read-only production audit performed at commit `2ac20b0eb15eb1ce4078fdd2a357b5ad63c40cf0`. No code, schema, production data, thresholds, gates, valuation records, factors, or signals were changed. The only deliverable is this document.

Validated valuations remain zero for two distinct reasons:

1. Every target still lacks at least one evidence item needed by every currently applicable fair-value method: verified financial scale and perimeter, a credible peer/target multiple, sourceable discount-rate assumptions, or preferred-class legal economics.
2. The production valuation path is incomplete. It records eligibility failures but contains no general orchestration that executes an eligible P/E, P/B, EV multiple, residual-income, or dividend method and stores its individual result. Consequently, even a future fully eligible input set would not reliably become a completed valuation.

The five verified class-share counts are real, effective-dated, class-specific, and consumed by the valuation assembler and Data Quality calculation. Shares are no longer a blocker. The five quarantined reports are excluded from current fundamental and valuation queries, but the exclusion is fail-open for a new document with no entity-check row; that is a future contamination defect.

The audit registers **26 material findings**: A=4, B=4, C=5, D=2, E=4, F=2, G=5. Category G records the five current target-level economic conclusions after the method audit; it does not imply the underlying fixable A–F findings should be ignored.

## Five-Security Matrix

| Item | AGMKP | KASUP | IPKY | UZTL | QZSM |
|---|---|---|---|---|---|
| Verified identity / class | Yes / Preferred | Yes / Preferred | Yes / Common | Yes / Common | Yes / Common |
| Security ID | `de64eadf-d7a2-5744-b5d6-208d7c772148` | `37a67d28-d290-5adc-a757-2e00570865c1` | `9922a46f-208e-50f4-a367-4930fa116e60` | `c9918d32-fa6e-51fb-af55-794929eb90e0` | `fd1dc881-f47d-5c8b-b00c-a518cc5186c6` |
| Verified class shares | 8,998,232 | 1,875,000,000,000 | 60,239,945,264 | 818,339,529 | 447,516,900 |
| Share effective / disclosure date | 2026-09-14 / 2026-09-14 | same | same | same | same |
| Share source / confidence | RSE detail page / VERIFIED | RSE / VERIFIED | RSE / VERIFIED | RSE / VERIFIED | RSE / VERIFIED |
| Latest stored price | 24,001 UZS | 0.18 UZS | 185.02 UZS | 17,500 UZS | 1,469 UZS |
| Market coverage | 18 observations, 2026-08-17–2026-09-11 | same | same | same | same |
| Eligible financial documents | 2 | 3 | 3 | 2 | 2 |
| Audited / IFRS | 1 / 0 verified | 2 / 0 verified | 3 / 0 verified | 2 / 0 verified | 1 / 0 verified |
| Currency / units / perimeter | UZS / unknown / unknown | UZS / unknown / unknown | UZS / no usable observations / unknown | UZS / unknown / unknown | UZS / unknown / unknown |
| Available fundamentals | Gross Margin, Net Margin, Net Debt (two periods each) | none | none | Gross Margin, Net Margin, Net Debt (two periods each) | Gross Margin, Net Margin, Net Debt (two periods each) |
| Ownership | missing | missing | missing | 2 partial rows | missing |
| Rights | RIGHTS_PARTIAL | RIGHTS_PARTIAL, no structured `security_rights` row | N/A | N/A | N/A |
| Eligible methods | mining DCF; EV/EBITDA; EV/EBIT; P/E; P/B; FCF yield; dividend; historical/peer relative | P/B; P/E; ROE-adjusted P/B; residual income; dividend | P/B; P/TBV; P/E; residual income; DDM | industrial DCF; EV/EBITDA; EV/EBIT; P/E; P/B; FCF yield; dividend; historical/peer relative | same as UZTL |
| Methods actually attempted | `MINING_SCENARIO_DCF`, generic `RELATIVE` | P/B, P/E, ROE-adjusted P/B, residual income, DDM | P/B, P/TBV, P/E, residual income, DDM | `INDUSTRIAL_DCF`, generic `RELATIVE` | same as UZTL |
| Supported now | none sufficiently reliable | none sufficiently reliable | none sufficiently reliable | none sufficiently reliable | none sufficiently reliable |
| Primary blocker | unit/perimeter plus incomplete mining inputs and preferred rights | unit/perimeter, missing Equity/Net Income, rights | correct reports have no normalized bank values | unit/perimeter plus no valuation anchor | unit/perimeter plus no valuation anchor |
| Primary category | B/C/E/F | B/C/E/F | B/C/E | B/C/E/F | B/C/E/F |
| Existing-data ingestion needed | yes | yes | yes | yes | yes |
| Normalization fix needed | yes | yes | yes | yes | yes |
| Software fix needed | yes | yes | yes | yes | yes |
| New verified source eventually needed | discount/peer and possibly rights | peer/cost-of-equity and possibly rights | peer/cost-of-equity | discount/peer | discount/peer |
| Responsible valuation-ready now | No | No | No | No | No |
| Readiness proximity | READY_AFTER_MULTIPLE_SMALL_FIXES | READY_AFTER_MULTIPLE_SMALL_FIXES | READY_AFTER_MULTIPLE_SMALL_FIXES (closest) | READY_AFTER_MULTIPLE_SMALL_FIXES | READY_AFTER_MULTIPLE_SMALL_FIXES |

This is a readiness ranking, not an investment ranking: **IPKY is closest**, because three correct audited annual reports and verified common shares exist, bank P/B/P/E need fewer operating inputs than DCF, and preferred-right uncertainty does not apply. It still requires extraction of the already-approved structured statements, scale/perimeter closure, and a defensible valuation anchor.

## Blocker Classification

The counts below count discrete audit findings, not database rows. Each finding has one primary category.

| ID | Category | Affected scope | Exact finding |
|---|---|---|---|
| A1 | A — SOURCE_DATA_UNAVAILABLE | all relative methods | no versioned credible peer set or sourced target multiples exist |
| A2 | A | DCF/residual-income/DDM | no sourced risk-free, ERP/country-risk, beta/cost-of-debt or cost-of-equity input set exists |
| A3 | A | all targets | ownership/free-float evidence is missing except two partial UZTL rows; this lowers confidence and liquidity certainty, not every valuation method |
| A4 | A | all targets | only 18 recent market observations exist; long-history/momentum and robust historical multiples are unavailable |
| B1 | B — SOURCE_DATA_EXISTS_NOT_INGESTED | all active reports | official report spreadsheets that can carry statement-unit headers are not preserved as production raw documents |
| B2 | B | IPKY | approved Openinfo bank reports exist, but their structured tabular payload is not ingested; current HTML yields only audit-name raw rows |
| B3 | B | all targets | linked audit attachments capable of establishing IFRS/perimeter are not ingested and tied to the financial document |
| B4 | B | AGMKP, KASUP | RSE-linked charters exist in the approved source family but are not ingested/extracted; current rights evidence is only historical dividend treatment |
| C1 | C — DATA_INGESTED_NOT_NORMALIZED | AGMKP, UZTL, QZSM | source-template row 480 is Equity and row 770 is liabilities, but formula-bearing labels are not mapped |
| C2 | C | KASUP | raw row 570 Equity and raw row 320 Net Income are present but not normalized by the exact source labels |
| C3 | C | IPKY | correct raw documents are present, but the HTML parser does not expose bank tables; zero observations result |
| C4 | C | KASUP | `CapEx` is present as a normalized value without adequate proof it is period capital expenditure rather than a balance-sheet capital-investment line; it must be revalidated, not consumed |
| C5 | C | industrial/insurance | accumulated depreciation/amortization balance rows exist but must not be mislabeled as period D&A expense; no valid period D&A is currently normalized |
| D1 | D — NORMALIZED_DATA_NOT_INTEGRATED | AGMKP, UZTL, QZSM | available Net Debt is not used because the Balance-Sheet Risk map only requests Net Debt/EBITDA |
| D2 | D | QZSM, UZTL | stored governance events (1 and 2 respectively) never feed Governance; the factor is a hardcoded unavailable placeholder |
| E1 | E — SOFTWARE_DEFECT | all targets | `run_real_validation` always writes the primary `valuation_records` row as `VALUATION_INSUFFICIENT`; it has no success execution/storage branch for the general method set |
| E2 | E | all targets | method attempts are stored in `valuation_model_attempts`, but individual valuation results are not created for each eligible method and no consensus path exists |
| E3 | E | all financial consumers | quarantine is fail-open through `coalesce(c.validation_status,'MATCHED')`; a future unchecked document can enter metrics, valuation, factors, and historical research |
| E4 | E | common shares | Data Quality penalizes weak/unknown share rights for every security, including common shares, rather than applying class-relevant evidence; thresholds are unchanged but input logic is inaccurate |
| F1 | F — MODEL_REQUIREMENT_TOO_STRICT | AGMKP, UZTL, QZSM | industrial alternatives are collapsed into one generic `RELATIVE` attempt instead of independent P/E, P/B, EV/EBITDA, EV/EBIT, dividend and FCF eligibility tests |
| F2 | F | AGMKP, KASUP | incomplete preferred rights are applied as a blanket method blocker; they should block class-specific dividend/liquidation/terminal assumptions, while company-level analysis remains separately computable and clearly non-transferable to the preferred security |
| G1 | G — LEGITIMATE_ECONOMIC_INSUFFICIENCY | AGMKP | no current method has both complete validated inputs and preferred-security economics |
| G2 | G | KASUP | no current method has verified scale/perimeter, Equity/earnings and adequate preferred economics |
| G3 | G | IPKY | no current method has usable normalized bank statements plus a defensible fair-value anchor |
| G4 | G | UZTL | ratios can be partly computed after scale closure, but no defensible fair-value anchor currently exists |
| G5 | G | QZSM | same: accounting ratios are not a valuation distribution without a sourced multiple or DCF assumptions |

## Alternative Valuation Audit

“Computable” means arithmetic could be performed after identified deterministic fixes. “Research-sufficient” additionally requires a sourced valuation anchor and valid metadata.

| Security / method | Status | Computable after existing-data fixes? | Research-sufficient now? | Reason |
|---|---|---:|---:|---|
| AGMKP DCF | UNSUPPORTED | No | No | no OCF/CapEx/period D&A, production/cost scenario, or discount-rate set; rights affect security-level terminal economics |
| AGMKP EV/EBITDA, EV/EBIT | UNSUPPORTED | No | No | EBITDA/EBIT and defensible EV/peer multiple unavailable |
| AGMKP P/E | PARTIALLY_SUPPORTED | Yes | No | Net Income and shares exist, but scale/perimeter and target multiple do not |
| AGMKP P/B | PARTIALLY_SUPPORTED | Yes | No | raw Equity row exists, but scale/perimeter, peer anchor and preferred/common allocation are unresolved |
| AGMKP FCF yield | UNSUPPORTED | No | No | verified FCF absent |
| AGMKP dividend | PARTIALLY_SUPPORTED | Yes as historical yield only | No | observed dividend is not a governing formula or sustainability model |
| AGMKP historical/peer relative | UNSUPPORTED | No | No | insufficient price/history and no credible peers |
| UZTL/QZSM DCF | UNSUPPORTED | No | No | OCF, CapEx, period D&A and sourced WACC absent |
| UZTL/QZSM EV/EBITDA, EV/EBIT | UNSUPPORTED | No | No | EBIT/EBITDA and target multiple absent |
| UZTL/QZSM P/E | PARTIALLY_SUPPORTED | Yes | No | earnings and shares exist; scale/perimeter and target multiple absent |
| UZTL/QZSM P/B | PARTIALLY_SUPPORTED | Yes | No | raw Equity row exists; mapping, scale/perimeter and target multiple absent |
| UZTL/QZSM FCF/dividend/historical/peer | UNSUPPORTED or PARTIAL dividend observation only | Mostly no | No | no verified FCF or valuation anchor; history is 18 observations |
| KASUP P/B | PARTIALLY_SUPPORTED | Yes | No | raw Equity exists; mapping/scale/perimeter, preferred allocation and peer anchor missing |
| KASUP P/E | PARTIALLY_SUPPORTED | Yes | No | raw Net Income exists; same metadata/rights/anchor limitations |
| KASUP ROE-adjusted P/B | PARTIALLY_SUPPORTED | Yes | No | Equity/Net Income can support ROE after correction, but benchmark relationship and rights are absent |
| KASUP residual income / dividend | UNSUPPORTED | No | No | cost of equity/growth absent; preferred dividend law incomplete |
| IPKY P/B / P/E | PARTIALLY_SUPPORTED | Likely, after structured ingestion | No | correct audited reports exist but yield zero normalized bank inputs; peer/target multiple absent |
| IPKY P/TBV | UNSUPPORTED | Unknown | No | tangible-book deductions are not exposed |
| IPKY residual income / DDM | UNSUPPORTED | No | cost of equity, growth and dividend sustainability inputs absent |

No target can **already** receive a responsible fair-value range under another approved method. P/E or P/B ratios may become arithmetically computable after existing-data fixes, but a ratio is not a Bear/Base/Bull valuation without a defensible multiple or economic model.

## Shares-Outstanding Audit

`share_capital_observations` contains one VERIFIED target-class row per target, sourced to immutable RSE `raw_documents`. All use effective and disclosure date 2026-09-14, parser `remediation-b/1.0.0`. The quantities in the matrix agree with ticker, ISIN and security class. Common and preferred quantities are separate rows; the assembler requests the exact `security_id`, so there is no issuer-total double counting.

The path is:

`raw_documents` → `parse_exchange_share_rows` / `ingest_verified_exchange_shares` in `uzquant/remediation_b.py` → `share_capital_observations` → `_real_reasons` in `uzquant/valuation.py` → `financial_period_inputs_json.assembled.class_shares_outstanding` in `valuation_records`.

The same verified state reaches `Evidence.shares_outstanding_verified` in `uzquant/scoring.py`, so the prior 15-point missing-share penalty is removed. There is no obsolete hardcoded `shares_outstanding_verified = false`; the dataclass default is overridden by the production query. Regression coverage exists in `tests/test_remediation.py` and `tests/test_remediation_b.py`. Finding: **no current shares-consumption blocker**.

## Financial Metadata Audit

All 12 eligible documents have `currency='UZS'`, `accounting_standard='LOCAL_STATUTORY'`, and explicit audit status/publication dates. All have `reporting_perimeter='UNKNOWN'`. Every nonempty normalized observation has `unit='SOURCE_UNIT_UNSPECIFIED'`. IPKY has no normalized observations.

The five quarantined documents are source IDs 296, 1257, 168, 361 and 692. They are marked `MISMATCH` in `financial_document_entity_checks` and excluded from current fundamentals and valuation. The incorrect IPKY document 296 remains labeled consolidated IFRS but is not usable because it belongs to Ipoteka Bank.

The inspected portal HTML contains generic translated strings mentioning “thousand UZS”; those strings are not document-specific proof of statement scale. Earlier official spreadsheet inspection showed explicit thousand-soum statement headers, but the spreadsheets are not preserved and linked in production. Therefore scale remains unverified in the database. Applying current raw values as UZS could produce a 1,000× error; assuming million or billion could produce 1,000,000× or 1,000,000,000× errors. `scale_financial_value` rejects unknown units, but the ingestion path never invokes it and continues storing the unscaled number.

Perimeter and IFRS must be extracted from document-specific report/audit evidence. The source HTML includes audit attachment metadata (for example an IFRS-named attachment for IPKY report 354), but the attachment is not ingested or linked as metadata evidence. This is B3, not permission to label the statements IFRS or consolidated.

## Normalization Audit

### AGMKP, UZTL and QZSM

Currently normalized: Revenue, COGS, Gross Profit, Operating Expenses, Interest Expense, Pretax Income, Taxes, Net Income, Cash, Receivables, Inventory, Current Assets, PP&E, Investments, Intangibles, Long-Term Debt, Short-Term Debt, Retained Earnings and Total Assets.

Raw but not normalized: Equity at template row 480; liabilities at row 770; current liabilities in the explicit “Current Liabilities, Total” row; charter capital; cash-and-equivalent detail; and accumulated depreciation/amortization. “Capital Investments (0800)” is a balance-sheet asset, not automatically period CapEx. Accumulated depreciation is not D&A expense. OCF and a cash-flow statement are not present in the active raw rows.

Normalized but not fully consumed: Net Debt is computed and stored but the sector Balance-Sheet Risk factor requests only Net Debt/EBITDA. Gross Margin and Net Margin correctly feed Quality. The available figures remain unsuitable for per-share valuation until scale and perimeter are resolved.

### KASUP

Currently normalized: Accounts Payable, Cash, Gross Profit, Insurance Reserves, Interest Expense, Inventory, Investments, Long/Short-Term Debt, Operating Expenses, PP&E, Premiums, Pretax Income, Receivables, Retained Earnings, plus a questionable CapEx mapping.

Raw but not normalized: Equity (row 570), Net Income (row 320), total balance-sheet amount, current liabilities, charter capital, multiple insurance expense/claims lines, investment/dividend income and solvency-related rows where labels must be checked individually. The parser has also produced repeated Premium and Reserve concepts from distinct lines; those cannot be silently summed or selected. There are no AVAILABLE insurance fundamental metrics because the required canonical combinations are absent or ambiguous.

### IPKY

Three correct audited reports (289, 354, 387) are active, but `financial_observations` contains zero rows. `financial_raw_values` contains only auditor-name text. The source page did not place the bank statements in the generic HTML tables consumed by `parse_statement_rows`. This is an ingestion/parser gap for the approved structured payload, not evidence that the bank published no financial data.

Across all targets, stored normalized observations are HIGH extraction confidence but their units are unknown; extraction confidence does not cure metadata uncertainty. No LOW-confidence observation is being used in valuation.

## Preferred-Rights Audit

| Right | AGMKP | KASUP | Effect of absence |
|---|---|---|---|
| Historical dividend treatment | verified observation: 489.25 UZS/share | verified historical preferred dividend disclosure | evidence of history only |
| Governing dividend entitlement/formula/minimum | unknown | unknown | blocks dividend valuation and preferred cash-flow scenarios |
| Cumulative status | unknown | unknown | blocks arrears/terminal dividend assessment |
| Voting rights | unknown | unknown | affects governance/control analysis; not company-level earnings arithmetic |
| Liquidation preference | unknown | unknown | blocks liquidation/downside and terminal allocation |
| Conversion rights | unknown | unknown | blocks conversion-option value |
| Redemption rights | unknown | unknown | blocks redemption value |
| Participation rights | unknown | unknown | blocks participation in residual common value |

AGMKP has a LOW-confidence `security_rights` record; KASUP only has `RIGHTS_PARTIAL` in `security_rights_assessments`, so scoring currently sees no structured rights row. Missing rights do **not** prevent company-level enterprise/equity analysis, but they prevent transferring common-equity value mechanically to the preferred security and specifically block dividend, liquidation, conversion and terminal-security valuation. They also reduce final security confidence. Charter ingestion B4 must be attempted before declaring the provisions unavailable.

## Valuation-Orchestration Audit

Production entry point: CLI `run-valuations` → `run_real_validation` → `route_valuation` and `_real_reasons` in `uzquant/valuation.py` → `record_model_attempt` in `uzquant/remediation_b.py` → `valuation_model_attempts` and one primary `valuation_records` row.

What works:

- exact security/share class is selected;
- sector is explicitly overridden for IPKY bank, KASUP insurance and AGMKP mining;
- effective-dated exact-class shares are retrieved;
- financial rows are point-in-time filtered by publication date;
- currently marked mismatches are excluded;
- currency, unknown observation unit, unknown perimeter and preferred rights are checked;
- permitted method names are enumerated for banks/insurance;
- rejection reasons and source record IDs are stored.

What does not work:

- industrial/mining alternatives are not independently enumerated;
- financial observations, not derived fundamental metrics, are the only valuation input source;
- `run_real_validation` never calls P/B, P/E, residual-income, DDM, implied-multiple or industrial-DCF functions using assembled inputs;
- it unconditionally creates the primary result with null Bear/Base/Bull and `VALUATION_INSUFFICIENT`;
- attempts do not retain an individual valuation output or method confidence;
- there is no consensus/weighted method aggregation;
- quarantine defaults unchecked documents to MATCHED;
- DCF assumptions are globally described as unavailable even for methods that do not require WACC.

Verified data not used: raw Equity and Net Income labels, available Net Debt in factor risk, QZSM/UZTL governance events, audit attachment metadata, and the method-specific significance of preferred rights.

## Factor-Integration Audit

| Available metric | Securities | Classification | Reason |
|---|---|---|---|
| Gross Margin | AGMKP, UZTL, QZSM | USED_CORRECTLY | feeds Quality absolute transformation |
| Net Margin | AGMKP, UZTL, QZSM | USED_CORRECTLY | feeds Quality absolute transformation |
| Net Debt | AGMKP, UZTL, QZSM | AVAILABLE_BUT_NOT_INTEGRATED | Balance-Sheet Risk asks only for Net Debt/EBITDA |

There are 18 AVAILABLE metric rows: six per industrial issuer (three concepts over two periods). KASUP and IPKY have none. Growth requires Revenue Growth/EBIT Growth, neither of which was generated with compatible prior-period integration. Dividend is unavailable despite historical dividend records because no date-compatible factor methodology is implemented. Governance is always initialized unavailable and is never replaced, despite one QZSM and two UZTL governance events. Momentum is correctly unavailable because each target has only 18 observations; it is not assigned a neutral 50.

Data Quality correctly recognizes verified shares. It incorrectly penalizes unknown rights for common shares. Confidence then inherits that inaccurate evidence input. No thresholds need changing; the evidence routing needs correction.

## Remediation C Authorized Worklist

Only the following proven B–F fixes are authorized. Source-unavailable A findings may be represented as unavailable inputs but not invented.

| Task | Blocker | Securities | Module / tables | Exact correction | Validation test |
|---|---|---|---|---|---|
| C1 | B1/B3 | all | `financial_documents.py`; `raw_documents`, `financial_document_metadata_evidence`, `financial_documents` | ingest official spreadsheet/audit attachments, hash/store them, extract document-specific unit/perimeter/standard evidence; never infer from magnitude | fixture proves 1×/1,000×/1m×/1bn conversion and unknown metadata rejection |
| C2 | B2/C3 | IPKY | bank document parser; raw/financial observations | ingest the approved structured bank payload and deterministically map actual labels | real reports yield Assets, Equity, loans/deposits, income concepts with lineage; unrelated Ipoteka rows remain absent |
| C3 | C1/C2/C4/C5 | AGMKP, KASUP, UZTL, QZSM | `financial_taxonomy.py`, `financial_documents.py`; raw/observations | add source-label plus template/row-code mappings for Equity, liabilities, Net Income and insurance concepts; remove/reject false CapEx and D&A mappings | exact-label fixtures and balance identity; accumulated depreciation never becomes period D&A |
| C4 | E3 | all | every financial consumer; entity checks | change quarantine to fail closed: only explicit MATCHED documents may contribute | unchecked and MISMATCH documents contribute zero observations, metrics, valuation inputs, factors and historical snapshots |
| C5 | E1/E2/F1 | all | `valuation.py`; valuation records/attempts/peer sets | implement independent method eligibility, actual execution, per-method output/confidence and exact rejection; enumerate industrial P/E/P/B/EV/dividend/FCF separately | supported synthetic/real-evidence case stores result; unsupported model stores only exact rejection; DCF absence does not block P/E |
| C6 | F2/B4 | AGMKP, KASUP | rights ingestion and valuation routing; rights tables | ingest RSE-linked charters; create a field-by-field verified/unknown rights matrix; gate only methods affected by the missing right and keep company value separate from security value | preferred security is never treated as common; dividend/liquidation models reject missing governing terms while company-level analysis can proceed |
| C7 | A1/A2 representation | all | valuation assumptions/peer tables | implement typed provenance states OBSERVED/SOURCE_DERIVED/MODEL_ESTIMATED/CONFIGURABLE_RESEARCH_ASSUMPTION/UNAVAILABLE; no constants; execute only when supplied | missing WACC rejects DCF but not valid P/B; peer method requires versioned real peer records |
| C8 | D1/D2 | industrial targets, QZSM, UZTL | `scoring.py`; factors, governance events | route Net Debt only through a documented absolute risk rule if economically valid; build evidence-based Governance coverage/score and leave missing evidence unavailable | source IDs and transformations persist; missing governance never means good governance |
| C9 | E4 | common securities | `scoring.py`; Data Quality/confidence | apply rights certainty according to share class/materiality; retain the same penalties and thresholds | verified shares remove only their penalty; common shares do not receive a preferred-right penalty; preferred rows still do |
| C10 | D/F integration | all | end-to-end runner and tests | rerun current pipeline only after fixes; preserve point-in-time and model lineage; produce forensic traces | five target traces reproduce stored inputs/results; gates remain byte-for-byte behaviorally equivalent on existing tests |

Remediation C must not create peer values, WACC inputs, reporting perimeter, charter terms, or financial lines that the retrieved evidence does not support. If C1–C10 leave zero valuations solely because A/G limitations remain, remediation can still be complete.

## Known Source Limitations

- No credible, versioned peer group and target multiples are currently stored for any target.
- No complete sourced discount-rate/country-risk set is stored.
- Market history is only 18 observations per target; momentum, historical multiples and robust volatility evidence remain unavailable.
- Ownership/free float is missing for four targets and partial for UZTL.
- Until linked charters are ingested and inspected, preferred legal terms remain unverified; historical dividends cannot substitute.
- Some local statutory reports may not identify consolidated/standalone perimeter. If document-specific report and audit evidence remain silent after authorized ingestion, perimeter must remain UNKNOWN.
- The active JSC/insurance statements do not currently expose verified operating cash flow or period CapEx/D&A adequate for DCF. Balance-sheet capital investments and accumulated depreciation are not substitutes.

## Final Conclusions

1. Validated valuations are zero because no method currently has complete validated metadata plus a defensible fair-value anchor, and the runner lacks a genuine success-execution path.
2. Software/integration defects: **8** (D=2, E=4, F=2).
3. Existing-source ingestion gaps: **4**.
4. Normalization gaps: **5**.
5. Source-data limitations: **4**, plus five target-level legitimate current insufficiency conclusions.
6. IPKY is closest to readiness, followed by KASUP, UZTL, QZSM, then AGMKP; this ordering reflects method/input distance only.
7. No target can already be responsibly valued by merely switching methods. P/E/P/B may become computable after fixes, but require a defensible valuation anchor to become fair-value estimates.
8. Remediation C should perform only C1–C10 above.
9. Short market history, missing ownership/free float, absent peer/discount inputs, and any legal/perimeter terms still absent after approved-source ingestion should be accepted as known limitations, not filled by speculation.
