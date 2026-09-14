# UZQUANT Phase 0 — Verified Data Sources

Research date: 2026-09-14 (Asia/Tashkent)

Status vocabulary: `VERIFIED_AUTOMATED`, `VERIFIED_MANUAL`, `PARTIAL`, `RESTRICTED`, `UNKNOWN`, `UNAVAILABLE`.

This inventory records observed access, not assumed capability. Search-result snippets were used only to discover pages; material conclusions below are based on pages or endpoints that were opened or requested directly.

## 1. Republican Stock Exchange “Toshkent” (RSE)

- Source: Republican Stock Exchange “Toshkent”
- Domain: `uzse.uz`
- Authority: primary market operator
- Tested URLs:
  - <https://uzse.uz/asking_prices?page=5>
  - <https://uzse.uz/trade_results?date=02.02.2018>
  - <https://uzse.uz/exchange/structure?locale=en>
  - <https://uzse.uz/robots.txt>
- Observed access: anonymous HTTPS; all tested URLs returned HTTP 200. The dated trade-results page returned a large HTML response and exposed transaction rows. No authentication was requested.
- Formats: server-rendered HTML tables; PDF exchange reviews; no public JSON/CSV market-data endpoint was verified.
- Identifiers observed: ticker, ISIN-like security code, issuer name, market/board, security class.
- Market fields observed: last/close price, last-trade date, best bid/ask, displayed bid/ask quantity, transaction price, quantity, value and timestamp on trade-results pages.
- History: a dated trade-results page for 2018-02-02 was successfully retrieved. This proves that at least some 2018 pages remain accessible, not that every session/security is complete from 2018 onward.
- Publication date: transaction date/time appears in rows. Page revision history and ingestion timestamp were not found.
- Automation: `PARTIAL`. Low-volume HTML retrieval works, but parsing is required and no supported public market-data API was verified.
- Terms/access: `robots.txt` permits general indexing but disallows administrative paths, two execution-ranking paths, and several parameter patterns (including pagination/search patterns). Robots rules are not a license. No explicit bulk-reuse or redistribution permission was verified. Automated collection should therefore be conservative, cached, rate-limited, and reviewed before production.
- Reliability: high authority for exchange trades and displayed market state; completeness and correction history remain unverified.
- Important limitations: no verified historical order book/depth, supported bulk download, delisting history, historical quotation-list membership, or corporate-action adjustment file.

## 2. Openinfo corporate disclosure portal

- Source: Unified Corporate Information Portal (Openinfo)
- Domain: `openinfo.uz` (some search results also resolve on `new.openinfo.uz`)
- Authority: official disclosure portal; individual issuers remain responsible for accuracy and completeness, as stated on disclosure pages.
- Tested URLs:
  - <https://openinfo.uz/en/reports/jsc/quarter/18364> (AGMK/AGMKP, Q1 2026)
  - <https://openinfo.uz/en/reports/insurance/quarter/361> (KASU/KASUP, Q2 2023)
  - <https://openinfo.uz/en/reports/bank/quarter/1257> (IPKY/IPKYP, Q1 2026)
  - <https://openinfo.uz/en/reports/jsc/annual/6116> (UZTL/UZTLP, FY2025)
  - <https://openinfo.uz/en/reports/jsc/quarter/18437> (QZSM, Q1 2026)
  - <https://openinfo.uz/en/facts/25/1706> (UZTL issue disclosure)
  - <https://openinfo.uz/en/facts/11/30> (QZSM material fact disclosed 2017-02-10)
  - <https://openinfo.uz/robots.txt>
