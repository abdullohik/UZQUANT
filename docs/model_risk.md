# UZQUANT Model Risk Register

## Governing conclusion

Model risk is dominated by sparse evidence and absent performance validation, not measured return instability. Current monitored pipelines are healthy, but freshness does not create missing historical, ownership, rights, or execution evidence. Absence of observed strategy failure must not be interpreted as robustness. Historical Phase 19 findings remain preserved in `docs/final_audit.md`; their current dispositions are recorded below.

| Risk | Severity | Current evidence | Control | Residual risk |
|---|---|---|---|---|
| Issuer collision / report misassignment | RESOLVED correctness finding | Canonical identity forensic retest passed; ambiguous reports quarantined | Opaque issuer IDs, effective-dated identifier evidence, ticker+ISIN corroboration | Historical ambiguous documents remain quarantined |
| Normalized financial reinterpretation | RESOLVED correctness finding | 342 immutable versions; mutation/deletion triggers pass | Append-only versions and analytical lineage | Historical pre-version lineage is `LEGACY_INFERRED` |
| Source format drift | CONTROL IMPLEMENTED; operational validation pending | Production parser contracts and adversarial tests pass; zero real post-migration checks | Raw archive, semantic contract, fail-closed schema check, durable failure evidence | Needs a legitimate real source cycle |
| Degraded upstream propagation | RESOLVED correctness finding | Scheduler/API tests cover propagation and recovery; current health is 17/17 `HEALTHY` | Shared health context and dependency propagation | A future partial-source incident still requires normal operational monitoring |
| Prospective financial freeze | RESOLVED for new snapshots | Full-freeze reconstruction tests pass | Immutable hashed `FULL_FREEZE_V1` payload | Original snapshot remains `LEGACY_SNAPSHOT_LIMITED` |
| Exact prospective signal lineage | RESOLVED for new snapshots | Negative test excludes unrelated issuer observations | Factor/metric/valuation traversal to exact immutable versions | No new real full-freeze production snapshot yet |
| Breaking schema evidence rollback | RESOLVED in code | Adversarial caller-rollback test passes | Forensic evidence commits before parser abort | No real schema failure after repair yet |
| Wrong units/currency/perimeter | HIGH inherent, currently gated | 81 unspecified units; 16 unknown perimeters | Valuation returns insufficient; TTM/FX checks | Prevents valuation rather than producing an observed wrong value |
| Preferred rights/value allocation | HIGH inherent, currently gated | Preferred rights low/missing | Rights-specific gates and valuation insufficiency | No preferred valuation can be relied upon |
| Share-count conflict | HIGH latent | No current same-date conflict | Verified/effective-date filter | No authority/tie-break rule for a future verified conflict |
| Liquidity/execution error | HIGH inherent | No spread/depth history | Participation limits, no-fill, stale gates | Slippage and capacity cannot be empirically calibrated |
| Survivorship/lookahead | HIGH inherent | Universe and vintages incomplete | Backtest refuses to run | Strategy validity remains unknown |
| Parameter/selection overfit | HIGH untestable | Zero completed backtests/OOS periods | Experiment registry and locked OOS design | Cannot be measured |
| Macro vintage error | MEDIUM-HIGH | Release/revision dates missing | First-observed append-only vintage | Historical real-time macro state incomplete |
| Event classification | MEDIUM | Current events deterministic and sourced | Evidence/method/confidence retained | Sparse coverage; no LLM error sample |
| Portfolio concentration/correlation | MEDIUM latent | No real positions | Transparent caps and conservative missing-correlation handling | Real interaction untested |
| Confidence miscalibration | HIGH untestable | Zero prospective outcomes | Separate confidence and sample-size fields | Cannot be calibrated yet |
| Production operations | MEDIUM for local research; HIGH for hosted service | No auth, backup drill, supervision, or alert delivery | Local binding and read-only API | Not suitable for dependable multi-user deployment |

## Model-risk interpretation

The model is neither shown to be good nor bad. It is unvalidated. The next material reduction in model risk requires legitimate current-source recovery, valuation-ready evidence, historical point-in-time coverage where available, and prospective accumulation—not parameter tuning against the current sample.
