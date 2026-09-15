from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .repository import Repository, stable_id, utc_now

PARSER_VERSION = "macro-cbu-1.0.0"
RULES_VERSION = "macro-regime-1.0.0"
MAPPING_VERSION = "sector-macro-1.0.0"
SOURCE_ID = "cbu-macro-official"
POLICY_URL = "https://cbu.uz/upload/medialibrary/479/szj8z2sr5oanndna0npgsw6r0xcyi67u/asosiy_stavka.xlsx"
MONEY_URL = "https://cbu.uz/upload/open_data/0021/4-009-0021_eng.json"
RESERVES_URL = "https://cbu.uz/upload/open_data/0017/4-009-0017_eng.json"
FX_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/{date}/"


@dataclass(frozen=True)
class MacroValue:
    code: str
    name: str
    category: str
    frequency: str
    period_start: str
    period_end: str
    value: Decimal
    unit: str
    currency: str | None
    source_url: str


def _download(url: str, timeout: float, attempts: int, backoff: float) -> bytes:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "UZQUANT/0.1 macro-research"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - exercised by live network only
            last = exc
            if attempt + 1 < attempts:
                time.sleep(backoff * (2**attempt))
    raise RuntimeError(f"download failed for {url}: {last}")


def _xlsx_rows(payload: bytes) -> list[list[str]]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(io.BytesIO(payload)) as archive:
        strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(t.text or "" for t in item.findall(".//m:t", ns)) for item in root.findall("m:si", ns)]
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in root.findall(".//m:row", ns):
            values: list[str] = []
            for cell in row.findall("m:c", ns):
                node = cell.find("m:v", ns)
                value = "" if node is None else (node.text or "")
                if cell.attrib.get("t") == "s" and value:
                    value = strings[int(value)]
                values.append(value.strip())
            rows.append(values)
        return rows


def parse_policy_rates(payload: bytes) -> list[MacroValue]:
    values = []
    for row in _xlsx_rows(payload)[1:]:
        if len(row) < 2:
            continue
        match = re.match(r"(\d{2}\.\d{2}\.\d{4})\s*[—-]\s*(?:(\d{2}\.\d{2}\.\d{4})|\.\.\.)", row[0])
        if not match:
            continue
        start = datetime.strptime(match.group(1), "%d.%m.%Y").date()
        end = datetime.strptime(match.group(2), "%d.%m.%Y").date() if match.group(2) else date.today()
        values.append(MacroValue("CBU_POLICY_RATE", "Central Bank policy/refinancing rate", "MONETARY_POLICY", "EVENT", start.isoformat(), end.isoformat(), Decimal(row[1]), "PERCENT", None, POLICY_URL))
    return values


def parse_money_supply(payload: bytes) -> list[MacroValue]:
    rows = json.loads(payload)
    values = []
    for row in rows:
        try:
            period = date.fromisoformat(str(row["Sana"]))
            amount = Decimal(str(row["KengmanodagipulmassasiM2"]))
        except (KeyError, ValueError, InvalidOperation):
            continue
        values.append(MacroValue("MONEY_SUPPLY_M2", "Broad money M2", "MONEY_AND_CREDIT", "MONTHLY", period.isoformat(), period.isoformat(), amount, "UZS_BILLION_SOURCE_REPORTED", "UZS", MONEY_URL))
    return values


def parse_reserves(payload: bytes) -> list[MacroValue]:
    rows = json.loads(payload)
    if not rows:
        return []
    total = next((row for row in rows if str(row.get("Rasmiyzaxira", "")).strip().startswith("A.")), None)
    if total is None:
        return []
    values = []
    for key, raw in total.items():
        if not re.fullmatch(r"\d{8}", key):
            continue
        try:
            period = datetime.strptime(key, "%d%m%Y").date()
            amount = Decimal(str(raw))
        except (ValueError, InvalidOperation):
            continue
        values.append(MacroValue("FX_RESERVES", "Official reserve assets", "EXTERNAL", "MONTHLY", period.isoformat(), period.isoformat(), amount, "USD_MILLION", "USD", RESERVES_URL))
    return values


