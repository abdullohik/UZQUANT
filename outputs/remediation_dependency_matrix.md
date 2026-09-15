# Remediation A dependency matrix

Production rerun: 2026-09-15. `AVAILABLE` means usable by the current production code; `PARTIAL` is never treated as verified.

| Ticker | Identity / class | Shares outstanding | Price / history | Financial periods | Audit / standard | Currency / unit / perimeter | Fundamentals | Ownership | Rights | Valuation | Liquidity | Factors | Confidence / gates / signal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AGMKP | VERIFIED / preferred | UNAVAILABLE: no class count | VERIFIED latest / 18 dates | 2023 annual; Q1 2026 | audited local; unaudited local | UZS / unknown / unknown | 42 observations; 6 metrics | missing | RIGHTS_PARTIAL | INSUFFICIENT | LIQUIDITY_TRAP, LOW | 4/10 available; only 3 positive-weight | 16.75; data quality, liquidity, rights; DATA_INSUFFICIENT |
| KASUP | VERIFIED / preferred | PARTIAL: 658,616,940 issuer total only | VERIFIED latest / 18 dates | H1 2023; 2023 annual; 9M 2025 | one audited local; two unaudited local | UZS / unknown / unknown | 72 observations; 0 metrics | missing | RIGHTS_PARTIAL | INSUFFICIENT | INVESTABLE, LOW | 2/10 available | 34.25; data quality, rights; DATA_INSUFFICIENT |
| IPKY | VERIFIED / common | UNAVAILABLE: no class count | VERIFIED latest / 18 dates | 2022 annual; Q1 2026 | audited IFRS; unaudited local | UZS / unknown / mixed consolidated/unknown | 9 observations; 2 metrics | missing | not a preferred gate | INSUFFICIENT | INVESTABLE, LOW | 2/10 available | 14.75; data quality; DATA_INSUFFICIENT |
| UZTL | VERIFIED / common | UNAVAILABLE: no class count | VERIFIED latest / 18 dates | 2024 annual; 2025 annual | two audited local | UZS / unknown / unknown | 42 observations; 6 metrics | partial threshold disclosures, no exact % | not a preferred gate | INSUFFICIENT | INVESTABLE, LOW | 4/10 available; only 3 positive-weight | 16.75; data quality; DATA_INSUFFICIENT |
| QZSM | VERIFIED / common | UNAVAILABLE: no class count | VERIFIED latest / 18 dates | 2023 annual; Q1 2026 | audited local; unaudited local | UZS / unknown / unknown | 42 observations; 6 metrics | missing | not a preferred gate | INSUFFICIENT | LIMITED_LIQUIDITY, LOW | 3/10 available | 15.75; data quality; DATA_INSUFFICIENT |

## Exact remaining valuation blockers

| Ticker | Engine | Missing or unverified inputs |
|---|---|---|
| AGMKP | Industrial DCF | verified preferred-class shares; OCF; CapEx; D&A; source unit; reporting perimeter; complete preferred rights |
| KASUP | Insurance P/B | verified preferred-class shares; source unit; reporting perimeter; complete preferred rights |
| IPKY | Bank P/B | verified class shares; source unit; reporting perimeter |
| UZTL | Industrial DCF | verified class shares; OCF; CapEx; D&A; source unit; reporting perimeter |
| QZSM | Industrial DCF | verified class shares; OCF; CapEx; D&A; source unit; reporting perimeter |

The assembler now records the exact set of available concepts, document IDs, observation IDs, and the required share input. It does not create a value unless the inputs and explicit assumptions pass the existing gates.

## Pipeline status after remediation

| Layer | Status | Result |
|---|---|---|
| Security master | Unchanged | 74 securities / 53 issuers; target identities and classes retained |
| Market history | Blocked at source expansion | 126 observations / 7 securities / 18 dates; dated official endpoint returned HTTP 403 |
| Financial documents | Improved | 5 → 11 real Openinfo reports; all five target issuers now have 2–3 reports |
| Normalized financials | Improved | 88 → 207 observations; 27 canonical concepts |
| Fundamental metrics | Improved | 142 → 303 records; available 9 → 20 |
| Share capital | New structural support | 5 effective-dated assessments; 0 verified class counts, 1 partial issuer total, 4 unavailable |
| Preferred rights | Improved classification | AGMKP and KASUP explicitly RIGHTS_PARTIAL; neither promoted to verified |
| Valuation | Assembler repaired; data still insufficient | 0/5 available; precise input inventories and blockers stored |
| Factor scoring | Improved wiring | Quality now consumes stored fundamentals for AGMKP, UZTL, and QZSM; gates unchanged |
| Signals | Correctly unchanged | 7/7 latest signals remain DATA_INSUFFICIENT |
