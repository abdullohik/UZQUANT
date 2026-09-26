# UZQUANT Launch Data Recovery & Public Backfill Sprint

Audit date: 2026-09-27  
Scope: public, authorized sources only. This is not Phase 20.

## Outcome

The current RSE connector recovered without weakening any control. The production `asking_prices` request succeeded with 70 records and all five required securities. A normal scheduler cycle then completed all 17 pipelines as `HEALTHY`; the prior `FAILED`/`STALE` state cleared through normal dependency processing, not manual state editing.

The official RSE Excel export route remains broken (`HTTP 500`). The visible public trade-results HTML is available, contains exact trade rows and pagination, and was therefore implemented as a bounded fallback. Every retrieved page is archived, every row is checked for ISIN, market, date, positive price/quantity and price×quantity turnover, and daily OHLC/volume/turnover/count is derived only from actual trades. Empty result windows remain `EMPTY`; no zero-return or synthetic trade is created.

## Before and after

| Measure | Before | After |
|---|---:|---:|
| Pipeline health | 1 FAILED, 1 DEGRADED, 15 STALE | 17 HEALTHY |
| Issuers | 55 | 55 |
| Securities | 76 | 76 |
| Security-class codes | 4 | 4 |
| Market observations | 140 | 355 |
| Unique market dates | 20 | 73 |
| Reliable market span | 2026-08-17–2026-09-15 | 2024-09-27–2026-09-25 |
| Financial-document records | 17 | 29 |
| Current normalized observations | 342 | 603 |
| Available fundamental metrics | 30 | 60 |
| Verified share-count observations | 9 | 9 |
| Verified security rights | 0 | 0 |
| Ownership positions | 4 | 4 |
| Available valuations | 0 | 0 |
| Research signals | 105 | 112 |
| Prospective snapshots | 1 | 1 |

The financial-document increase represents newly retrieved official content revisions/pages under immutable content hashes. It does not imply twelve new reporting periods.

## RSE failure reproduction and root cause

- Production function: `uzquant.security_master.ingest_security_master` via `uzquant.rse.fetch`.
- Route: `https://uzse.uz/asking_prices`.
- Historical recorded failure: three exhausted attempts; administrative HTTP access rejection was previously observed and preserved.
- Current reproduction: HTTP 200 HTML; parser accepted 70 security anchors; required schema and required securities passed.
- Parser expectation: anchors containing `/isu_infos/STK?isu_cd=...`, ISIN, ticker and issuer name.
- Current actual structure: compatible HTML security anchors.
- Classification: `SOURCE_UNAVAILABLE` for the historical incident (temporary external/access condition), now recovered. It is not a current parser, pagination, identifier, or database defect.
- The official trade export route `/trade_results/export?...` currently returns HTTP 500 even for a verified date with visible trades. Classification: `SOURCE_UNAVAILABLE` for that route.
- The ordinary `/trade_results?...` HTML route returns HTTP 200 and exact paginated trade rows. The connector previously did not ingest it: `PUBLIC DATA EXISTED BUT WAS NEVER BACKFILLED`.

## Public RSE source inventory

| Source | Verified route/pattern | Data | Range observed | Pagination/download | Automation and limits | Ingestion state |
|---|---|---|---|---|---|---|
| Asking prices | `/asking_prices` | current ISIN, ticker, issuer anchor | current | HTML | compliant requests currently work | production ingested |
| Security detail | `/isu_infos/STK?isu_cd={ISIN}` and `/isu_infos/{ISIN}/detail?locale=en` | current class/security detail and rolling chart | current/rolling | HTML | works; schema guarded | production ingested |
| Trade results | `/trade_results?begin=DD.MM.YYYY&end=DD.MM.YYYY&mkt_id=STK&search_key={ISIN}&page=N` | timestamp, ISIN, ticker, issuer, class label, market, board, price, quantity, turnover | verified back to 2024-09-27 in this run; older range not yet exhausted | 50 visible rows/page | feasible but slow; rate-limited/resumable | fallback implemented; partial backfill |
| Trade Excel export | `/trade_results/export?...` | intended XLSX trade export | current request tested | XLSX intended | HTTP 500; not usable | parser retained for files legitimately obtained later |
| Boards/listing notices | `/boards?locale=en` | listing/delisting notices | current and dated notices | HTML/PDF links | discoverable; historical normalization incomplete | not comprehensively ingested |
| Exchange reviews | public Active Storage PDF links exposed by RSE review pages | listings, delistings, annual/quarterly exchange statistics | search verified at least 2023–2024 reports | PDF | public; deterministic extraction needs a separate bounded inventory | not backfilled in this sprint |

No hidden API was invented or used. No CAPTCHA, authentication, anti-bot rule or rate limit was bypassed.

## Historical RSE backfill result

The queue contains 1,900 monthly security windows for 76 active STK securities over 2024-09-27–2026-09-27. This sprint completed 11 imported windows and 3 verified-empty windows, archived 125 HTML pages, and stored 5,873 trade-level records with exact raw-page lineage. The active job was safely returned to `PENDING` when the bounded run stopped. Remaining queue: 1,885 `PENDING`, one historically `SOURCE_BLOCKED` job, no stranded `IN_PROGRESS` job.

