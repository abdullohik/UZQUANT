# UZQUANT Phase 0 — Findings and Reality Check

Research date: 2026-09-14

## Executive conclusion

`VERIFIED FACT`: An accurate Uzbekistan-focused research system is technically feasible for current and recent-period issuer research using official RSE market pages, Openinfo disclosures, CBU/Statistics Committee macro data, CSD identifier tools, issuer documents and state-asset publications.

`VERIFIED FACT`: The five required securities—AGMKP, KASUP, IPKY, UZTL and QZSM—were found on official RSE and/or Openinfo pages. Current identifiers/classes and recent corporate reports were retrievable for all five; dated 2018 trade evidence was directly observed for four of five.

`VERIFIED FACT`: An institutional-quality *point-in-time backtest* is not currently proven feasible. Historical order books/spreads, complete delisting/universe history, historical ownership/free float, full corporate-action histories, immutable filing vintages and systematic historical execution data were not verified.

`RECOMMENDATION`: Phase 1 should build a provenance-first source archive and validation pipeline, not valuation models or signals.

## 1. What is definitely available?

- RSE public HTML exposes current/last price, last-trade date, ISIN, ticker, issuer, class, best bid/ask and displayed quantities.
- RSE dated trade-results pages can expose individual transaction rows. A 2018-02-02 URL returned data successfully.
- Openinfo exposes issuer identity, tickers, disclosure dates, structured financial tables, material facts and downloadable filings without authentication on tested pages.
- Recent financial reports were verified for each test issuer; material facts were found as far back as 2017.
- CBU provides official policy-rate, FX and banking/money statistics through pages and downloadable/machine-readable formats.
- Statistics Committee pages advertise XLSX, CSV, JSON/XML API and SDMX for GDP, CPI, production and trade data.
- CSD publicly advertises ISIN/FISN/CFI and issuer/security lookup functions.
- NAPP publishes a registered-securities-issue registry and capital-market participant registers.
- UzSAMA publishes state-asset and privatization material, with attribution required for reuse.

## 2. What is partially available?

- Historical trades and derived daily prices/volume/turnover: accessible for tested dates, but completeness across all dates, pages, boards and securities is unaudited.
- Financial statements: broad disclosure exists, but IFRS/local, audited/unaudited and consolidated/standalone boundaries are inconsistent and require document-level validation.
- Dividends and corporate actions: present in reports, facts and resolutions, but no verified complete normalized history.
- Shares outstanding: issue and annual reports provide snapshots; a complete effective-dated series was not verified.
- Ownership/state participation: disclosed in some reports and government announcements, but not as a complete historical cap table.
- Publication dates: commonly available; exact timestamps and preserved original/restated vintages are inconsistent or unverified.
- Macro series: machine-readable current histories exist, while real-time historical vintages/revisions need testing.

## 3. What is unavailable or unverified?

- Historical order-book depth and displayed sizes.
- Historical bid/ask spreads as a supported archive.
- A complete historical listing universe, including delisted/failed securities.
- Complete historical free float and ownership.
- Complete historical ticker/ISIN effective-date mappings.
- A complete, immutable corporate-action master.
- Reliable publication timestamps for every historical filing.
- A verified official bulk market-data API.
- A continuous official government-yield curve source tested in this phase.

These are classified `UNKNOWN` unless absence was directly established; “not found” is not the same as “does not exist.”

## 4. What requires document parsing?

- IFRS and audited reports, notes, auditor opinions and consolidation detail.
- Charters, prospectuses and issue documents for security rights.
- Shareholder resolutions for dividends, reorganizations and capital changes.
- Ownership tables and state-asset documents.
- Legacy corporate actions and restatements.

Deterministic Excel/HTML extraction should be preferred. PDF text extraction should precede OCR; OCR output must carry confidence and cannot become numerical truth without validation.

## 5. What requires scraping?

- RSE current quote/order snapshots and dated transaction HTML unless an official supported download/API is later verified.
- Openinfo report/fact indexes and structured HTML where downloads are absent.
- Some issuer/government pages lacking feeds or bulk downloads.

Scraping should mean conservative retrieval of public pages, not bypassing controls. Raw responses, retrieval timestamps and hashes should be retained.

## 6. What should not be scraped?

- RSE paths disallowed by `robots.txt`, including the explicitly disallowed execution-ranking paths and parameter patterns.
- Authenticated portals, personal cabinets, CAPTCHA-protected pages or anti-bot barriers.
- Any endpoint whose terms prohibit automated collection, storage or redistribution.
- Order-entry/trading interfaces or non-public depth feeds.
- CSD backing services until their public status, access expectations and terms are verified.

## 7. What can safely be automated now?

`RECOMMENDATION`, subject to legal/terms confirmation:

