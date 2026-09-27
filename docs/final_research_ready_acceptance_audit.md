# Final Independent Research-Ready Acceptance Audit

Audit date: 2026-09-28 (Asia/Tashkent)  
Audited checkpoint: `87b1eb7d12b64f107d882c476c97ca302d7f35b0`  
Audit mode: read-only red-team verification

## Final verdict

**B. RESEARCH_READY CLAIM INVALIDATED BY CRITICAL/HIGH DEFECT**

The IPKY residual-income arithmetic is reproducible and the current database is conservative about investment eligibility. However, the accepted Git checkpoint does not contain the readiness rubric or two hardening fixes on which the closure relies, exact valuation lineage omits material ROE inputs, and the fourth factor is unavailable because of a demonstrated integration defect rather than solely missing evidence. These defects prevent the accepted checkpoint from satisfying its own traceability and “no silent correctness defect” requirements.

This verdict does not say IPKY is attractive, unattractive, or wrongly priced. It says the `RESEARCH_READY` milestone is not yet independently reproducible from the accepted checkpoint.

## Audit scope and method

The audit reconstructed the claim from the production SQLite database, committed code at the accepted SHA, current working code, source hashes, valuation/assumption records, factor and signal rows, pipeline records, prospective snapshots, and isolated tests. It did not refresh sources, alter a gate, modify production data, rerun Phases 13–15, or remediate a defect.

Two test contexts were kept separate:

- Current working tree: 204 passed, 0 failed, 0 skipped, no warnings reported.
- Clean archive of accepted commit `87b1eb7`: 201 passed, 0 failed. It does not contain three later adversarial tests.
- Clean accepted commit plus the current hardening test file: 13 passed and **4 failed**. Failures reproduce rollback loss of breaking-schema evidence and overbroad signal lineage.
- Production foreign-key check: 0 violations.

## Independent readiness reconstruction

The closure document applies an eight-item rubric from the current working copy of `docs/readiness.md`. That file is modified but uncommitted. At accepted commit `87b1eb7`, `docs/readiness.md` instead classifies the system `EXPERIMENTAL` and contains a different seven-item remediation rubric. Therefore the accepted checkpoint does not preserve the governing standard used to declare itself research-ready.

Against the intended eight-item rubric reconstructed from the working copy:

| Requirement | Independent result | Reason |
|---|---|---|
| Legitimate current source and stable fresh cycles | PASS WITH OPERATIONAL QUALIFICATION | All 17 `pipeline_health` rows are `HEALTHY`; two full 17-pipeline cycles exist on 2026-09-26 and 15 due pipelines ran successfully on 2026-09-27 while two weekly pipelines remained fresh. One old ingestion run is stranded as `RUNNING`. |
| Minimum viable source-traceable evidence cohort | PARTIAL | IPKY has substantial verified evidence, but the valuation/signal lineage does not include all source values used to derive ROE. |
| Units and perimeter resolved for valuation statements | PASS | The used audited PDF explicitly states consolidated IFRS and million UZS; stored normalized values are UZS. |
| Preferred rights for a preferred valuation | NOT EVALUABLE / NOT REQUIRED | IPKY is common equity. No preferred valuation is claimed. |
| Explicit consistent assumptions and independent reconciliation | PARTIAL | Assumption values and methods are stored and arithmetic reconciles; the 2021 opening equity used in 2022 ROE is hard-coded and lacks a normalized observation/assumption lineage record. |
| Exact signal lineage and durable breaking-schema evidence | FAIL | Required fixes are absent from the accepted commit. Clean-checkpoint adversarial tests fail. Current IPKY lineage also omits comparative/opening-equity inputs used for ROE. |
| No unresolved silent correctness defect | FAIL | The fundamental engine fails to construct Average Equity despite compatible verified observations, artificially suppressing the Quality factor and potentially changing the research state. |
| Independent current audit | FAIL by verdict | This audit found HIGH defects. |

The documented result and reconstructed result therefore do not agree.