Daily analytical observations now cover:

| Security | Dates | Earliest | Latest |
|---|---:|---|---|
| AGMKP | 73 | 2024-09-27 | 2026-09-25 |
| IPKY | 73 | 2024-09-27 | 2026-09-25 |
| UZTL | 52 | 2024-09-27 | 2026-09-25 |
| QZSM | 73 | 2024-09-27 | 2026-09-25 |
| KASUP | 28 | 2026-08-17 | 2026-09-25 |

Counts of securities with at least 30/60/120/250/500 dates are 4/3/0/0/0. Liquidity, ADV, trading-frequency and volatility evidence is improved for four targets, but the history remains inadequate for valid backtesting, long-window momentum, or model validation. Phase 13–19 were not rerun.

## Openinfo and CBU

The approved Openinfo connector successfully refreshed all 12 configured financial pages and five configured corporate pages. It added immutable content versions, bringing stored financial-document records to 29 and current normalized observations to 603. Public Openinfo clearly exposes broader annual, quarterly, IFRS, material-fact, charter and prospectus archives, but the existing connector is a curated list rather than a complete issuer archive crawler. Therefore broader history remains category `A/C`: public data is discoverable but not fully inventoried/backfilled.

CBU official policy-rate XLSX, money-supply JSON, reserves JSON and daily FX JSON all refreshed successfully. Four structured series are usable. The database now has 519 append-only observation vintages, including repeated retrieval vintages; genuine original-release/revision dates remain unavailable and are not inferred. The official CBU open-data portal lists additional structured datasets (including policy rate, FX, banking rates, monetary and external-sector data), but they were not silently added without parser contracts.

## Target valuation readiness

| Security | Financial periods | Unit/perimeter | Shares | Rights | Ownership | Valuation result | Exact remaining blocker |
|---|---|---|---|---|---|---|---|
| AGMKP | 2023 annual; 2026 Q1 | units usable in current version; perimeter unknown | verified class count present | LOW, not verified | none | `VALUATION_INSUFFICIENT` | preferred rights, perimeter, ownership and complete model assumptions |
| KASUP | 2017/2023 annual; 2025 H1 | 72 unspecified-unit observations; perimeter unknown | verified class count present | unavailable | none | `VALUATION_INSUFFICIENT` | units, perimeter, preferred rights, ownership and insurer inputs |
| IPKY | 2022–2024 annual | 9 unspecified-unit observations; perimeter unknown | verified class count present | not material as common, but no structured record | none | `VALUATION_INSUFFICIENT` | units/perimeter, bank valuation inputs/assumptions and ownership |
| UZTL | 2024–2025 annual | units usable in current version; perimeter unknown | verified class count present | LOW | 4 positions | `VALUATION_INSUFFICIENT` | perimeter, complete assumptions and broader ownership/free-float evidence |
| QZSM | 2023 annual; 2026 Q1 | units usable in current version; perimeter unknown | verified class count present | no structured record | none | `VALUATION_INSUFFICIENT` | perimeter, ownership, cash-flow/assumption completeness |

No target became valuation-ready. No Bear/Base/Bull value was forced.

## Mandatory answers

1. RSE ingestion failed because the public source was temporarily unavailable/rejected after all retries; the same production route now succeeds.
2. The recorded outage was external. The lack of historical ingestion was a connector/backfill capability gap. The Excel export HTTP 500 is currently an RSE route failure.
3. Public paginated RSE history exists at least from 2024-09-27 through 2026-09-25 for the tested targets. The absolute earliest public date has not yet been exhaustively proven.
4. UZQUANT now contains 5,873 HTML trade rows from 125 archived pages and 355 daily observations across 73 dates; only 14 of 1,900 planned windows are completed.
5. It previously had ~20 dates because it consumed only rolling security-detail charts and had no working historical HTML backfill.
6. Yes. 1,885 queued windows remain, plus listing/review history not normalized.
7. Openinfo exposes substantially more public archive categories than the 12 curated financial routes, but a defensible complete count was not established; no count is fabricated.
8. Four CBU structured series are currently parsed and usable: policy rate, USD/UZS, M2 and reserves. Other official datasets require explicit contracts and release-date treatment.
9. No target became valuation-ready.
10. Verified full preferred-share rights, reliable free float/ownership breadth, historical order-book/depth, some valuation assumptions and genuine macro release vintages may require new authoritative/authorized sources or issuer documents.
11. Prospective validation, paper outcomes and model evidence require time after stable fresh cycles.
12. Yes. The real scheduler completed 17/17 pipelines as `HEALTHY`, while analytical outputs still fail closed where evidence is insufficient.
13. Smallest path: finish the priority-security public backfill, obtain authoritative perimeter/unit/rights/ownership evidence and explicit valuation assumptions for a minimum cohort, then accumulate full-freeze prospective observations. Do not weaken gates.

## Tests

Full suite: **194 passed**. New coverage includes RSE HTML row parsing, pagination detection and turnover rejection. Existing tests continue to cover idempotency, duplicate handling, no-trade behavior, schema changes, point-in-time logic and identifier integrity.

