# Phase 16 — Research API and Functional Interface

## Architecture

Phase 16 adds a read-only institutional research interface over the existing UZQUANT production database. The analytical engine remains authoritative. `uzquant/research_api.py` assembles versioned records and lineage; `uzquant/web.py` exposes JSON and static assets through the Python standard-library WSGI server; the browser client only filters, formats, and displays API values.

No valuation, factor, confidence, liquidity, capacity, risk, backtest, validation, or portfolio calculation exists in JavaScript. Missing values remain JSON `null` and display as `Unavailable`.

Run locally with:

```text
python3 -m uzquant serve-research --host 127.0.0.1 --port 8765
```

## API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/health` | service health |
| `GET /api/v1/universe` | security universe/ranking records; supports sector, signal, and liquidity query filters |
| `GET /api/v1/securities/{ticker}` | complete security research record |
| `GET /api/v1/securities/{ticker}/market` | raw observed market history |
| `GET /api/v1/securities/{ticker}/financials` | matched financial-document evidence |
| `GET /api/v1/securities/{ticker}/valuation` | method-specific valuation records |
| `GET /api/v1/securities/{ticker}/liquidity` | liquidity/capacity state |
| `GET /api/v1/securities/{ticker}/corporate` | corporate actions |
| `GET /api/v1/securities/{ticker}/signals` | immutable signal history |
| `GET /api/v1/securities/{ticker}/report` | deterministic grounded institutional report |
| `GET /api/v1/issuers/{issuer_id}` | issuer identity/name/security detail |
| `GET /api/v1/macro` | macro observations and regime records |
| `GET /api/v1/portfolios` | versioned portfolio runs and positions |
| `GET /api/v1/backtests` | Phase 13 runs, orders, fills, and insufficiency state |
| `GET /api/v1/validation` | Phase 14 run, experiments, and model-risk findings |
| `GET /api/v1/pipelines` | nine pipeline stages with health, freshness, source, and failure information |

The complete security response includes identity, issuer, share class, market observations/quality/flags, matched documents, normalized observations, fundamentals, valuation methods/assumptions/rejections, liquidity, capacity, ownership/free-float metrics, rights, governance, actions, dividends, events, factors, Data Quality, signal history, risk gates, warnings, models/snapshots, raw source identifiers, hashes, URLs, publication dates, and retrieval dates.

## Interface views

- **Universe:** comparable columns for price/freshness, share class, valuation status, factors, liquidity, Data Quality, confidence, signal, and gates. Missing securities are not ranked as validated opportunities.
- **Security research:** prominent critical warnings; identity, current price, freshness, evidence coverage, fundamentals, method-level valuation reasons, liquidity/capacity, ownership/rights, governance/events, factor lineage, signal state, and raw provenance.
- **Institutional report:** a deterministic narrative built only from the same backend response. It covers all required report sections and lists source record IDs. It does not independently calculate numbers.
- **Portfolios:** latest style/AUM runs, positions, cash, validation state, and exact rejection reasons. The 100%-cash result is explained rather than hidden.
- **Backtest & Validation:** prominently displays `BACKTEST_INSUFFICIENT` and `UNRELIABLE`; unavailable evidence is not graphed as zero.
- **Pipelines:** security master, market data, financials, corporate intelligence, valuation, liquidity, events, macro, and signals with explicit operational status.

## Lineage and freshness

API objects retain backend primary IDs and the applicable dates/versions: trade date and first/last seen timestamps, publication/report periods, effective/disclosure dates, valuation cutoff/model, liquidity model, scoring/model/snapshot versions, signal generation time, validation version, portfolio model, source document ID, source URL, retrieval time, and SHA-256 where stored.

Financial data is fail-closed to documents with an explicit `MATCHED` entity check. Raw market observations remain separate from adjusted/total-return series. Historical signal versions are returned append-only.

## Real acceptance result

| Ticker | Signal | Valuation | Other prominent warnings |
|---|---|---|---|
| AGMKP | DATA_INSUFFICIENT | VALUATION_INSUFFICIENT | LIQUIDITY_TRAP, LOW_CONFIDENCE, RIGHTS_UNVERIFIED |
| KASUP | DATA_INSUFFICIENT | VALUATION_INSUFFICIENT | LOW_CONFIDENCE, RIGHTS_UNVERIFIED |
| IPKY | DATA_INSUFFICIENT | VALUATION_INSUFFICIENT | LOW_CONFIDENCE |
| UZTL | HOLD | VALUATION_INSUFFICIENT | LOW_CONFIDENCE |
| QZSM | DATA_INSUFFICIENT | VALUATION_INSUFFICIENT | LOW_CONFIDENCE |

All method rejection reasons come from `valuation_records`/`valuation_model_attempts`; no sample fair values are shown.

## Known limitations

- This is a local, read-only research interface; authentication, multi-user authorization, deployment hardening, and caching are not yet implemented.
- The universe contains 76 mastered securities, but only seven currently have market/research coverage.
- No validated valuation exists; the interface therefore cannot display legitimate Bear/Base/Bull values for the acceptance targets.
- Free float, ownership, rights, reporting perimeter, long market history, benchmark, and execution evidence remain incomplete as documented by prior phases.
- Pipeline freshness is exposed from stored run/record timestamps; no background scheduler is added in this phase.
- Charts are deliberately omitted where an unavailable or short series would imply false analytical completeness.
