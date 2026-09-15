# Macro Engine

## Purpose and boundary

The Phase 10 engine stores macro observations as append-only vintages, supports historical as-of queries, produces transparent regime context, and records sector transmission assumptions. Macro output is context for risk and scenarios only. It cannot independently emit or modify BUY/SELL classifications.

## Official production sources

The production importer currently uses only verified Central Bank of Uzbekistan (CBU) endpoints:

- policy/refinancing-rate history: `https://cbu.uz/upload/medialibrary/479/szj8z2sr5oanndna0npgsw6r0xcyi67u/asosiy_stavka.xlsx`;
- official USD/UZS archive API documented by CBU: `https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/{date}/`;
- broad-money open data: `https://cbu.uz/upload/open_data/0021/4-009-0021_eng.json`;
- official-reserve-assets open data: `https://cbu.uz/upload/open_data/0017/4-009-0017_eng.json`.

Raw responses are content-addressed under `data/raw/cbu/macro`. Parsed observations retain their raw-document link, URL, retrieval timestamp, parser version, unit, currency, and observation period.

## Vintage and release policy

CBU snapshot files provide historical observation/effective dates, but the tested feeds do not provide a dependable original release date and full revision ledger for every value. UZQUANT therefore does **not** equate observation date with release date. `initial_release_date` and `revision_date` remain NULL when unverified, while `vintage_known_at` is the first successful UZQUANT retrieval timestamp. An as-of query filters on both `period_end <= as_of` and `vintage_known_at <= as_of`, then selects the latest eligible vintage. Consequently, a current snapshot is unavailable at earlier decision dates. This is conservative and prevents future leakage; it is not a reconstructed historical vintage archive.

Reruns append a new vintage and never overwrite raw observations. If a source later publishes explicit release/revision metadata, it may populate those fields without changing this selection rule.

## Series and units

`CBU_POLICY_RATE` is percent and event-frequency. Historical rows before the modern policy-rate framework are described as policy/refinancing history, matching the source workbook. `USD_UZS` is UZS per USD after dividing the published rate by its nominal. `MONEY_SUPPLY_M2` retains the source-reported scale label pending independent unit confirmation. `FX_RESERVES` is USD millions as described by the official reserve template.

The Phase 0 audit did not establish production-ready structured sources and vintage semantics for CPI/core CPI, GDP, industrial output, credit/deposit growth, government yields, fiscal/trade data, or global commodity prices. Those series are not fabricated or silently imported from secondary aggregators.

## Regime rules

Rules are deterministic and versioned as `macro-regime-1.0.0`. Thresholds are provisional research assumptions:

- policy rate rises/falls activate tightening/easing;
- CPI YoY at or above 10% activates high inflation; a decline activates disinflation;
- USD/UZS change above 5% activates UZS depreciation; an absolute move within 3% activates stability;
- credit growth at or above 20% is high and below 10% is low;
- a verified commodity composite move above +10% or below -10% denotes strong or weak conditions.

Missing inputs produce `UNAVAILABLE`, not an inferred state. Each classification stores its inputs and threshold as evidence. The current sparse annual FX sampling makes FX regimes illustrative and low-frequency; it must not be interpreted as a monthly regime.

## Sector context

Sector mappings are versioned, explicitly labelled `ECONOMIC_ASSUMPTION`, and store their transmission channel and directional interpretation. Effects are conditional, not forecasts: rates may have mixed bank effects, depreciation can support exporters but hurt importers, commodity prices affect miners, rates affect leveraged issuers, and inflation affects consumer demand and pricing power.

## Operator commands

Run `python3 -m uzquant init-db`, then `python3 -m uzquant update-macro`. Run `python3 -m uzquant export-macro` to reproduce the two Phase 10 CSV outputs. Environment variables documented for the existing project control database path, raw-data path, timeout, and retries.
