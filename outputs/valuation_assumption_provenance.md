# Valuation Assumption Provenance

Assessment date: 2026-09-27

## Official CBU curve

| Field | Stored value |
|---|---|
| Economic definition | Theoretical average and smoothed government-securities yield curve in national currency, estimated from Ministry of Economy and Finance and CBU securities in primary/secondary markets, overnight money-market rate, and CBU deposit/REPO auctions |
| Model | Nelson-Siegel with interpolation, extrapolation and weighting |
| Publication | Weekly; operations through Tuesday 18:00, published Wednesday by 10:00 |
| Rate convention | Continuously compounded zero rates |
| Currency | UZS |
| Nominal/real | NOMINAL. The instruments are nominal national-currency market instruments; the curve is not an inflation-indexed real curve. |
| Provenance | `AUTHORITATIVE_SOURCE`; each point is an `OBSERVED` published curve value |
| Source | https://uz-yield-curve.cbu.uz/api/open/yield-curve-results/ and `/yield-curve-points/` |
| Methodology | https://cbu.uz/en/monetary-policy/local-currency-yield-curve/ |
| Stored | 111 curve dates; 2,544 points; 2024-08-21 through 2026-09-23 |
| Latest 10-year point | 16.96054015902% on 2026-09-23 (API value; displayed rounded value 16.96054%) |
| API/source version | The API's `codeRevisionNumber`/`codeRevisionDate` string is retained per vintage; no semantic API version is published |

Every retrieval creates a new append-only curve vintage linked to immutable raw results and points documents. Historical queries select only a vintage whose `retrieved_at` was known at the requested timestamp.

## Permitted valuation use

The curve is a reference/risk-free-rate input only when the valuation cash flows are nominal UZS and the selected tenor matches the economic duration. Continuous rates must be converted consistently before combining them with differently compounded inputs. It is not WACC, cost of equity, cost of debt, an equity-risk premium, or a forecast.

## Remaining assumption chain

| Component | Status | Provenance class | Why |
|---|---|---|---|
| Nominal UZS reference/risk-free curve | AVAILABLE | AUTHORITATIVE_SOURCE / OBSERVED | Official CBU full curve now stored |
| Equity-risk premium | MISSING | CONFIGURABLE_RESEARCH_ASSUMPTION or SOURCE_DERIVED | No approved Uzbekistan-specific series has been adopted in production |
| Security/sector beta | MISSING | MODEL_ESTIMATED | No defensible local estimation sample or approved comparable set |
| Cost of equity | MISSING | DERIVED | Cannot be derived until risk premium and beta/method choice exist |
| Cost of debt | MISSING | OBSERVED or SOURCE_DERIVED | Issuer borrowing terms and compatible marginal spread are not normalized |
| Target capital structure | MISSING | CONFIGURABLE_RESEARCH_ASSUMPTION | No approved target weights |
| WACC | MISSING | DERIVED | The CBU point alone is never WACC |
| Long-term growth | MISSING | CONFIGURABLE_RESEARCH_ASSUMPTION | No approved nominal UZS terminal-growth basis |
| Forecast scenarios | MISSING | CONFIGURABLE_RESEARCH_ASSUMPTION | No approved issuer forecast set |