## IPKY valuation forensic trace

### Identity and security

- Security ID: `9922a46f-208e-50f4-a367-4930fa116e60`.
- Issuer ID: `487ac1c0-869d-5afe-bff9-541534e376e9`.
- Class: `COMMON`; currency: UZS.
- Repeated RSE records link ticker `IPKY` and ISIN `UZ7039920002` to the same security.
- Verified shares: 60,239,945,264; nominal value 10 UZS; effective/disclosed 2026-09-14.

The present identity is corroborated. However, the targeted valuation ingestion helper selects the security by latest ticker alone and places a hard-coded ISIN into evidence rather than resolving and testing ticker plus ISIN as of the disclosure date. That bypass is a latent identity-control defect even though it did not produce a demonstrated current mismatch.

### Financial evidence

- Audited PDF document: `7c1e86df-7f87-57b0-9d62-3f92b0f7634a`.
- Raw document: `0ca469d0-ecca-5875-94a8-1c11d1f6fb77`.
- Source: official Openinfo attachment; publication date 2024-12-11; retrieval 2026-09-27T13:03:03Z.
- Stored SHA-256 `240286e90cf9bcc846b2966fcf9bba62ceda418c35de27814c09d94d3487db6f` matches the archived file.
- Explicit evidence: IFRS, consolidated perimeter, million Uzbek soum.
- Reported and normalized values include 2022/2023 equity and net income in UZS.

No unit, currency, perimeter, issuer, or share-class mismatch was reproduced.

### Assumptions and point in time

- 2023 equity: 2,817,695,000,000 UZS.
- 2022 equity: 2,133,021,000,000 UZS.
- 2023 net income: 731,342,000,000 UZS.
- 2022 net income: 522,935,000,000 UZS.
- 2021 opening equity used by code: 1,491,673,000,000 UZS.
- CBU curve date: 2026-09-23; retrieved 2026-09-27T12:39:52Z; nominal UZS; continuous compounding; 3,653-day zero rate 16.96054015902%.
- Effective government reference: 18.4837224179%.
- Base cost of equity: 22.2410224179%, calculated as effective government reference minus 3.06% default spread plus 0.51 × 4.23% mature ERP plus 4.66% country-risk premium.
- Growth: 4% / 5% / 6%, identified as configurable nominal research assumptions around the cited CBU target.

Financial publication, curve, shares, market price, and assumption dates precede the 2026-09-28 research date. No actual future-dated input was found. The report is stale, but staleness is disclosed through LOW valuation confidence.

The country-risk construction is explicit and arithmetically avoids adding both the full sovereign-bearing government yield and the country-risk premium without an offset. Its economic specification remains a LOW-confidence model assumption, not an observed WACC.

### Independent recalculation

Using a separately written five-year residual-income calculation with the stored scenario inputs produced:

| Scenario | Independent value/share | Stored value/share | Difference |
|---|---:|---:|---:|
| Bear | 57.6098572111716 | 57.6098572111716 | immaterial |
| Base | 66.0939781562458 | 66.0939781562458 | immaterial |
| Bull | 78.3092595811942 | 78.3092595811942 | immaterial |

The formula, compounding conversion, scenario ordering, and per-share denominator reproduce. The valuation is mathematically valid conditional on its inputs.

### Valuation-lineage defect

The current residual-income valuation links exactly two immutable financial versions: 2023 Equity and 2023 Net Income. The stored ROE assumptions also use 2022 Equity, 2022 Net Income, and 2021 opening Equity. The 2022 observations exist but are not linked through the valuation/signal lineage; the 2021 opening equity is hard-coded in `targeted_valuation_unlock.py` and is neither stored as a normalized observation nor exposed in the assumption derivation JSON. Therefore the claimed exact backward chain is incomplete.

## Pipeline-health verification

The literal health-table claim is true at audit time:

- `HEALTHY`: 17
- `FAILED`, `DEGRADED`, `STALE`: 0 current health rows
- Current health rows have no retry failure or stale dependency.
- Latest RSE security-master and market ingestion runs succeeded; the latest market run processed 126 rows for seven requested/seven successful securities.

