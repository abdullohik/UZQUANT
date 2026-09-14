# UZQUANT Phase 1 — Data Foundation

## Scope

This phase begins the provenance-first data foundation recommended by Phase 0. It does not implement valuation, investment signals, backtesting, execution, portfolio construction or user interface work.

## Implemented foundation

- Issuers and securities are separate entities.
- Common, preferred, other and unknown security classes remain distinct.
- Identifiers are versioned with validity dates, knowledge timestamps and source snapshots.
- Every raw source snapshot stores its URL, retrieval timestamp, optional publication timestamp, media type, content hash and original bytes.
- Financial/market facts require provenance and distinguish reported, derived and estimated values.
- Missing values are not converted to zero or stored as facts without a value.
- Point-in-time queries filter on when information became known.
- Documents retain reporting period, publication date, audit status, accounting standard, reporting perimeter and restatement lineage.
- Validation issues are recorded rather than silently resolved.

## Deliberate limitations

- No live source collector is enabled yet.
- No Openinfo or RSE parser is implemented yet.
- No real production data is bundled.
- No source is treated as a verified API unless Phase 0 actually verified it.
- Date strings are stored in ISO 8601 form; ingestion must normalize and validate them before insertion.
- Numeric values are stored as decimal strings to avoid binary floating-point corruption; domain-specific parsing and scale validation remain future work.

## Security-master ingestion

The operator command retrieves the verified public RSE universe page, archives it with provenance, parses real identifiers and issuer candidates, enriches the required securities from explicit RSE class labels, and records every ingestion run. See outputs/security_master_validation.md.
