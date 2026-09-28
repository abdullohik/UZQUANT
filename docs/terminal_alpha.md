# UZQUANT Terminal Alpha

## Purpose

Terminal Alpha is the local, read-only research interface for the accepted UZQUANT backend. It presents stored production evidence without recalculating valuation, factor scores, confidence, signals, or risk gates in the browser.

The interface does not execute orders, modify research records, or bypass `DATA_INSUFFICIENT`, liquidity, governance, confidence, or model-risk controls.

## Start locally

From the repository root:

```bash
python3 -m uzquant serve-research --host 127.0.0.1 --port 8765
```

Then open <http://127.0.0.1:8765/>.

The service binds to localhost by default. It is not configured as an internet-facing deployment.

## Screens

- **Market Overview** — pipeline health, coverage, current signal distribution, latest observed market data, valuation availability, alerts, and recovery evidence.
- **Market Screener** — sortable and filterable security universe with share class, current price, liquidity state, valuation status, factor coverage, confidence, signal, freshness, and research coverage.
- **Security Research** — stored market history, market-quality evidence, normalized fundamentals, source reports, factor records, risk gates, and source provenance for a selected security.
- **Valuation Lab** — stored bear/base/bull results, model method and confidence, exact assumptions, and rejected-method reasons. Production values are read-only; no browser-side valuation model exists.
- **Evidence Lineage** — exact signal dependencies through factor records, financial metrics, valuation assumptions, immutable normalized observations, raw evidence, and source documents.
- **System Health** — pipeline status, ingestion/backfill evidence, prospective snapshots, alerts, state transitions, and validation results.

## Read-only API surface

The terminal uses these versioned GET endpoints:

- `/api/v1/overview`
- `/api/v1/universe`
- `/api/v1/securities/{ticker}`
- `/api/v1/securities/{ticker}/lineage`
- `/api/v1/health`
- `/api/v1/validation`

Existing structured errors and as-of semantics remain authoritative. No mutating endpoint is exposed.

## Evidence policy

- Raw observed market data is identified as raw and is never presented as an adjusted or total-return series.
- Missing values remain unavailable; the interface does not interpolate or invent them.
- `RESEARCH_READY` applies only to the accepted limited cohort and is displayed separately from signal state.
- A stored signal such as `REDUCE` is research classification output, not an executable order or personalized recommendation.
- Lineage is sourced from backend dependency records. Presentation sorting, filtering, formatting, and chart scaling do not alter analytical values.

## Current limitations

- The formal status remains **RESEARCH_READY — LIMITED IPKY COHORT**. Most securities remain partial or data-insufficient.
- Only IPKY currently has an available, independently reconciled production valuation and complete positive-factor minimum.
- The price chart is a presentation of stored raw observations, not a technical-analysis or total-return chart.
- The valuation laboratory is intentionally read-only. A future isolated scenario sandbox is reserved but not implemented.
- This local interface has no authentication or internet deployment hardening. It must remain localhost-only until those controls are added and reviewed.
- The terminal does not provide brokerage connectivity, trade execution, or autonomous trading.