- Observed access: anonymous HTML requests returned HTTP 200 for tested reports. `robots.txt` returned HTTP 404, so no robots policy was located at the conventional path.
- Formats: structured HTML tables plus download links for PDF and, on many reports, Excel; material facts in HTML/download form.
- Fields observed: issuer legal name, ticker(s), TIN and other registration/statistical identifiers, disclosure date, reporting/approval period, balance-sheet and income-statement fields, dividends in annual reports, material facts, decision dates, issue terms, and named responsible officers.
- History: a 2017 material fact was directly accessible; 2023 and 2026 reports were directly accessible. “History” links are visible on report/fact pages, but a complete bulk historical index and revision semantics were not verified.
- Publication date: explicit disclosure date is present. Exact timestamps are not consistently visible in the tested English pages.
- Restatements: history controls exist, but preservation of every original/restated version was not proven.
- Automation: `PARTIAL`. HTML is mechanically retrievable and partially structured. Excel may support deterministic extraction. PDFs require document parsing; scanned documents may require OCR. No official API was verified.
- Terms/access: no authentication on tested public pages; no conventional robots file; no bulk collection, storage, redistribution, attribution, or rate-limit terms were located during this pass. Absence of a discovered restriction is not permission.
- Reliability: primary disclosure channel, but issuer-submitted content requires validation and reconciliation.
- Important limitations: inconsistent templates/languages, possible malformed values, uncertain consolidated/standalone labeling, incomplete timestamps, and no verified bulk change feed.

## 3. Central Securities Depository of Uzbekistan (CSD)

- Source: Central Securities Depository
- Domain: `uzcsd.uz`
- Authority: primary securities-infrastructure source
- Tested URLs:
  - <https://www.uzcsd.uz/>
  - <https://www.uzcsd.uz/robots.txt>
- Observed access: public single-page application. The conventional robots URL returned the application shell (HTML), not a robots policy.
- Public functions advertised: assigned ISIN/FISN/CFI list, joint-stock-company list, security-code search, issuer search and open data.
- Format/access: JavaScript application; exact backing endpoints and downloadable schemas were not verified in this phase.
- Automation: `UNKNOWN` pending endpoint and terms verification. The UI is suitable for manual identifier checks; it must not be described as a verified API.
- History: `UNKNOWN`; current lookup capability does not prove historical ISIN/issuer mappings.
- Important limitations: historical identifiers, effective dates, outstanding-share history, delistings and reuse/redistribution rights remain unverified.

## 4. Central Bank of the Republic of Uzbekistan (CBU)

- Source: Central Bank of Uzbekistan
- Domain: `cbu.uz`
- Authority: primary official monetary/banking source
- Tested URLs:
  - <https://cbu.uz/en/arkhiv-kursov-valyut/>
  - <https://cbu.uz/en/monetary-policy/refinancing-rate/>
  - <https://cbu.uz/ru/services/open_data/portal/>
  - <https://cbu.uz/en/statistics/e-gdds/data/111573/>
  - <https://cbu.uz/robots.txt>
- Observed access: anonymous HTML returned HTTP 200. Archive page offers XLS downloads; policy-rate page offers XLSX; the open-data catalogue links XML, CSV, JSON and XLSX resources for policy rate, exchange rate, monetary aggregates and bank statistics.
- History observed: FX archive UI exposes years back to 1994; a monthly e-GDDS exchange-rate series visibly covers 2013 onward. Policy rate is defined from 2020, with refinancing-rate history relevant before then.
- Publication dates: page update dates and dated releases are present. Vintage/revision history for every statistical series was not verified.
- Automation: `VERIFIED_AUTOMATED` for anonymous page/file retrieval; `PARTIAL` for point-in-time macro vintages because later revisions may overwrite earlier values.
- Robots/access: public content paths tested are not disallowed by the retrieved robots policy. No authentication was required. Dataset-specific license/redistribution and rate-limit terms still require legal review.
- Reliability: high for official rates and banking statistics.

## 5. National Statistics Committee

- Source: National Statistics Committee of the Republic of Uzbekistan
- Domain: `stat.uz`
- Authority: primary official statistics source
- Tested pages:
  - <https://stat.uz/en/official-statistics/national-accounts>
  - <https://stat.uz/en/official-statistics/e-gdds-imf>
