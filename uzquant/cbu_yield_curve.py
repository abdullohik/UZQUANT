from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .config import Settings
from .repository import Repository, stable_id, utc_now

SOURCE_ID = "cbu-government-yield-curve"
RESULTS_URL = "https://uz-yield-curve.cbu.uz/api/open/yield-curve-results/"
POINTS_URL = "https://uz-yield-curve.cbu.uz/api/open/yield-curve-points/"
METHODOLOGY_URL = "https://cbu.uz/en/monetary-policy/local-currency-yield-curve/"
PARSER_VERSION = "cbu-yield-curve/1.0.0"
METHODOLOGY = (
    "CBU theoretical average and smoothed national-currency government-securities curve; "
    "Nelson-Siegel; continuously compounded; weekly source observations with interpolation, "
    "extrapolation and weighting"
)


@dataclass(frozen=True)
class CurvePoint:
    source_point_id: int
    source_result_id: int
    tenor_label: str
    tenor_days: int
    maturity_date: str
    zero_rate_percent: Decimal
    discount_factor: Decimal
    forward_rate_percent: Decimal | None


def _download(url: str, timeout: float, attempts: int, backoff: float) -> bytes:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "UZQUANT/0.1 valuation-research"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - live-network path
            last = exc
            if attempt + 1 < attempts:
                time.sleep(backoff * (2**attempt))
    raise RuntimeError(f"download failed for {url}: {last}")


def parse_curve_payloads(results_payload: bytes, points_payload: bytes):
    results = json.loads(results_payload)
    raw_points = json.loads(points_payload)
    if not isinstance(results, list) or not isinstance(raw_points, list):
        raise ValueError("CBU curve APIs must return JSON arrays")
    result_map = {}
    for row in results:
        result_id = int(row["id"])
        curve_date = str(row["date"])
        datetime.fromisoformat(curve_date)
        result_map[result_id] = row
    points: list[CurvePoint] = []
    for row in raw_points:
        result_id = int(row["yieldCurveResultsId"])
        if result_id not in result_map:
            continue
        try:
            zero = Decimal(str(row["zeroRate"]))
            discount = Decimal(str(row["discount"]))
            forward = Decimal(str(row["forwardRate"])) if row.get("forwardRate") is not None else None
        except (InvalidOperation, KeyError) as exc:
            raise ValueError("invalid CBU curve numeric field") from exc
        tenor_days = int(row["deltaPeriods"])
        if tenor_days < 0 or discount <= 0:
            raise ValueError("invalid CBU curve point")
        points.append(CurvePoint(int(row["id"]), result_id, str(row["str"]), tenor_days,
                                 str(row["date"]), zero, discount, forward))
    if not result_map or not points:
        raise ValueError("empty CBU curve payload")
    return result_map, points


def _archive(repo: Repository, settings: Settings, run_id: str, url: str, payload: bytes,
             retrieved_at: str) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    path = settings.raw_data_dir / "cbu" / "yield_curve" / f"{digest}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(payload)
    document_id = stable_id("raw-document", f"{url}:{retrieved_at}")
    repo.add_raw_document((document_id, SOURCE_ID, run_id, url, retrieved_at, None,
                           "application/json", digest, str(path)))
    return document_id


