# Remediation Phase C Report

## Exit classification

**REMEDIATION_COMPLETE**

The fixable software, parser, normalization, and integration defects identified by the approved post-Remediation-B audit have been closed. No target currently supports a defensible fair-value range because verified reporting perimeter and a sourceable valuation anchor (peer multiple, cost of equity/WACC, or equivalent economic assumption set) remain unavailable. That is a source-evidence limitation, not a remaining critical software defect.

No threshold, factor minimum, confidence rule, liquidity gate, governance gate, or preferred-right requirement was weakened. No Phase 13–15 process was run.

## Production run

The real pipeline was rerun through financial attachment ingestion, fundamentals, valuation, liquidity, factors, confidence, gates, and signals. Official Openinfo XLSX attachments were retrieved, hashed, and preserved as immutable raw documents. Twelve document-specific headers explicitly established thousand-UZS units; 222 existing observations were scaled deterministically to base UZS and 39 bank observations were extracted from structured workbooks. Five previously quarantined issuer-mismatched reports remain excluded.

## Before and after

Counts are production counts. Target-only figures cover AGMKP, KASUP, IPKY, UZTL, and QZSM; universe signal figures cover the seven currently analyzed securities.

| Measure | Before C | After C |
|---|---:|---:|
| Financial documents | 17 | 17 |
| Normalized observations | 279 | 342 |
| Available fundamentals | 18 | 30 |
| Verified target share counts | 5 | 5 |
| Valuation-ready securities | 0 | 0 |
| Validated valuations | 0 | 0 |
| Available target factor scores | 15 | 16 |
| Target attractiveness scores | 0 | 1 |
| Target average confidence | 28.05 | 30.05 |
| Target median confidence | 21.25 | 25.25 |
| Universe DATA_INSUFFICIENT | 7 | 5 |
| Other universe signals | 0 | 2 (1 HOLD, 1 LIQUIDITY_TRAP) |

The signal change is an outcome of corrected evidence flow, not a target. UZTL reaches a low-confidence HOLD research classification from four or more supported factors; it still has no valuation. AGMK remains a LIQUIDITY_TRAP. Four of the five priority targets remain DATA_INSUFFICIENT.

## Software defects fixed

- Valuation routing now evaluates each sector-approved method independently; DCF failure no longer blocks P/E or P/B eligibility.
- Eligible P/E and P/B calculations have a real execution and storage path with exact class shares, explicit assumptions, scenarios, lineage, and method confidence.
- Multi-method consensus is currency-safe and confidence-weighted; individual results remain preserved.
- Assumption provenance is typed as OBSERVED, SOURCE_DERIVED, MODEL_ESTIMATED, CONFIGURABLE_RESEARCH_ASSUMPTION, or UNAVAILABLE. Hidden constants are rejected.
- Financial consumers are fail-closed: only documents with an explicit MATCHED entity check may contribute observations, metrics, or valuation inputs.
- Common shares no longer receive a preferred-right Data Quality penalty. Preferred securities retain the existing rights gate.
- Stored adverse governance evidence now reaches the Governance factor; missing evidence remains unavailable rather than being treated as good governance.

## Normalization defects fixed

- Exact template/row mappings were added for Equity, Current Liabilities, Total Liabilities, and Net Income.
- A false balance-sheet CapEx mapping was removed: capital-investment balances are not period capital expenditure.
- Structured bank workbooks now provide IPKY Assets, Equity, Net Interest Income, and other mapped bank concepts with raw-document and cell/row lineage.
- Source-declared thousand-UZS units are converted exactly to UZS. No scale was inferred from magnitude.

## Integration and ingestion defects fixed

- Verified, effective-dated, class-specific shares flow into valuation input assembly and per-share execution without common/preferred mixing.
- Official Openinfo XLSX attachments are stored in `raw_documents`; unit evidence is stored in `financial_document_metadata_evidence`.
- Interrupted attachment runs are closed as failed before a new idempotent run starts.
- Production emits one valuation record and one auditable model attempt per approved method, rather than a single generic rejection.

## Remaining source-data limitations

- All active reports still have reporting perimeter UNKNOWN; it was not inferable from the retrieved structured workbooks.
- No versioned, credible peer set and sourced Bear/Base/Bull multiples are available.
- No sourceable cost-of-equity, country-risk, WACC, or terminal-growth assumption set is approved for production.
- Operating cash flow, CapEx, and D&A remain incomplete for DCF/FCF methods.
- AGMKP and KASUP preferred rights remain partial; dividend, liquidation, conversion, and terminal-security economics cannot be asserted.
- Ownership/free-float evidence is absent for most securities.
- Current market history is short (20 observations per priority security), so momentum and historical-multiple evidence remain insufficient.
- Insurance reports contain ambiguous/repeated premium, reserve, claims, and expense lines; they were not silently combined.

## Exit audit

Valuation orchestration, share consumption, unit controls, sector routing, preferred-security routing, quarantine exclusion, method lineage, factor mapping, confidence recalculation, and immutable signal history were verified. Every unsupported method records exact reasons. No available verified evidence is known to be blocked by a remaining critical parser or integration defect.

Full test result: **131 passed**.
