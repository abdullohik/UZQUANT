# Financial ingestion methodology

## Source and extraction

Phase 3 uses official structured HTML report pages from the [Openinfo Corporate Disclosure Portal](https://openinfo.uz/). Each response is hashed with SHA-256 and archived immutably before parsing. The parser walks HTML tables deterministically and records the selected cell location. This follows the extraction hierarchy: structured official data is used, so spreadsheet, PDF, OCR, and LLM extraction are neither needed nor implemented for the reports encountered in this phase.

The five configured reports are linked to issuers through the approved Phase 1 ticker-to-security-to-issuer master. Preferred and common securities therefore resolve to the same issuer without collapsing their security records.

## Storage and point-in-time behavior

Migration `005_financial_documents.sql` adds documents, raw values, normalized observations, and validation issues. Documents retain period and publication dates, retrieval time, source URL and identifier, content hash, parser version, format, standard, audit status, perimeter, and revision lineage. A changed payload for the same source identifier is stored as a new revision linked to the preceding document. The `point_in_time` query admits only documents published on or before the requested date.

Unknown metadata is explicit. The selected pages did not establish currency, unit, audit status, accounting standard, or reporting perimeter sufficiently for safe automated attribution, so these are stored as `UNKNOWN`/null rather than inferred.

## Parsing and validation

Balance-sheet rows use the reported period-end column. Income-statement templates expose prior/current income-and-expense pairs; the parser selects the reported non-zero cell in the current pair while preserving its exact location. Missing markers are not converted to zero.

Validation checks period order, duplicate/revised source identifiers, overlapping periods, currency and perimeter availability, negative balance totals, and the accounting identity when Total Assets, Total Liabilities, and Equity are all unambiguously mapped. Suspected problems are recorded, not repaired. Content hashes and uniqueness constraints make unchanged reruns idempotent.

Run from a clean initialized environment with:

```text
python3 -m uzquant init-db
python3 -m uzquant update-security-master
python3 -m uzquant update-financial-documents
```
