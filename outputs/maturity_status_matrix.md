# UZQUANT Maturity Status Matrix

| Dimension | Status | Basis | What would be required next |
|---|---|---|---|
| BUILD_STATUS | BUILD_COMPLETE_BUT_EVIDENCE_LIMITED | Core research, valuation, controls, operations, audit lineage, and prospective capture work; tests and FK checks pass | Maintain rather than broaden indiscriminately |
| RESEARCH_READY | PASS_LIMITED_IPKY_COHORT | One complete, source-traceable company research pack; healthy current operation; valid reconciled valuation; explicit limitations | Add issuer breadth when justified, without changing this minimum proof |
| PAPER_TRADING_READY | FAIL | Only 2 full-freeze snapshots over ~24h25m; 0 orders, fills, positions, and outcomes; execution mechanics not empirically verified | Time, repeated snapshots, observed outcomes, fees/mechanics evidence, backup/scheduling/alert controls |
| LIMITED_CAPITAL_READY | FAIL | Strategy is not validated; capacity and execution evidence are insufficient; no mature paper sample | Valid model evidence, operational controls, empirically supported capacity, formal authorization |
| PRODUCTION_READY | FAIL | Breadth, validation, security, governance, disaster recovery, and operating evidence remain insufficient | Formal controls, broader reliable evidence, validation, monitoring, governance, and explicit approval |

The earlier single `EXPERIMENTAL` label mixed these dimensions. Under the existing rubric, the build can be research-ready for a narrow cohort while remaining wholly unready for paper maturity, capital use, or production trading.
