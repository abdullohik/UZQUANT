# Remediation C Dependency Matrix

Status is the final real production state. “Fixed” means the approved existing evidence is now consumed; “limitation” means no defensible value can be produced from current verified sources.

| Dependency | AGMKP | KASUP | IPKY | UZTL | QZSM |
|---|---|---|---|---|---|
| Security/share class | Verified preferred | Verified preferred | Verified common | Verified common | Verified common |
| Class shares | Verified, exact security ID | Verified, exact security ID | Verified, exact security ID | Verified, exact security ID | Verified, exact security ID |
| Raw market history | 20 observations | 20 | 20 | 20 | 20 |
| Matched financial reports | 2 | 3 | 3 | 2 | 2 |
| Normalized observations | 46 | 156 | 48 | 46 | 46 |
| Unit | Verified workbook header; UZS | Verified; UZS | Verified; UZS | Verified; UZS | Verified; UZS |
| Reporting perimeter | Unknown—limitation | Unknown—limitation | Unknown—limitation | Unknown—limitation | Unknown—limitation |
| Available fundamentals | 8 | 0 | 6 | 8 | 8 |
| Ownership rows | 0 | 0 | 0 | 2 | 0 |
| Security rights | Partial | Partial | Not material to common routing | Not material to common routing | Not material to common routing |
| Valuation methods evaluated | Mining DCF, EV/EBITDA, EV/EBIT, P/E, P/B, FCF yield, DDM | P/B, P/E, ROE-adjusted P/B, residual income, DDM | P/B, P/TBV, P/E, residual income, DDM | Industrial DCF, EV/EBITDA, EV/EBIT, P/E, P/B, FCF yield, DDM | Same as UZTL |
| Completed valuation | None | None | None | None | None |
| Primary rejection | No sourced anchor; perimeter; DCF inputs; preferred rights | No sourced anchor; perimeter; preferred rights | No sourced anchor; perimeter; P/E also lacks Net Income | No sourced anchor; perimeter; DCF inputs | No sourced anchor; perimeter; DCF inputs |
| Liquidity | LIQUIDITY_TRAP | INVESTABLE, low confidence | INVESTABLE, low confidence | INVESTABLE, low confidence | LIMITED_LIQUIDITY, low confidence |
| Available factors | 4 | 2 | 2 | 5 | 3 |
| Confidence | 21.25 | 38.75 | 41.75 | 25.25 | 23.25 |
| Gates | Critical data quality; critical liquidity; unknown preferred rights | Unknown preferred rights | None; insufficient factor coverage | None | None; insufficient factor coverage |
| Signal | DATA_INSUFFICIENT | DATA_INSUFFICIENT | DATA_INSUFFICIENT | HOLD | DATA_INSUFFICIENT |

## Dependency disposition

| Audit work item | Result | Disposition |
|---|---|---|
| Official financial attachments and units | 12 XLSX files preserved; 12 unit-evidence rows | Fixed with current verified source |
| IPKY structured statements | 39 bank observations parsed | Fixed with current verified source |
| Exact taxonomy gaps/false CapEx | Exact mappings added; false mapping rejected | Fixed |
| Quarantine fail-open path | Explicit MATCHED join required | Fixed |
| Multi-method execution and storage | Implemented and tested | Fixed |
| Preferred routing | Company methods separated; affected security methods gated | Fixed; legal terms remain source-limited |
| Assumption/peer provenance | Typed schema and eligibility enforcement | Fixed; no legitimate inputs currently available |
| Fundamental/governance factors | Supported evidence connected | Fixed where methodologically supported |
| Common-share rights penalty | Removed only for common securities | Fixed |
| End-to-end rerun | Completed through signals | Fixed |
