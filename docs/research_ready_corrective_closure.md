# UZQUANT Research-Ready Corrective Closure

Date: 2026-09-28

Scope: corrections required by `docs/final_research_ready_acceptance_audit.md`

Result: **PASS — RESEARCH_READY, LIMITED IPKY COHORT**

## Working-tree delta classification

The accepted checkpoint omitted six tracked changes already present during its review. `uzquant/operations.py` and `uzquant/paper_trading.py` are `REQUIRED_FOR_CORRECTNESS`; `tests/test_high_findings_hardening.py` is `REQUIRED_FOR_TEST_COVERAGE`; and `docs/readiness.md`, `docs/known_limits.md`, and `docs/model_risk.md` are `READINESS_DOCUMENTATION`. This closure includes those files plus the narrowly scoped average-equity and valuation-lineage implementation, migration, tests, and required evidence outputs.

Unrelated pre-existing untracked data/import material, local databases, temporary/output material, unrelated audit drafts, and document artifacts are `DO_NOT_COMMIT`. `AGENTS.md` remains explicitly untracked and excluded.

## Why the accepted checkpoint had 201 tests

Commit `87b1eb7d12b64f107d882c476c97ca302d7f35b0` did not contain the three later adversarial tests in the working copy. The dirty working tree reported 204, while a clean checkout correctly discovered only 201. This closure adds the missing adversarial coverage plus two corrective regression tests, bringing the exact clean committed suite to 206.

## Four adversarial failures and corrections

1. Breaking-schema evidence was written inside the caller's transaction, so a later caller rollback erased the schema check, anomaly, alert, and failed health state. The enforcement boundary now commits forensic evidence before raising.
2. Security-master parser abort followed the same rollback path, losing its raw document and failed ingestion evidence. The same durable boundary preserves those records before control returns to the abort handler.
3. Full snapshot capture labeled all issuer observations `EXACT`, even when no factor or valuation referenced them. Capture now traverses exact factor/metric/valuation dependencies.
4. A later unrelated same-issuer observation could be included under the same overbroad issuer query. Exact traversal is tied to the selected signal and its versioned analytical records, excluding unrelated and future records.

The tests were retained and strengthened; expected outcomes were not relaxed.

## IPKY accounting and valuation correction

The official audited consolidated IFRS PDF contains 2021 opening equity, 2022/2023 equity, and 2022/2023 net income in million UZS. The parser now stores 2021 equity as raw evidence and an immutable normalized UZS observation. ROE assumptions relationally link every version used. The valuation record now includes all five exact financial versions.

For 2023, compatible adjacent equity observations support deterministic average equity of 2,475,358,000,000 UZS. Dividing audited 2023 net income of 731,342,000,000 UZS yields ROE 0.2954489815210567521950360312. Currency, unit, perimeter, accounting standard, audit status, and period compatibility are enforced; missing or mismatched inputs return unavailable.

The residual-income values are unchanged because the newly extracted 2021 value exactly matches the formerly embedded value. Reconciliation remains exact: bear 57.6098572111716, base 66.0939781562458, bull 78.3092595811942 UZS/share, LOW confidence.

## Ordinary factor and gate result

Quality changed from unavailable to score 29.54489815210567521950360312. The four available positively weighted factors are Valuation, Quality, Liquidity, and Data Quality. The required count remains exactly four. Growth, Momentum, Dividend, Governance, Catalyst, and Balance-Sheet Risk remain unavailable; no value was manufactured.

With no triggered hard risk gate, the unchanged scorer produced attractiveness 29.88622453802641880487590078, confidence 59.75, and state `REDUCE`. This is a research classification, not an executable order or recommendation.

## Operational reconciliation

The single stranded ingestion run `00353b54-826f-4fb7-9989-6dcab761c3e2` was explicitly closed as `FAILED` with reason `ABANDONED_STRANDED_RUN_RECONCILED_DURING_RESEARCH_READY_CORRECTIVE_CLOSURE`; no historical row was deleted. Remaining `RUNNING` ingestion runs: zero. Current monitored health remains 17/17 `HEALTHY`.

## Verification

- Focused adversarial/corrective tests: 32 passed.
- Development full suite: 206 passed.
- Clean committed checkout full suite: 206 passed.
- Clean committed checkout adversarial/corrective tests: 32 passed.
- Foreign-key violations: 0.
- Clean reconstruction: IPKY valuation AVAILABLE; reconciliation passed; four factors; `REDUCE`.

All current readiness artifacts now agree. Historical audits remain unchanged and are explicitly historical. The unchanged rubric supports `RESEARCH_READY — LIMITED IPKY COHORT`; higher maturity tiers remain failed.
