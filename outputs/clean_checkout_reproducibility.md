# Clean-Checkout Reproducibility

The corrective candidate is validated in two separate contexts.

| Context | Full suite | Adversarial subset | FK violations | IPKY reconstruction |
|---|---:|---:|---:|---|
| Development working tree | 206 passed | 32 passed | 0 | AVAILABLE valuation; 4 factors; `REDUCE` |
| Clean checkout of exact committed state | 206 passed | 32 passed | 0 | AVAILABLE valuation; 4 factors; `REDUCE` |

The clean validation uses a clean checkout of the candidate commit and a temporary copy of the production database. It applies committed migrations and runs fundamentals, valuation, ranking, valuation reconciliation, and the readiness evidence queries using only committed code. The source production database is not altered by the clean-checkout reconstruction.

The two contexts agree on valuation values, factor count, signal state, confidence, and foreign-key integrity. No required behavior depends on an uncommitted file.
