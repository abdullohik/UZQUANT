# Post-audit identity forensic trace

Generated from the production database after migrations 028–030 and the scoped identity audit. Historical analytical rows are shown for lineage only; the current failed/stale pipeline state still blocks execution.

## Five-target chain

| Ticker | Source | Legacy issuer ID | Canonical issuer ID | Security ID | Class | ISIN | Verified reports | Normalized observations | Fundamental metrics | Valuations | Factors | Signals | Latest stored signal | Current prospective admission |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| AGMKP | RSE / Openinfo | `f3273f20-e10c-5cce-baa3-f5462c0e18ef` | `da30f3ae0cd8a50c5ce15b9e997c49cd` | `de64eadf-d7a2-5744-b5d6-208d7c772148` | PREFERRED | `UZ700055K015` | 2 | 46 | 66 | 9 | 150 | 15 | DATA_INSUFFICIENT | STALE_BLOCKED |
| KASUP | RSE / Openinfo | `8ba46025-25d4-5ba1-b383-12022c199ab0` | `2b3d2a07a861095ec4e2198e6bb8b260` | `37a67d28-d290-5adc-a757-2e00570865c1` | PREFERRED | `UZ702866K013` | 3 | 84 | 57 | 7 | 150 | 15 | DATA_INSUFFICIENT | STALE_BLOCKED |
| IPKY | RSE / Openinfo | `487ac1c0-869d-5afe-bff9-541534e376e9` | `ee9eda21846107ce8bf038f1c89a6929` | `9922a46f-208e-50f4-a367-4930fa116e60` | COMMON | `UZ7039920002` | 3 | 39 | 72 | 7 | 150 | 15 | DATA_INSUFFICIENT | STALE_BLOCKED |
| UZTL | RSE / Openinfo | `3dd2e6b9-25f8-5303-b252-b69f4f7664fa` | `5cc7a55eaf4681b4e618ed4366f6c35e` | `c9918d32-fa6e-51fb-af55-794929eb90e0` | COMMON | `UZ7047110000` | 2 | 46 | 66 | 9 | 150 | 15 | HOLD | STALE_BLOCKED |
| QZSM | RSE / Openinfo | `8f85eccf-f5d8-5711-af69-3366a08d9eb0` | `cf602ec2fdae4b373dfe0e46f9197d67` | `fd1dc881-f47d-5c8b-b00c-a518cc5186c6` | COMMON | `UZ7029000005` | 2 | 46 | 66 | 9 | 150 | 15 | DATA_INSUFFICIENT | STALE_BLOCKED |

Each report count includes only `financial_document_identity_assignments.assignment_status = VERIFIED`. Each verified assignment contains the ticker evidence ID, ISIN evidence ID, publication date, resolved security ID, canonical issuer ID, source identifier, method, and assignment timestamp.

UZTL's historical stored `HOLD` does not authorize a paper order: its prospective state remains `STALE_BLOCKED` because the security master is `FAILED`, all dependent research layers are `STALE`, the model is not validated, and valuation remains insufficient.

## Multiple-security safety

| Issuer pair | Common security | Preferred security | Relationship |
|---|---|---|---|
| AGMK / AGMKP | AGMK, ISIN `UZ7000550002`, COMMON | AGMKP, ISIN `UZ700055K015`, PREFERRED | Same canonical issuer; distinct security IDs and identifier histories |
| KASU / KASUP | KASU, ISIN `UZ7028660007`, COMMON | KASUP, ISIN `UZ702866K013`, PREFERRED | Same canonical issuer; distinct security IDs and identifier histories |

Issuer-level reports may feed issuer fundamentals, while price, market history, rights, dividends, liquidity, valuation adjustments, factors, and signals remain keyed to the individual security.

## Quarantine and invalidation trace

Five earlier documents with `financial_document_entity_checks.validation_status = MISMATCH` could not be corroborated by the verified report catalog. They now have assignment status `QUARANTINED`. The source documents and 588 raw extracted rows remain immutable. Eighty-one dependent normalized observations are listed in `analytical_identity_invalidations` and are excluded by production query gates. There were no dependent fundamental metrics to recompute and no corrected source identity with which to recompute the observations.

## Current operational evidence

| Health state | Count |
|---|---:|
| FAILED | 1 |
| DEGRADED | 1 |
| STALE | 15 |

The security master remains `FAILED` after the genuine RSE outage; macro remains `DEGRADED`; all dependent research pipelines remain `STALE`. Historical degraded evidence, the seven `STALE_BLOCKED` Phase 18 security states, three zero-position shadow portfolios, zero paper orders/fills, and 100% cash are preserved unchanged.

## Re-audit conclusion

The critical identity exploit is no longer reproducible through production paths. The database has 55 auditable legacy-to-canonical issuer mappings, no null canonical issuer IDs, and zero foreign-key violations. The system fails closed for ambiguity, disagreement, missing mappings, and out-of-range identifiers. Final readiness remains **EXPERIMENTAL** because the four HIGH findings and source/model limitations remain.