def parse_fx(payload: bytes, source_url: str) -> list[MacroValue]:
    rows = json.loads(payload)
    values = []
    for row in rows:
        if row.get("Ccy") != "USD":
            continue
        period = datetime.strptime(row["Date"], "%d.%m.%Y").date()
        rate = Decimal(row["Rate"]) / Decimal(row["Nominal"])
        values.append(MacroValue("USD_UZS", "Uzbek soum per US dollar official rate", "FX", "DAILY", period.isoformat(), period.isoformat(), rate, "UZS_PER_USD", "UZS", source_url))
    return values


def _archive(repo: Repository, raw_dir: Path, run_id: str, url: str, payload: bytes, retrieved_at: str, media_type: str) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    suffix = ".xlsx" if "sheet" in media_type else ".json"
    path = raw_dir / "cbu" / "macro" / f"{digest}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(payload)
    document_id = stable_id("raw-document", f"{url}:{retrieved_at}")
    repo.add_raw_document((document_id, SOURCE_ID, run_id, url, retrieved_at, None, media_type, digest, str(path)))
    return document_id


def _store_values(repo: Repository, document_id: str, retrieved_at: str, values: list[MacroValue]) -> int:
    for item in values:
        series_id = stable_id("macro-series", item.code)
        repo.connection.execute(
            "INSERT OR IGNORE INTO macro_series VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (series_id, item.code, item.name, item.category, item.frequency, item.unit, item.currency, SOURCE_ID, item.source_url, "FIRST_OBSERVED_BY_UZQUANT", "APPEND_ONLY_VINTAGES", retrieved_at),
        )
        vintage = retrieved_at
        observation_id = stable_id("macro-observation", f"{item.code}:{item.period_start}:{item.period_end}:{vintage}")
        repo.connection.execute(
            "INSERT OR IGNORE INTO macro_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (observation_id, series_id, item.period_start, item.period_end, None, None, vintage, str(item.value), item.unit, item.currency, item.source_url, document_id, retrieved_at, PARSER_VERSION, "REPORTED"),
        )
    return len(values)


SECTOR_MAPPINGS = (
    ("BANK", "CBU_POLICY_RATE", "Funding costs and net-interest margin", "MIXED", "Higher rates can support asset yields but raise funding and credit risk."),
    ("BANK", "MONEY_SUPPLY_M2", "System liquidity and balance-sheet growth", "POSITIVE_WHEN_ORDERLY", "Money and deposit growth can support banking activity; excessive growth can increase risk."),
    ("EXPORTER", "USD_UZS", "Foreign-currency revenue translation", "GENERALLY_POSITIVE", "UZS depreciation can increase translated export revenue, subject to FX-linked costs."),
    ("IMPORTER", "USD_UZS", "Imported input costs", "GENERALLY_NEGATIVE", "UZS depreciation raises local-currency import costs unless passed through."),
    ("MINING", "GOLD_USD", "Commodity revenue", "GENERALLY_POSITIVE", "Higher realized commodity prices normally support revenue, subject to volumes and costs."),
    ("MINING", "COPPER_USD", "Commodity revenue", "GENERALLY_POSITIVE", "Higher realized commodity prices normally support revenue, subject to volumes and costs."),
    ("LEVERAGED", "CBU_POLICY_RATE", "Refinancing and interest costs", "GENERALLY_NEGATIVE", "Higher rates tend to increase debt-service burden for floating-rate or refinancing needs."),
    ("CONSUMER", "CPI", "Purchasing power and pricing", "MIXED", "Inflation can erode real demand while firms differ in pricing power."),
)


def store_sector_mappings(repo: Repository) -> int:
    created = utc_now()
    for sector, code, channel, direction, basis in SECTOR_MAPPINGS:
        repo.connection.execute(
            "INSERT OR IGNORE INTO sector_macro_exposures VALUES(?,?,?,?,?,?,?,?,?)",
            (stable_id("sector-macro", f"{sector}:{code}:{channel}:{MAPPING_VERSION}"), sector, code, channel, direction, basis, "ECONOMIC_ASSUMPTION", MAPPING_VERSION, created),
        )
    return len(SECTOR_MAPPINGS)


