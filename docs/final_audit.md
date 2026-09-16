# Phase 19 — Independent Red-Team Audit

Audit date: 2026-09-16

Audited checkpoint: `82306c47d99c176fc07b3bce7d403cc4d89d4eaa`

## Executive conclusion

UZQUANT fails safely in its current real RSE outage: the security master remains `FAILED`, 15 dependent pipelines remain `STALE`, macro remains `DEGRADED`, all seven prospective security states remain `STALE_BLOCKED`, and all shadow portfolios remain 100% cash. The outage itself is not a product defect. Historical evidence was preserved and no order, fill, position, valuation, or backtest result was forced.

The audit nevertheless found a **CRITICAL entity-boundary defect**. The security master derives canonical issuer IDs from normalized legal name alone, and financial ingestion resolves a report to an issuer by ticker without an as-of validity test. A reproduced name collision generated the same issuer ID for two visually different names that normalize identically. This violates the permanent identity rules and could merge distinct issuers or assign a report to the wrong issuer. Accordingly, Phase 19 does not declare research readiness. Classification is `EXPERIMENTAL`.

No product code, model threshold, gate, source state, or UI behavior was changed during this audit.

## Severity summary

| Severity | Count | Result |
|---|---:|---|
| CRITICAL | 1 | Canonical issuer/report entity boundary is not safe under collision or historical ticker reuse |
| HIGH | 4 | Mutable normalized lineage; incomplete source-change integration; degraded-state propagation gaps; prospective financial snapshot not fully self-contained |
| MEDIUM | 5 | Source-priority policy not executable; sparse anomaly coverage; class/sector coverage gaps; incomplete dividend/corporate-action paper accounting; operational count semantics |
| LOW / informational | 6 | Documentation and interface breadth, external scheduling, alert delivery, sparse real sample, and similar disclosed constraints |

## Critical finding

### C-01 — Issuer identity can be silently merged or a report can be misassigned

Evidence:

- `uzquant/security_master.py:40` computes `issuer_id` as a stable hash of `normalize_name(issuer_display_name)`. It does not use a verified permanent issuer ID, tax/registration ID, exchange issuer ID, or an ambiguity record.
- The adversarial inputs `Example Bank AJ` and `<Example Bank> AJ` normalize to the same string and generated the same issuer UUID. The expected behavior was an unresolved collision; the actual behavior was silent equality.
- `uzquant/financial_documents.py:73-75` resolves an issuer with ticker alone and `ORDER BY known_at DESC LIMIT 1`; it does not apply `valid_from`, `valid_to`, report publication date, ISIN, registration/tax ID, or issuer evidence.
- `uzquant/financial_documents.py:86-89` considers the assignment matched when the expected ticker text occurs anywhere in the HTML. This is insufficient protection against historical ticker reuse or a misassigned page containing the ticker in navigation/related text.

Current production impact is not proven: no duplicate current ticker maps to multiple security IDs and no duplicate normalized legal-name issuer row exists in the stored database. The defect remains critical because it is a canonical ingestion boundary that can contaminate all downstream financial, valuation, factor, and signal records without necessarily triggering a gate.

Required before `RESEARCH_READY`:

1. canonical issuer IDs based on authoritative permanent identifiers or explicit unresolved mapping;
2. effective-dated ticker/ISIN resolution at the document publication date;
3. multi-field issuer verification for every financial document;
4. collision and historical ticker-reuse regression tests;
5. re-audit and re-ingestion after migration, without rewriting historical evidence silently.

## High findings

### H-01 — Normalized financial lineage is mutable

`uzquant/financial_documents.py:93` deletes all normalized observations for an existing document on reparse, and lines 99-100 update a logical observation in place. The raw document is immutable, but a later parser can change the normalized interpretation under the same document/observation identity. Historical analytical reconstruction and prospective references therefore cannot prove which normalized version was used solely from the observation ID.

### H-02 — Source-schema alerting is not integrated into production parsers

The generic `record_source_schema_check` fails closed and is tested, but it has no production caller outside its definition. Individual parsers often fail when required labels are absent, which is safer than silent success, but the promised centralized schema-change alert/audit path is not operational. The production database has zero `SOURCE_SCHEMA_CHANGE` alerts.

### H-03 — `DEGRADED` does not propagate as stale and is omitted from security warnings

The scheduler blocks dependants only for `FAILED` or `STALE`, not `DEGRADED` (`uzquant/operations.py:130`). Security API warnings similarly query only `STALE` and `FAILED` (`uzquant/research_api.py:134`). A partially failed upstream domain may therefore continue downstream without a prominent degraded warning. Current RSE failure is still handled correctly because it is `FAILED`, not merely degraded.

### H-04 — Prospective snapshots do not freeze the complete normalized financial payload

Phase 18 freezes document IDs and a compact financial-document state, plus factors/signals. It does not copy normalized financial observation values into the immutable snapshot. Combined with H-01, exact future reconstruction of the financial information known at a prospective decision time is incomplete.

## Audit by domain

### Source and provenance

All four registered sources are primary official sources. SQLite integrity and foreign-key checks pass. There are 152 raw snapshots and 141 distinct hashes; repeated raw content is retained as retrieval evidence rather than treated as a new fact. Publication-date checks found no financial report published after its retrieval date. No lower-authority stored source currently overrides a primary source because no secondary production source is registered. However, authority is metadata only; no generic conflict resolver enforces source priority.

### Entity and security master

Securities are stable by ISIN and common/preferred pairs for AGMK/AGMKP and KASU/KASUP remain distinct. No current ticker maps to two stored security IDs, and no unresolved production identity conflicts exist. There are 76 securities, but 67 retain `UNKNOWN` class. C-01 prevents acceptance of the issuer boundary.

