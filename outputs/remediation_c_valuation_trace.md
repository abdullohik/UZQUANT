# Remediation C Valuation Trace

## Production lineage

`raw_documents` → `financial_document_metadata_evidence` / `financial_document_entity_checks` → `financial_observations` → `fundamental_metrics` → `share_capital_observations` / `security_rights_assessments` → `valuation_model_attempts` / `valuation_records` → `factor_scores` → `research_signals`.

All financial inputs require an explicit MATCHED entity check. Exact effective-dated class shares are requested by `security_id`. Assumptions must carry an allowed provenance state and source; peer valuation additionally requires a versioned real peer set. Production model version is `sector-valuation/3.0.0`.

## Method results

Thirty-one method-specific production cases were evaluated: DDM 5; P/E 5; P/B 5; EV/EBITDA 3; EV/EBIT 3; FCF Yield 3; industrial DCF 2; residual income 2; mining scenario DCF 1; P/TBV 1; ROE-adjusted P/B 1. Result: **0 AVAILABLE, 31 VALUATION_INSUFFICIENT**.

| Security | Company inputs now available | Method trace | Exact remaining blockers |
|---|---|---|---|
| AGMKP | Revenue, Net Income, Equity, Cash, Debt and other statutory concepts; exact preferred shares | Seven mining/relative/dividend methods evaluated independently | all: unknown perimeter; relative methods: no sourced multiple; DCF: missing OCF/CapEx/D&A and discount-rate inputs; security-level methods: preferred rights incomplete |
| KASUP | Equity, Net Income, premiums/reserves and statutory lines normalized; exact preferred shares | Five insurance methods evaluated | unknown perimeter; no sourced multiple/cost of equity; preferred dividend/liquidation/conversion rights incomplete; insurance KPI combinations ambiguous |
| IPKY | Assets, Equity, Net Interest Income and other bank lines from three official workbooks; exact common shares | P/B, P/TBV, P/E, residual income and DDM evaluated | unknown perimeter; no sourced multiple/cost of equity; P/E additionally lacks normalized Net Income |
| UZTL | Revenue, Net Income, Equity, Cash and Debt; exact common shares | Seven industrial methods evaluated | unknown perimeter; no sourced multiple; DCF missing OCF/CapEx/D&A and discount-rate inputs |
| QZSM | Revenue, Net Income, Equity, Cash and Debt; exact common shares | Seven industrial methods evaluated | same as UZTL |

## Scenario and consensus controls

The execution engine creates Bear/Base/Bull only from explicitly supplied scenario assumptions. It does not apply mechanical ±20% bands. Synthetic regression tests prove exact-share P/E/P/B arithmetic, monotonic scenarios, preferred-security gating, provenance validation, and confidence-weighted consensus. No real reconciliation was required because no production valuation passed eligibility; fabricating assumptions solely to exercise reconciliation would violate the accuracy rules.

## Conclusion

The former orchestration defect is closed: a fully eligible input set can now execute and persist. Current zero valuations are evidence-driven rejections, not a hardcoded unavailable state.
