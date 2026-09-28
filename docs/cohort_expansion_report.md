# Cohort Expansion Report

Generated: 2026-09-28T11:03:21.629880+00:00  
Version: `cohort-readiness/1.0.0`

## Result

This sprint ranks and audits the full security universe using data readiness only. It does not change any valuation, factor, confidence, signal, liquidity, or readiness rule. Missing evidence remains missing.

| Measure | Result |
| --- | --- |
| evaluated | 76 |
| selected | 20 |
| executable_valuations | 1 |
| factor_coverage_4_plus | 4 |
| non_insufficient_states | 4 |
| data_insufficient | 16 |
| valuation_insufficient | 19 |
| security_rights_blocked | 4 |
| financial_metadata_blocked | 18 |
| terminal_visible | 76 |
| fully_researchable | ['IPKY'] |
| closest_to_researchable | ['UZTL', 'KASU', 'QZSM', 'AGMKP', 'KASUP'] |
| blockers_by_category | {'DATA_ALREADY_PRESENT_NOT_NORMALIZED': 5, 'PARSER_GAP': 0, 'METADATA_GAP': 18, 'MODEL_INTEGRATION_GAP': 8, 'DERIVED_METRIC_GAP': 0, 'PUBLIC_DATA_NOT_YET_COLLECTED': 20, 'PUBLIC_SOURCE_EXHAUSTED': 0, 'REQUIRES_AUTHORIZED_SOURCE': 0, 'REQUIRES_TIME': 0, 'GENUINELY_UNAVAILABLE': 0} |
| market_observations | 830 |
| rse_history_queue | {'EMPTY': 36, 'IMPORTED': 79, 'PENDING': 1784, 'SOURCE_BLOCKED': 1} |
| valuation_method_assessments | 194 |
| foreign_key_violations | 0 |

## Bounded acquisition

The existing official RSE HTML importer was run for one bounded batch over the selected cohort. Eighteen jobs imported verified trades and two were correctly recorded empty. No broad crawler, guessed endpoint, or access-control bypass was used.

## Correctness defect fixed

The valuation eligibility runner was structurally hard-coded to five ticker symbols. It now accepts an explicit readiness-selected cohort and applies the pre-existing sector routing and methods. Preferred-rights gating is now based on the stored security class and authoritative rights record rather than two hard-coded preferred tickers. Formulas, assumptions, weights, thresholds, and gates are unchanged.

## Interpretation

The selected list is a recovery and normalization worklist, not a list of attractive securities. A selected security remains `DATA_INSUFFICIENT` or `VALUATION_INSUFFICIENT` wherever the stored evidence cannot support a conclusion. The dominant remaining blockers are missing authoritative financial metadata, unnormalized statement concepts, verified security-specific rights, credible peers/assumptions, and uncollected public filings for the lower-readiness names.
