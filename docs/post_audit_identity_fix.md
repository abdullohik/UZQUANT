# Post-audit canonical identity hotfix

## Outcome

The Phase 19 critical finding is fixed and re-tested. Canonical issuer identity is now an opaque, persistent internal identifier. Legal names are evidence attributes only. Financial reports require an effective-dated ticker **and** ISIN resolution to the same security and issuer; disagreement, ambiguity, or an out-of-range identifier fails closed.

Readiness remains **EXPERIMENTAL** under the unchanged Phase 19 criteria. This hotfix does not resolve the four HIGH findings or the historical/source limitations, and it does not authorize live trading.

## Failure reproduction before the fix

The legacy path in `uzquant/security_master.py` generated `stable_id("issuer", "uzse:" + normalize_name(name))`. The distinct raw inputs `Example Bank AJ` and `<Example Bank> AJ` both normalized to `example bank aj` and both generated legacy issuer ID `53c129bd-e87a-55a4-bd72-1a928957b5be`. This demonstrated silent name-derived collision.

The legacy `_issuer_for_ticker` path in `uzquant/financial_documents.py` selected the most recently known ticker row without testing `valid_from`, `valid_to`, document publication date, ISIN, or conflicting evidence. The affected chain was `identifier_history → securities → issuers → financial_documents → financial_observations → fundamental_metrics → valuation_records → factor_scores → research_signals`.

## Root cause and correction

- Root cause 1: normalized legal name was used as identity rather than candidate evidence.
- Root cause 2: report assignment treated ticker as authoritative and ignored effective dates.
- Migration 028 adds `canonical_issuers`, a one-to-one legacy migration map, effective identifier evidence, collision records, report identity assignments, and contamination-audit records.
- Migration 029 adds effective-dated security-class/listing evidence and append-only analytical invalidations. Migration 030 removes the legacy uniqueness assumption that would otherwise prevent contradictory identifier evidence from being stored and detected.
- All 55 existing issuer records received distinct opaque canonical IDs. Existing issuer IDs and every foreign key remain in place for lineage. `issuer_identity_migrations` preserves the complete old-ID-to-canonical-ID mapping.
- New issuer creation uses random opaque IDs. Existing securities are found by verified ISIN; normalized names never merge records. Same-name candidates are retained separately and recorded as conflicts.
- Ticker and ISIN resolution applies both observation-date validity and knowledge-time availability. Multiple effective mappings produce `IDENTITY_CONFLICT`; known but out-of-range mappings produce `IDENTIFIER_OUT_OF_RANGE`; missing evidence produces `IDENTITY_UNRESOLVED`.
- Financial ingestion now requires ticker and ISIN to resolve to the same security. Production consumers for normalization, fundamentals, valuation, scoring, research API, backtesting, and prospective snapshots admit only `VERIFIED` report assignments.
- Issuer, security, security class, listing, and identifier remain separate database entities. AGMK/AGMKP and KASU/KASUP share their appropriate issuer but retain distinct security IDs and classes.

## Migration and contamination audit

The migration completed with zero foreign-key violations.

| Result | Count |
|---|---:|
| Legacy issuer → opaque canonical mappings | 55 |
| Securities preserved | 76 |
| Financial documents audited | 17 |
| Verified report assignments | 12 |
| Quarantined pre-existing entity mismatches | 5 |
| Audit records classified CORRECT | 3,483 |
| Audit records classified AMBIGUOUS | 593 |
| Audit records requiring recomputation/invalidation | 81 |
| Explicit analytical invalidations written | 81 |
| Records recomputed | 0 |

The five quarantined reports were already marked `MISMATCH` by the earlier entity checker. Their 588 raw extracted values and five document records are preserved as ambiguous evidence; nothing was deleted. Their 81 normalized observations are now explicitly invalidated and excluded by the verified-assignment gates. They were not recomputed because no corrected authoritative identity evidence exists. No fundamental metric was present for those five reports, and the audit found no newly proven cross-issuer contamination in valuation, factor, signal, portfolio, or shadow-portfolio records.

## Adversarial regression and re-audit

Fifteen canonical-identity regression cases were added, covering identical normalized names, punctuation collision, fuzzy-name non-merging, ticker reuse, ticker change, ISIN conflict, ticker/ISIN disagreement, effective-date boundary, post-change documents, AGMK/AGMKP and KASU/KASUP class separation, ambiguous identity, source disagreement, report quarantine, and canonical-ID persistence.

The exact Phase 19 attacks now fail safely:

| Attack | Result |
|---|---|
| Collide normalized legal names | Separate opaque issuer and canonical IDs; no merge |
| Assign a report using ticker alone | Impossible through the production assignment path |
| Supply disagreeing ticker and ISIN | `IDENTITY_CONFLICT` |
| Use an identifier outside its validity interval | `IDENTIFIER_OUT_OF_RANGE` |
| Confuse common and preferred securities | Distinct security IDs/classes retained |
| Repeat migration/resolution | Existing canonical IDs persist |

The full suite passed: **173 tests passed**.

## Operational-state preservation

No RSE refresh was attempted and no operational state was cleared. Current health remains one `FAILED` security-master pipeline, one `DEGRADED` macro pipeline, and 15 `STALE` dependent pipelines. The Phase 18 prospective states remain `STALE_BLOCKED`; no order, fill, position, risk gate, portfolio threshold, or signal was forced or changed.

## Remaining findings and limitations

The four Phase 19 HIGH findings remain:

1. mutable normalized-financial lineage;
2. source-schema alerting not integrated into production parsers;
3. incomplete propagation/display of `DEGRADED` state;
4. prospective snapshots do not freeze the full normalized-financial payload.

Source/model limits also remain: insufficient historical point-in-time evidence for validation, incomplete reporting units/perimeters/restatement history, incomplete share-rights and share-count evidence, absent order-book/depth history, uncalibrated execution capacity, and incomplete macro vintages. Phase 14 therefore remains `UNRELIABLE — INSUFFICIENT EVIDENCE`, and readiness remains **EXPERIMENTAL**. `docs/readiness.md` was intentionally not changed.