Operational qualifications found outside `pipeline_health`:

- 1 `ingestion_runs` row has remained `RUNNING` since 2026-09-26T20:39:59Z.
- 1,804 history-acquisition jobs are `PENDING`, 1 is `SOURCE_BLOCKED`, 61 imported, and 34 empty.
- 3 HIGH signal-state alerts and 1 HIGH market anomaly remain open, alongside 83 warning alerts and 82 medium anomalies.
- Historical failed/stale/degraded scheduled runs are preserved, as they should be.

The open alerts are not hidden failed pipeline dependencies and do not by themselves falsify IPKY research. The stranded run shows that `17/17 HEALTHY` is a scheduler-health statement, not a complete operational-cleanliness statement.

## Data-lineage verification

Verified chains:

- 2023 Equity/Net Income → immutable normalized versions → audited document → hash-verified raw PDF → official Openinfo URL.
- RSE market observation → source/run IDs → official public RSE source.
- CBU curve point → curve vintage → official API URL and retrieval timestamp.
- Shares → verified share-capital observation → official RSE issue URL.

Broken or incomplete chains:

- 2022 Equity and Net Income used in modeled ROE are not included in the valuation/signal exact lineage.
- 2021 opening Equity is a literal in code rather than a first-class sourced observation.
- Assumption records have URLs and derivation values but no relational links to the exact source record/version for every financial input.
- At the accepted commit, prospective capture labels every issuer observation as `EXACT`; the uncommitted working fix narrows this, but is not part of the checkpoint.

## Factor-gate verification

The stored current signal has confidence 58.75, no triggered hard gate, null attractiveness, and `DATA_INSUFFICIENT`. The minimum remains four positively weighted factors.

| Factor | Stored status | Independent assessment |
|---|---|---|
| Valuation | AVAILABLE, score 0 | Legitimately available; base value 66.094 versus observed 211 UZS gives -68.6758% and the documented cap produces 0. |
| Liquidity | AVAILABLE, score 60 | Legitimately available for descriptive research, LOW confidence; capacity is not validated. |
| Data Quality | AVAILABLE, score 90 | Reproduces from documented penalties, chiefly unknown ownership. |
| Growth | UNAVAILABLE | Supported growth inputs are absent. |
| Momentum | UNAVAILABLE | Correctly unavailable because no verified corporate-action-adjusted return series exists; raw count alone is insufficient. |
| Dividend | UNAVAILABLE | No date-compatible class-specific dividend score. |
| Governance | UNAVAILABLE | No directionally supported governance evidence; absence is not a positive score. |
| Catalyst | UNAVAILABLE | No directionally supported catalyst. |
| Balance-Sheet Risk | UNAVAILABLE | NPL/capital-adequacy inputs are absent. |
| Quality | UNAVAILABLE | **Not solely a data limitation.** Audited 2022/2023 equity and 2023 net income support a 2023 average-equity ROE, already calculated by the valuation workflow. The fundamental engine requires an `Average Equity` concept but never constructs it from compatible periods. |

The Quality integration defect is material. If the verified ROE were correctly emitted as a fundamental metric, Quality would become the fourth positively weighted factor. The unchanged aggregation rule could then produce a non-null attractiveness and a different research state. This audit does not calculate or force that production result; it establishes that the present `DATA_INSUFFICIENT / NO ACTION` path is not proven to be caused only by missing evidence.

## Failure-mode verification

Current working-tree tests cover fail-closed behavior for RSE/Openinfo/CBU failures, schema changes, ambiguous identities, wrong identifiers, unknown units/perimeters, stale prices, and missing valuation inputs. Missing data generally returns unavailable/insufficient rather than fabricated values.

The accepted commit itself fails the newer adversarial checks for two controls:

1. A breaking source-schema check, anomaly, alert, and failed-health state can be rolled back by the caller, erasing the forensic evidence.
2. Prospective signal lineage can label unrelated observations from the same issuer as `EXACT`.