- Low-frequency retrieval of tested public RSE and Openinfo pages.
- Downloads explicitly offered by CBU and Statistics Committee.
- Archiving public disclosure documents with URL, retrieval time, publication date and cryptographic hash.
- Deterministic parsing into a staging layer that preserves original units/currencies and distinguishes reported, derived and estimated values.
- Validation checks for duplicate IDs, statement identities, units, reporting periods and conflicting sources.

No source should be polled aggressively. Technical access does not itself grant redistribution rights.

## 8. What cannot currently be backtested honestly?

- Strategies requiring historical spreads, depth, queue position or reliable intraday execution.
- Free-float- or ownership-history factors.
- A survivorship-bias-free full-market strategy until delisted securities and historical membership are reconstructed.
- Corporate-action-adjusted or total-return histories until actions/dividends are reconciled.
- Point-in-time fundamental strategies until original filing versions, disclosure times and restatements are archived.
- Capacity claims requiring more than transaction prints and conservative participation assumptions.

Any preliminary backtest must be labeled experimental and must return `DATA INSUFFICIENT` where these gaps affect validity.

## 9. What historical period is realistically usable?

`VERIFIED FACT`: at least one RSE dated trade-results page from 2018 and Openinfo material facts from 2017 are publicly retrievable. This establishes a *candidate* recent-history window, not a validated complete dataset.

`RECOMMENDATION`: treat 2018–present as the earliest candidate window for a coverage audit. Do not promise or publish a backtest over that period until daily completeness, corporate actions, universe membership, filing vintages and execution assumptions pass acceptance tests. A defensible window may ultimately be shorter.

Macro series can extend further (CBU FX archive UI exposes 1994 onward), but longer macro history does not extend security-level backtest feasibility.

## 10. Largest data risks

1. Stale prices being mistaken for executable values.
2. Survivorship bias from missing delistings and historical universe membership.
3. Incorrect share-class rights, especially AGMKP and KASUP preferred shares.
4. Incomplete corporate-action/dividend adjustment.
5. Mixing IFRS/local, consolidated/standalone or audited/unaudited financials.
6. Look-ahead bias from restatements and missing original publication timestamps.
7. Missing historical ownership/free float.
8. Silent gaps or pagination failures in scraped trade history.
9. Legal/licensing uncertainty around bulk storage and redistribution.
10. Issuer-submitted disclosure errors and inconsistent units/templates.

## 11. Capabilities that must be weakened

- Replace precise historical slippage/depth models with conservative scenario ranges.
- Suppress high-confidence liquidity and capacity claims without depth/free-float evidence.
- Avoid preferred-share valuation until charter/issue rights are verified.
- Limit backtests to audited coverage windows and exclude claims of complete-market performance until delistings are recovered.
- Represent fair value and liquidity as ranges with explicit confidence.
- Use `DATA INSUFFICIENT` or `VALUATION INSUFFICIENT` where missing rights, ownership, statements or corporate actions are material.
- Do not produce intraday timing conclusions: `INTRADAY TIMING NOT RELIABLE`.

## 12. Is an institutional-quality research system feasible?

`ASSESSMENT`: Yes for a provenance-rich, explainable research and monitoring system, if it accepts manual verification for difficult documents and exposes uncertainty.

`ASSESSMENT`: Not yet proven for fully automated institutional-grade historical simulation, execution analytics or portfolio-capacity estimation. Those require additional evidence, licensed data or deliberately conservative limitations.

## 13. What should Phase 1 actually build?

`RECOMMENDATION`: after explicit approval, Phase 1 should build only the data foundation:

1. Versioned issuer/security master separating issuer and security.
2. Raw-source archive with URL/document ID, publication date, retrieval timestamp, checksum, language and format.
3. Source registry and access-policy metadata.
4. Staging parsers for one verified RSE page type and one Openinfo report/fact type.
5. Point-in-time filing/version model preserving originals and restatements.
6. Data-quality rules for units, currency, periods, perimeter and statement reconciliation.
7. Coverage-audit tooling for dates, securities, pagination and missing sessions.
8. Manual-review queue for entity ambiguity, OCR, share rights, corporate actions and conflicts.

Phase 1 should not yet build valuation, recommendations, backtests, execution, portfolio construction or UI.

## Acceptance-gate assessment

| Gate | Result |
|---|---|
| Major data domains investigated | PASS, with documented unknowns |
| Five test securities checked | PASS |
| Accessibility tested rather than guessed | PASS for core RSE/Openinfo/CBU pages; PARTIAL for CSD/API breadth |
| Material limitations documented | PASS |
| Point-in-time feasibility assessed | PASS — partial, not production-ready |
| Realistic historical window identified | PASS — 2018–present candidate audit window, not a promised backtest window |

## Phase status

Phase 0 research deliverables are complete at discovery-pass level. Phase 1 is not started and requires explicit approval.