def store_curve_payloads(repo: Repository, results_payload: bytes, points_payload: bytes,
                         retrieved_at: str, results_document_id: str,
                         points_document_id: str) -> dict:
    results, points = parse_curve_payloads(results_payload, points_payload)
    point_groups: dict[int, list[CurvePoint]] = {}
    for point in points:
        point_groups.setdefault(point.source_result_id, []).append(point)
    vintages = stored_points = 0
    for result_id, result in sorted(results.items(), key=lambda item: item[1]["date"]):
        group = point_groups.get(result_id, [])
        if not group:
            continue
        curve_id = stable_id("cbu-curve-vintage", f"{result_id}:{retrieved_at}")
        revision = str(result.get("codeRevisionNumber") or result.get("codeRevisionDate") or "") or None
        repo.connection.execute(
            "INSERT OR IGNORE INTO government_yield_curve_vintages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (curve_id, result_id, result["date"], "UZS", "NOMINAL", "CONTINUOUS", METHODOLOGY,
             SOURCE_ID, RESULTS_URL, METHODOLOGY_URL, retrieved_at, results_document_id,
             points_document_id, revision, "AUTHORITATIVE_SOURCE"),
        )
        if repo.connection.execute("SELECT changes()").fetchone()[0]:
            vintages += 1
        for point in group:
            point_id = stable_id("cbu-curve-point", f"{curve_id}:{point.source_point_id}")
            repo.connection.execute(
                "INSERT OR IGNORE INTO government_yield_curve_points VALUES(?,?,?,?,?,?,?,?,?,?)",
                (point_id, curve_id, point.source_point_id, point.tenor_label, point.tenor_days,
                 point.maturity_date, str(point.zero_rate_percent), str(point.discount_factor),
                 str(point.forward_rate_percent) if point.forward_rate_percent is not None else None,
                 "OBSERVED"),
            )
            if repo.connection.execute("SELECT changes()").fetchone()[0]:
                stored_points += 1
    return {"curve_vintages": vintages, "curve_points": stored_points,
            "source_results": len(results), "source_points": len(points),
            "latest_curve_date": max(row["date"] for row in results.values())}


def ingest_cbu_yield_curve(settings: Settings) -> dict:
    with Repository(settings.database_path) as repo:
        repo.initialize()
        repo.ensure_source(SOURCE_ID, "CBU government-securities yield curve",
                           "uz-yield-curve.cbu.uz", "PRIMARY", "VERIFIED_AUTOMATED",
                           {"results_url": RESULTS_URL, "points_url": POINTS_URL,
                            "methodology_url": METHODOLOGY_URL, "currency": "UZS",
                            "basis": "NOMINAL", "compounding": "CONTINUOUS"})
        run_id = repo.start_run(SOURCE_ID, PARSER_VERSION)
        retrieved_at = utc_now()
        try:
            results_payload = _download(RESULTS_URL, settings.request_timeout_seconds,
                                        settings.retry_attempts, settings.retry_backoff_seconds)
            points_payload = _download(POINTS_URL, settings.request_timeout_seconds,
                                       settings.retry_attempts, settings.retry_backoff_seconds)
            results_doc = _archive(repo, settings, run_id, RESULTS_URL, results_payload, retrieved_at)
            points_doc = _archive(repo, settings, run_id, POINTS_URL, points_payload, retrieved_at)
            summary = store_curve_payloads(repo, results_payload, points_payload, retrieved_at,
                                           results_doc, points_doc)
            repo.connection.commit()
            repo.finish_run(run_id, "SUCCEEDED", summary["curve_points"], 0,
                            json.dumps(summary, sort_keys=True))
            return {"status": "SUCCEEDED", "run_id": run_id, **summary}
        except Exception as exc:
            repo.connection.rollback()
            repo.finish_run(run_id, "FAILED", 0, 1, str(exc))
            return {"status": "FAILED", "run_id": run_id, "error": str(exc)}


def curve_as_of(connection, as_of_timestamp: str, curve_date: str | None = None):
    date_clause = "AND v.curve_date<=?" if curve_date else ""
    params = [as_of_timestamp]
    if curve_date:
        params.append(curve_date)
    sql = f"""WITH eligible AS (
      SELECT v.*,ROW_NUMBER() OVER(PARTITION BY v.curve_date
        ORDER BY v.retrieved_at DESC) AS rn
      FROM government_yield_curve_vintages v
      WHERE v.retrieved_at<=? {date_clause}
    ), latest AS (
      SELECT * FROM eligible WHERE rn=1 ORDER BY curve_date DESC LIMIT 1
    ) SELECT p.*,l.curve_date,l.currency,l.rate_basis,l.compounding,l.retrieved_at,
             l.source_url,l.methodology_url,l.source_api_version,l.provenance_class
      FROM latest l JOIN government_yield_curve_points p USING(curve_vintage_id)
      ORDER BY p.tenor_days"""
    return connection.execute(sql, params).fetchall()