These are not hypothetical documentation differences: four tests fail when the current hardening test file is run against a clean archive of the accepted SHA.

## Research/investment and scope separation

The architecture correctly allows valuation availability, LOW confidence, `DATA_INSUFFICIENT`, and no order to coexist. `RESEARCH_READY` does not inherently mean BUY/HOLD/ACCUMULATE, portfolio eligibility, paper readiness, capital readiness, or live-trading readiness.

Scope conclusions:

- IPKY: evidence supports a substantial but not yet acceptance-grade traceable research pack because of lineage and factor-integration defects.
- Five-target forensic cohort: not research-ready; only IPKY has an available valuation.
- Entire RSE universe: not research-ready; no evidence supports that generalization.

The wording “limited IPKY cohort” is appropriately narrow in intent, but the milestone still fails because the implementation evidence for IPKY is incomplete.

## Higher-tier separation

The following remain genuine higher-tier limitations and are not treated as software defects in this verdict: historical strategy validation, a longer prospective sample, paper orders/fills/outcomes, market-depth evidence, free float, calibrated capacity, portfolio validation, backup/restore, external alert delivery, authentication/authorization, deployment supervision, and formal operating governance.

## Findings

### HIGH-1 — Accepted checkpoint is not self-contained

The committed `docs/readiness.md` still says `EXPERIMENTAL` and contains a different rubric. The 204-test claim and key hardening behavior depend on uncommitted files. A clean checkpoint runs 201 tests, not 204. This prevents independent reproduction of the accepted milestone.

### HIGH-2 — Required schema and exact-lineage fixes are absent from the accepted commit

Clean-checkpoint adversarial execution produces four failures. Breaking-schema evidence is rollback-vulnerable and prospective signal lineage is overbroad. Both directly contradict readiness requirements 6 and 7.

### HIGH-3 — IPKY valuation lineage omits material ROE inputs

Only 2023 Equity and Net Income are linked. Comparative 2022 values and hard-coded 2021 opening equity materially determine the ROE scenarios but are not all preserved as exact source-linked valuation inputs.

### HIGH-4 — Quality factor is unavailable because of an integration defect

Compatible verified periods support 2023 ROE, and the valuation workflow already derives it. The generic fundamentals engine never creates Average Equity, so it returns `MISSING_INPUT`. This can suppress the fourth factor and materially alter IPKY's final research classification.

### MEDIUM-1 — Targeted identity lookup bypasses corroborated resolution

The targeted workflow selects the latest `IPKY` ticker and hard-codes the expected ISIN in evidence rather than resolving ticker plus ISIN/effective date through the canonical resolver. Current identity is correct, but the path does not enforce the permanent identity rule.

### MEDIUM-2 — Scheduler health omits stranded and queued operational work

Seventeen health rows are green while one ingestion run is stranded and 1,805 acquisition jobs are pending or blocked. The health statement should be interpreted narrowly.

### OBSERVATION-1 — Open alerts and anomalies are preserved

The open HIGH and warning records are historical research/market alerts, not concealed current pipeline failures. Their preservation is appropriate, but “healthy” must not imply they were resolved.

## Smallest exact corrective action

Create one corrective checkpoint that:

1. commits the already-tested schema-forensics and exact-signal-lineage fixes and the actual governing readiness rubric;
2. resolves IPKY through corroborated ticker+ISIN evidence;
3. stores and links every ROE input, including opening/comparative equity, as immutable sourced observations/assumption lineage;
4. constructs average equity and ROE in the fundamental engine from compatible periods, then reruns factors and records whatever unchanged gates produce; and
5. closes or explicitly marks the stranded ingestion run before repeating this acceptance audit from a clean checkout.

No threshold, gate, valuation confidence, or readiness criterion needs to change. No new issuer, UI, news engine, or trading capability is required.

The research-readiness backend milestone must **not** be frozen at checkpoint `87b1eb7`.
