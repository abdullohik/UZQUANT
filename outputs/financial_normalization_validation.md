# Phase 3 financial normalization validation

Validation run: 2026-09-14  
Parser: `openinfo-financial-html/1.0.0`  
Source: [Openinfo Corporate Disclosure Portal](https://openinfo.uz/) (official primary source)

## Result

The end-to-end run succeeded for five real issuer reports. It archived 5 HTML source documents, preserved 567 reported rows, and created 88 mapped canonical observations. No network or parser failures occurred.

| Target security | Report | Period end | Publication date | Raw rows | Normalized observations |
|---|---|---:|---:|---:|---:|
| AGMKP issuer | JSC quarterly 18364 | 2026-03-31 | 2026-05-01 | 112 | 21 |
| KASUP issuer | Insurance quarterly 361 | 2023-06-30 | 2023-07-26 | 171 | 16 |
| IPKY | Bank quarterly 1257 | 2026-03-31 | 2026-04-27 | 53 | 9 |
| UZTL | JSC annual 6116 | 2025-12-31 | 2026-07-10 | 119 | 21 |
| QZSM | JSC quarterly 18437 | 2026-03-31 | 2026-05-13 | 112 | 21 |

All observations retain the original text, normalized decimal, period, source document and cell location, extraction method, confidence, and `REPORTED` status. AGMKP and KASUP were resolved through their preferred-security tickers to their canonical issuers; no security records were merged.

## Validation findings

- 5 `CURRENCY_UNSPECIFIED` warnings: the retrieved table content did not explicitly establish currency.
- 5 `REPORTING_PERIMETER_UNKNOWN` warnings: consolidated versus standalone status was not explicit enough to assign.
- No accounting-identity failure remained where all three required totals mapped unambiguously.
- No duplicate, overlapping-period, period-order, or negative-total issue was detected in this run.

## Limitations

Only official structured HTML was encountered and implemented. XLS/XLSX, CSV, JSON, XML, PDF, DOC/DOCX, OCR, and LLM extraction are not claimed as supported by this run. Openinfo templates vary by issuer type, and many specialist insurance/bank rows do not map to the general taxonomy yet; those rows remain safely preserved. Audit status, accounting standard, currency, unit, and reporting perimeter remain unknown where the source did not explicitly support classification. No missing values, EBITDA, Free Cash Flow, or other concepts were inferred.