def query_as_of(connection, series_code: str, as_of: str):
    return connection.execute(
        """WITH eligible AS (
          SELECT mo.*,ms.series_code,ROW_NUMBER() OVER(
            PARTITION BY mo.series_id,mo.period_start,mo.period_end
            ORDER BY mo.vintage_known_at DESC,mo.retrieved_at DESC) AS rn
          FROM macro_observations mo JOIN macro_series ms USING(series_id)
          WHERE ms.series_code=? AND mo.vintage_known_at<=? AND mo.period_end<=?
        ) SELECT * FROM eligible WHERE rn=1 ORDER BY period_end""",
        (series_code, as_of, as_of[:10]),
    ).fetchall()


def classify_regimes(series: dict[str, list[tuple[str, Decimal]]]) -> dict[str, dict]:
    results: dict[str, dict] = {}
    def add(label: str, state: str, evidence: dict):
        results[label] = {"state": state, "evidence": evidence}
    policy = series.get("CBU_POLICY_RATE", [])
    if len(policy) >= 2:
        previous, current = policy[-2][1], policy[-1][1]
        add("MONETARY_TIGHTENING", "ACTIVE" if current > previous else "INACTIVE", {"previous": str(previous), "current": str(current)})
        add("MONETARY_EASING", "ACTIVE" if current < previous else "INACTIVE", {"previous": str(previous), "current": str(current)})
    else:
        add("MONETARY_TIGHTENING", "UNAVAILABLE", {"reason": "fewer than two observations"})
        add("MONETARY_EASING", "UNAVAILABLE", {"reason": "fewer than two observations"})
    cpi = series.get("CPI_YOY", [])
    if cpi:
        add("HIGH_INFLATION", "ACTIVE" if cpi[-1][1] >= Decimal("10") else "INACTIVE", {"latest": str(cpi[-1][1]), "provisional_threshold": "10 percent"})
        add("DISINFLATION", "ACTIVE" if len(cpi) >= 2 and cpi[-1][1] < cpi[-2][1] else "INACTIVE", {"latest": str(cpi[-1][1]), "previous": str(cpi[-2][1]) if len(cpi) >= 2 else None})
    else:
        add("HIGH_INFLATION", "UNAVAILABLE", {"reason": "CPI unavailable"}); add("DISINFLATION", "UNAVAILABLE", {"reason": "CPI unavailable"})
    fx = series.get("USD_UZS", [])
    if len(fx) >= 2 and fx[-2][1] != 0:
        change = (fx[-1][1] / fx[-2][1] - 1) * 100
        add("UZS_DEPRECIATION", "ACTIVE" if change > Decimal("5") else "INACTIVE", {"change_percent": str(change), "provisional_threshold": "5 percent"})
        add("UZS_STABILITY", "ACTIVE" if abs(change) <= Decimal("3") else "INACTIVE", {"change_percent": str(change), "provisional_band": "+/-3 percent"})
    else:
        add("UZS_DEPRECIATION", "UNAVAILABLE", {"reason": "fewer than two FX observations"}); add("UZS_STABILITY", "UNAVAILABLE", {"reason": "fewer than two FX observations"})
    credit = series.get("CREDIT_GROWTH_YOY", [])
    if credit:
        add("HIGH_CREDIT_GROWTH", "ACTIVE" if credit[-1][1] >= Decimal("20") else "INACTIVE", {"latest": str(credit[-1][1]), "provisional_threshold": "20 percent"})
        add("LOW_CREDIT_GROWTH", "ACTIVE" if credit[-1][1] < Decimal("10") else "INACTIVE", {"latest": str(credit[-1][1]), "provisional_threshold": "10 percent"})
    else:
        add("HIGH_CREDIT_GROWTH", "UNAVAILABLE", {"reason": "credit growth unavailable"}); add("LOW_CREDIT_GROWTH", "UNAVAILABLE", {"reason": "credit growth unavailable"})
    commodity = series.get("COMMODITY_INDEX", [])
    if len(commodity) >= 2 and commodity[-2][1] != 0:
        change = (commodity[-1][1] / commodity[-2][1] - 1) * 100
        add("STRONG_COMMODITY_ENVIRONMENT", "ACTIVE" if change > Decimal("10") else "INACTIVE", {"change_percent": str(change)})
        add("WEAK_COMMODITY_ENVIRONMENT", "ACTIVE" if change < Decimal("-10") else "INACTIVE", {"change_percent": str(change)})
    else:
        add("STRONG_COMMODITY_ENVIRONMENT", "UNAVAILABLE", {"reason": "verified commodity composite unavailable"}); add("WEAK_COMMODITY_ENVIRONMENT", "UNAVAILABLE", {"reason": "verified commodity composite unavailable"})
    return results


