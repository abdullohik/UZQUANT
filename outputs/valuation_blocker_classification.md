# Valuation Blocker Classification

Assessment date: 2026-09-27

| Blocker | Class | Current resolution path |
|---|---|---|
| Missing authoritative nominal UZS reference curve | RESOLVED | Full official CBU history ingested; this blocker is removed |
| Unknown reporting perimeter | COMPANY FACT / INCOMPLETE DISCLOSURE NORMALIZATION | Verify consolidated versus standalone from the exact source report; do not infer |
| Missing Net Income for IPKY | COMPANY FACT / INCOMPLETE INGESTION | Retrieve and parse the correct Ipak Yuli report containing profit; quarantined Ipoteka Bank reports cannot be used |
| Missing OCF, CapEx, D&A, EBIT, EBITDA | COMPANY FACT / INCOMPLETE INGESTION | Obtain compatible cash-flow/income-statement disclosures; do not derive absent line items silently |
| Preferred rights for AGMKP and KASUP | COMPANY FACT / LEGAL EVIDENCE | Obtain authoritative charter/prospectus/share-class provision |
| Verified production, unit cost and mining CapEx | COMPANY FACT / NEW OR IMPROVED SOURCE | Required for AGMKP mining scenarios |
| Security-class dividend history | COMPANY FACT / INCOMPLETE DISCLOSURE INGESTION | Required where no verified record exists |
| Credible peer set | PEER-DERIVABLE INPUT | Current verified universe has no minimum three comparable same-sector issuers; requires legitimate broader data |
| Equity-risk premium | RESEARCH ASSUMPTION | Adopt a sourced, versioned methodology explicitly; not a company fact |
| Beta | MODEL-ESTIMATED INPUT | Estimate from adequate data or approve a sourced sector proxy with comparability caveat |
| Long-term growth | RESEARCH ASSUMPTION | Versioned nominal UZS assumption with economic basis |
| Cost of debt | COMPANY FACT / DERIVED INPUT | Requires debt terms or defensible issuer spread methodology |
| Target capital structure | RESEARCH ASSUMPTION | Explicit method-specific target weights |
| Forecast scenarios | RESEARCH ASSUMPTION | Bear/base/bull operating assumptions with version and rationale |

No blocker was reclassified as “resolved” merely because the CBU curve became available. Only the authoritative UZS reference-rate component was removed.