### Financial data

The database has 17 financial documents, 12 matched entity checks, 342 normalized observations, and 30 available fundamental metrics. Sixteen documents have unknown reporting perimeter; 81 observations retain `SOURCE_UNIT_UNSPECIFIED`. Unit/currency/perimeter compatibility tests, TTM overlap/gap tests, FX mismatch tests, balance identities, and missing-value behavior fail closed. No real restatement sequence exists. H-01 remains unresolved.

### Security economics

Verified class-specific share observations exist for the seven researched securities, with no currently stored same-date conflicting verified values. Preferred rights remain low/missing confidence and correctly block or reduce conclusions. Ownership is present only for UZTL; free float and Top1/Top3 remain explicitly unavailable. Cross-class dividend tests pass. A future same-date verified share conflict has no general authority/tie-break resolver and must remain unresolved rather than be selected arbitrarily.

### Market data and liquidity

The database contains 140 raw observations: 120 reported trades and 20 explicit no-trade placeholders over 20 dates. There are no duplicate logical observations and no bid/ask history. No-trade observations do not fill orders, stale-price gates suppress execution confidence, participation limits constrain fills, and liquidity gates override attractive scores. Market history is too short for validation, and the current source is failed/stale.

### Valuation

All 41 stored valuation records are `VALUATION_INSUFFICIENT`; no Bear/Base/Bull value is fabricated. Missing perimeter, units, shares, preferred rights, CapEx/cash-flow concepts, peer multiples, discount-rate provenance, and country-risk inputs remain explicit. DCF/terminal-value, currency, FX, sector routing, negative earnings, and share-count mechanics are covered by tests. The audit could not manually reconcile a real available valuation because none exists.

### Events and governance

Five research events and three governance events use deterministic source mappings; no current event is LLM-derived. Each has source lineage. No event conflict is stored. The system therefore passes the no-LLM-fabrication check for current production data, while broad event coverage remains sparse.

### Macro

There are 259 observations across four verified series. All 259 have missing original release and revision dates and use first-observed-by-UZQUANT vintage timestamps. As-of querying excludes later ingested vintages and tests pass, but genuine real-time historical release/revision reconstruction is unavailable. Macro cannot independently generate a signal.

### Factors, confidence, gates, and signals

Raw metric JSON, transformation, factor status, scoring version, model versions, and snapshots are retained. Missing factors do not become average scores; no raw winsorization occurs; confidence is separate from attractiveness; and critical liquidity/data-quality/governance gates override tentative states. The latest real states are five `DATA_INSUFFICIENT`, one `HOLD`, and one `LIQUIDITY_TRAP`, all now prospectively `STALE_BLOCKED`.

### Backtest and model validation

Fourteen backtest-readiness rows are `DATA_INSUFFICIENT`; there are zero historical orders or fills. The framework tests filing/restatement/macro/action leakage, no-trade fills, participation limits, fees, delayed fills, and delistings. Phase 14 correctly remains `UNRELIABLE — INSUFFICIENT EVIDENCE`, failure type C. Lack of history is a source limitation, not a software failure or strategy failure.

### Portfolio and prospective shadow system

All 27 historical portfolio runs are 100% cash with zero positions. The three shadow portfolios remain degraded, unchanged at UZS 20 million cash each, with zero orders and fills. The initial immutable prospective snapshot has `FAILED` upstream state and seven `STALE_BLOCKED` security states. Snapshot future-signal and future-market-reference checks both returned zero violations. Immutability, partial fills, multi-day evidence, fees, dividends, model lineage, rejected stale orders, and persistent `NO_FILL` behavior pass tests, subject to H-04.

### Pipeline and software behavior

The full suite passed: **158 tests**. Database integrity and foreign keys pass. Source failure, parser failure, retry exhaustion, duplicate ingestion, staleness, missing fields, units, entity ambiguity, liquidity collapse, future leakage, and version lineage have test or adversarial coverage. The real RSE outage was handled correctly. Source schema integration and degraded propagation remain high findings.

## Adversarial scenario matrix

| Scenario | Result |
|---|---|
| Wrong ticker / historical reuse | **FAIL — CRITICAL:** report lookup is ticker-only and not effective-dated |
| Wrong ISIN | PASS for security identity: security IDs derive from ISIN; conflicts are recordable |
| Issuer-name collision | **FAIL — CRITICAL:** reproduced silent issuer-ID collision |
| Preferred/common mix-up | PASS for researched pairs; security IDs, rights, dividends, and shares are class-specific |
| Restatement leakage | PASS in point-in-time selector; no real restatement sequence available |
| 1000× unit error | PASS at valuation gate when units unverified; normalization versioning remains H-01 |
| Currency error | PASS: mismatched currency requires sourced FX |
| Misassigned report | **FAIL — part of C-01:** ticker text alone can mark a page matched |
| Share-count conflict | Current data clean; general conflict selection remains a documented model risk |
| Corporate action | Verified-only adjustment logic passes; history incomplete |
| Stale price | PASS: execution/gates block or reduce confidence |
| Failed source | PASS: retries exhausted, state failed, dependants stale, orders blocked |
| Parser format change | Unit helper passes; production alert integration fails H-02 |
| LLM classification error | Not applicable to current deterministic records; LLM-derived sample absent |
| Macro revision | Synthetic vintage test passes; real release/revision dates unavailable |
| Liquidity collapse | PASS: liquidity hard gate overrides attractiveness and position admission |
| Model-version mismatch | Captured versions are retained; exact normalized financial version remains incomplete H-04 |

## Final audit disposition

The system demonstrates strong fail-closed behavior, but C-01 is a correctness-threatening canonical-data defect. The audit therefore stops short of research readiness and does not authorize autonomous or live trading.
