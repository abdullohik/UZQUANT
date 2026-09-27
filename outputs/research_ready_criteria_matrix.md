# Research-Ready Criteria Matrix

> Historical pre-correction matrix. See `outputs/research_ready_post_correction.md` for the current result.

| Requirement | Status | Launch critical | Classification if unresolved | Resolution in this closure |
|---|---|---|---|---|
| Legitimate current source and stable fresh cycles | PASS | Yes | CURRENT_OPERATION_FIXABLE | Current normal cycle succeeded; all 17 health rows healthy; repeated healthy cycles retained |
| Minimum viable source-traceable evidence cohort | PASS, LIMITED | Yes | PUBLIC_DATA_FIXABLE | IPKY is the one-security minimum viable common-equity cohort; no larger count exists in the rubric |
| Unit/perimeter resolved for statements used in valuation | PASS | Yes | PUBLIC_DATA_FIXABLE | IPKY residual-income inputs use only audited consolidated IFRS values normalized to UZS |
| Preferred rights for preferred valuation | NOT_EVALUABLE / NOT REQUIRED | Conditional | NOT_ACTUALLY_REQUIRED_FOR_RESEARCH_READY | No preferred security is valued in the cohort |
| Explicit/sourceable/consistent assumptions | PASS | Yes | MODEL/INTEGRATION_FIXABLE | Nine versioned assumptions; nominal UZS consistency; provenance classes retained |
| Independent valuation reconciliation | PASS | Yes | MODEL/INTEGRATION_FIXABLE | Exact match, maximum difference `0E-26` |
| Exact signal lineage and breaking-schema evidence | PASS | Yes | MODEL/INTEGRATION_FIXABLE | Post-hardening cycle, schema checks, immutable lineage, and `FULL_FREEZE_V1` evidence exist |
| No silent correctness defect | PASS | Yes | MODEL/INTEGRATION_FIXABLE | No open critical/high audit finding; momentum reason defect fixed and tested; fail-closed gaps remain explicit |
| Independent current audit | PASS | Yes | CURRENT_OPERATION_FIXABLE | Closure uses refreshed current database and source state |

## Items deliberately excluded from the research-ready gate

| Item | Current status | Why it does not block `RESEARCH_READY` |
|---|---|---|
| BUY/HOLD/ACCUMULATE state | IPKY `DATA_INSUFFICIENT` | A research system may validly reject a recommendation |
| Portfolio eligibility | Ineligible | Portfolio admission is downstream of research evidence |
| High valuation confidence | LOW | Confidence qualifies a valid valuation; it is not a mandatory-input test |
| Valid historical strategy | Phase 14 insufficient evidence | Required before strategy-performance claims, not a company report |
| Mature paper sample | Two full-freeze snapshots over ~24h25m | Required for paper-trading readiness |
| Positions/orders/fills | Zero | A no-trade result is valid and preserves fail-closed behavior |
| Wider universe valuation breadth | One available valuation | Required for broader/higher maturity, not proof of minimum research functionality |

Formal result: `RESEARCH_READY = PASS_LIMITED_IPKY_COHORT`.
