# UZQUANT Readiness Classification

## Classification

**EXPERIMENTAL**

This classification applies to the research infrastructure only. It does not authorize autonomous execution, live trading, or use of real capital.

## Why this classification

UZQUANT has reproducible schemas, provenance, deterministic calculations, explicit missing-data states, risk gates, source-failure propagation, immutable prospective snapshots, and a 158-test suite. Its response to the real RSE outage was correct and conservative.

However, the audit reproduced a critical canonical-identity defect: issuer identity is based on normalized name and financial-document assignment is ticker-only rather than effective-dated and corroborated. A research system cannot be classified `RESEARCH_READY` while a plausible collision can silently contaminate issuer financials and every downstream layer.

Independent additional blockers include mutable normalized-financial lineage, incomplete source-schema integration, degraded-state propagation gaps, no available real valuation, only 20 market dates, no valid backtest/OOS evidence, zero prospective fills/outcomes, and major rights/ownership/execution-data gaps.

## Requirements for RESEARCH_READY

1. Replace name-derived issuer identity with authoritative permanent identifiers and explicit unresolved conflicts.
2. Resolve ticker/ISIN as of the disclosure date and require corroborating issuer evidence for report assignment.
3. Version normalized observations and preserve the exact version referenced by every analytical/prospective snapshot.
4. Wire fail-closed source-schema checks into each production parser and surface `DEGRADED` lineage downstream.
5. Re-ingest and independently reconcile the priority issuer/security set after the identity migration.
6. Add adversarial tests for exact-name collision, historical ticker reuse, misassigned documents, and conflicting verified share counts.
7. Complete a new red-team audit with no critical findings.

Even after those items, `PAPER_TRADING_READY` would require a stable operational source cycle, verified fee assumptions, repeated prospective snapshots, actual no-fill/partial-fill observations, and sufficient elapsed evidence. Higher classifications would additionally require reliable valuations, broader verified rights/ownership coverage, valid historical or prospective validation, and operational hardening.