def persist_regimes(repo: Repository, as_of: str) -> dict[str, dict]:
    rows = repo.connection.execute("SELECT series_code FROM macro_series ORDER BY series_code").fetchall()
    series = {}
    for row in rows:
        points = query_as_of(repo.connection, row[0], as_of)
        series[row[0]] = [(p["period_end"], Decimal(p["value"])) for p in points]
    regimes = classify_regimes(series)
    generated = utc_now()
    for label, result in regimes.items():
        repo.connection.execute(
            "INSERT OR IGNORE INTO macro_regimes VALUES(?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), as_of[:10], label, result["state"], json.dumps(result["evidence"], sort_keys=True), RULES_VERSION, generated),
        )
    return regimes


def ingest_macro(settings, fx_dates: list[str] | None = None) -> dict:
    fx_dates = fx_dates or [f"{year}-01-02" for year in range(2020, date.today().year + 1)] + [date.today().isoformat()]
    with Repository(settings.database_path) as repo:
        repo.initialize()
        repo.ensure_source(SOURCE_ID, "Central Bank of Uzbekistan official macro feeds", "cbu.uz", "PRIMARY", "VERIFIED_AUTOMATED", {"policy": POLICY_URL, "money": MONEY_URL, "reserves": RESERVES_URL, "fx": FX_URL})
        run_id = repo.start_run(SOURCE_ID, PARSER_VERSION)
        retrieved_at = utc_now()
        processed = errors = 0
        error_messages = []
        jobs = [(POLICY_URL, parse_policy_rates, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"), (MONEY_URL, parse_money_supply, "application/json"), (RESERVES_URL, parse_reserves, "application/json")]
        for target in fx_dates:
            url = FX_URL.format(date=target)
            jobs.append((url, lambda payload, url=url: parse_fx(payload, url), "application/json"))
        for url, parser, media_type in jobs:
            try:
                payload = _download(url, settings.request_timeout_seconds, settings.retry_attempts, settings.retry_backoff_seconds)
                document_id = _archive(repo, settings.raw_data_dir, run_id, url, payload, retrieved_at, media_type)
                processed += _store_values(repo, document_id, retrieved_at, parser(payload))
            except Exception as exc:
                errors += 1; error_messages.append(f"{url}: {exc}")
        mappings = store_sector_mappings(repo)
        repo.connection.commit()
        regimes = persist_regimes(repo, retrieved_at)
        repo.connection.commit()
        status = "SUCCEEDED" if errors == 0 else ("PARTIAL" if processed else "FAILED")
        repo.finish_run(run_id, status, processed, errors, "\n".join(error_messages) or None)
        return {"status": status, "run_id": run_id, "observations_processed": processed, "source_errors": errors, "sector_mappings": mappings, "regimes": regimes, "vintage_policy": "FIRST_OBSERVED_BY_UZQUANT"}


def export_macro_outputs(database: Path, history_path: Path, mapping_path: Path, as_of: str | None = None) -> dict:
    as_of = as_of or utc_now()
    with Repository(database) as repo:
        repo.initialize()
        rows = repo.connection.execute("""SELECT ms.series_code,ms.name,mo.period_start,mo.period_end,mo.value,mo.unit,mo.currency,mo.initial_release_date,mo.revision_date,mo.vintage_known_at,mo.source_url,mo.retrieved_at
          FROM macro_observations mo JOIN macro_series ms USING(series_id) WHERE mo.vintage_known_at<=? ORDER BY ms.series_code,mo.period_end,mo.vintage_known_at""", (as_of,)).fetchall()
        mappings = repo.connection.execute("SELECT sector_code,macro_series_code,transmission_channel,directional_effect,evidence_basis,basis_type,mapping_version FROM sector_macro_exposures ORDER BY sector_code,macro_series_code").fetchall()
    history_path.parent.mkdir(parents=True, exist_ok=True)
    for path, data in ((history_path, rows), (mapping_path, mappings)):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(data[0].keys() if data else [])
            writer.writerows([tuple(row) for row in data])
    return {"history_rows": len(rows), "mapping_rows": len(mappings)}