- Formats advertised: XLSX, PDF, CSV, JSON API, XML API and SDMX for GDP, CPI, trade, production and related official series.
- Publication dates: dataset entries display update/publication dates; releases are dated.
- Automation: `PARTIAL`. Machine-readable formats are explicitly linked, but individual JSON/XML endpoint schemas, pagination, rate limits and vintage behavior were not exhaustively tested.
- Point-in-time: release dates are usable; unrevised historical vintages are `UNKNOWN` until archived releases are preserved and compared.
- Reliability: high authority; revision policy/vintage retention must be captured.

## 6. State Assets Management Agency

- Source: State Assets Management Agency (UzSAMA)
- Domains: `gov.uz/en/davaktiv`, legacy `olddata.gov.uz`
- Authority: primary government source for state assets and privatization
- Tested/discovered pages:
  - <https://gov.uz/en/davaktiv/pages/about>
  - <https://gov.uz/en/davaktiv/sections/view/43777/>
  - <https://olddata.gov.uz/en/sphere/authority/30?page=2&per-page=10>
- Formats: HTML/PDF on gov.uz; legacy datasets advertise CSV/JSON/XML.
- Fields: agency mandate, privatization announcements/results, lists of enterprises/state participation in dated datasets.
- Automation: `PARTIAL`; public pages/files are accessible, but current security-level ownership percentages and historical effective dates were not verified as a complete dataset.
- Attribution: the agency site states that a link is required when its materials are used.
- Important limitations: announcement-based data is not a complete point-in-time ownership register.

## 7. Issuer websites and filings

- Authority: primary issuer source, subject to issuer accuracy and document controls.
- Access: issuer URLs are supplied by Openinfo reports for all five test issuers.
- Expected documents: annual/IFRS reports, auditor opinions, charters, prospectuses, shareholder resolutions and investor disclosures.
- Status: `PARTIAL`. Openinfo proves issuer identity and provides document links, but this phase did not establish a uniform issuer-site archive or machine-readable access pattern.
- Parsing: mostly PDF/HTML; scanned charters or legacy reports may need OCR. Numeric truth must remain grounded in source documents and reconciled to structured filings.
- Limitations: link rot, inconsistent language/template, unknown revision history and no common publication timestamp standard.

## 8. National Agency of Perspective Projects (NAPP)

- Source: National Agency of Perspective Projects of the Republic of Uzbekistan
- Domain: `napp.uz`
- Authority: official regulator for capital-market licensing/registration functions presented on its site
- Verified/discovered pages:
  - <https://napp.uz/uz>
  - <https://napp.uz/uz/pages/davlat-ro-yxatidan-o-tkazilgan-qimmatli-qog-ozlar-chiqarilishlari-reyestri>
  - <https://napp.uz/ru/pages/qimmatli-qog-ozlar-bozori-professional-ishtirokchilarining-reestri>
- Public information observed: registered securities-issue registry download and professional-participant/special-regime registers with licence identifiers and dates.
- Format/access: public HTML and downloadable registry; exact downloadable schema and historical version retention were not tested exhaustively.
- Automation: `PARTIAL`; useful for issue/licence cross-checking, but not yet a verified point-in-time security master.
- Important limitations: historical registry snapshots, corrections, security-level effective dates, rate limits and redistribution terms remain unverified.

## Secondary sources

No secondary source is approved as a numerical source of truth in Phase 0. Secondary databases may later assist discovery or cross-checking, but they must be labeled secondary and may not silently override RSE, Openinfo, CSD, CBU, Statistics Committee, regulator or issuer evidence.

## Legal/access conclusion

`VERIFIED FACT`: low-volume anonymous retrieval works for tested RSE, Openinfo, CBU and government pages.

`VERIFIED FACT`: no authentication, CAPTCHA or anti-bot bypass was attempted.

`ASSUMPTION`: production-scale collection may be acceptable if conservative; this is not established by technical accessibility.

`RECOMMENDATION`: before production ingestion, obtain or document source-specific terms/licensing, attribution, storage, redistribution and rate-limit positions. Do not scrape paths disallowed by RSE robots rules; prefer official downloads; cache immutable documents; identify the collector; and stop on throttling or access-control signals.
