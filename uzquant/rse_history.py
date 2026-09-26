from __future__ import annotations

import hashlib
import html
import json
import re
import time
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode

from .repository import Repository, stable_id, utc_now
from .rse_trade_export import ingest_trade_export, parse_trade_export
from .rse import fetch

HTML_PARSER_VERSION = "rse-trade-html/1.0.0"
_ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S | re.I)
_CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_LAST_PAGE_RE = re.compile(r"[?&]page=(\d+)[^\"]*[^>]*>[^<]*(?:Last|Последняя|So.nggi)", re.I)
_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}


def _text(fragment: str) -> str:
    return " ".join(html.unescape(_TAG_RE.sub(" ", fragment)).split())


def _decimal(value: str) -> str:
    from decimal import Decimal, InvalidOperation
    try:
        number = Decimal(value.replace(",", "").strip())
    except InvalidOperation as exc:
        raise ValueError(f"invalid numeric value: {value}") from exc
    return str(number)


def _timestamp(value: str) -> str:
    from datetime import datetime
    compact = value.replace(",", " ")
    parts = compact.split()
    if len(parts) < 4:
        raise ValueError(f"invalid RSE timestamp: {value}")
    if parts[0].isdigit():
        day, month_name, year, clock = int(parts[0]), parts[1].casefold(), int(parts[2]), parts[3]
    else:
        month_name, day, year, clock = parts[0].casefold(), int(parts[1]), int(parts[2]), parts[3]
    month = _MONTHS.get(month_name)
    if not month:
        raise ValueError(f"unsupported RSE month: {month_name}")
    return datetime.strptime(f"{year:04d}-{month:02d}-{day:02d} {clock}", "%Y-%m-%d %H:%M").isoformat()


def parse_trade_results_html(payload: bytes) -> tuple[list[dict[str, str]], int]:
    document = payload.decode("utf-8")
    rows = []
    for fragment in _ROW_RE.findall(document):
        cells = [_text(value) for value in _CELL_RE.findall(fragment)]
        if len(cells) != 10 or not re.fullmatch(r"UZ[A-Z0-9]+\s+[A-Z0-9]+", cells[2]):
            continue
        isin, ticker = cells[2].split()[:2]
        price, quantity = _decimal(cells[7]), _decimal(cells[8])
        currency_parts = cells[9].split(maxsplit=1)
        if len(currency_parts) != 2:
            raise ValueError("missing currency or turnover")
        currency, turnover = currency_parts[0], _decimal(currency_parts[1])
        from decimal import Decimal
        if Decimal(price) <= 0 or Decimal(quantity) <= 0 or Decimal(turnover) < 0:
            raise ValueError("impossible trade value")
        if abs(Decimal(price) * Decimal(quantity) - Decimal(turnover)) > Decimal("0.011"):
            raise ValueError("turnover mismatch")
        rows.append({"exchange_timestamp": _timestamp(cells[0]), "isin": isin, "ticker": ticker,
                     "issuer_name": cells[3], "source_security_type": cells[4], "market_code": cells[5],
                     "board_code": cells[6], "price": price, "quantity": quantity,
                     "turnover_value": turnover, "currency": currency})
    pages = [int(value) for value in re.findall(r"[?&]page=(\d+)", html.unescape(document))]
    return rows, max(pages, default=1)


def _archive_html(settings, repo, run_id, url: str, payload: bytes, retrieved_at: str):
    digest = hashlib.sha256(payload).hexdigest()
    document_id = stable_id("rse-trade-html", f"{url}:{digest}")
    path = settings.raw_data_dir / "uzse" / retrieved_at[:10] / f"trade-html-{digest}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(payload)
    if not repo.connection.execute("SELECT 1 FROM raw_documents WHERE document_id=?", (document_id,)).fetchone():
        repo.add_raw_document((document_id, "uzse-public-web", run_id, url, retrieved_at, None, "text/html", digest, str(path)))
    return document_id


def backfill_html(settings, job_limit: int = 1, pause_seconds: float = 1.0, tickers: set[str] | None = None) -> dict:
    completed = empty = failed = pages_fetched = trades = 0
    with Repository(settings.database_path) as repo:
        repo.initialize()
        clauses = ["status IN('PENDING','FAILED')"]
        parameters = []
        if tickers:
            clauses.append("ticker IN (%s)" % ",".join("?" for _ in tickers)); parameters.extend(sorted(tickers))
        jobs = repo.connection.execute(
            f"SELECT * FROM rse_history_acquisition_jobs WHERE {' AND '.join(clauses)} ORDER BY requested_begin,isin LIMIT ?",
            (*parameters, job_limit),
        ).fetchall()
    for job in jobs:
        run_id = None
        try:
            with Repository(settings.database_path) as repo:
                repo.initialize(); run_id = repo.start_run("uzse-public-web", HTML_PARSER_VERSION)
                stamp = utc_now(); repo.connection.execute("UPDATE rse_history_acquisition_jobs SET status='IN_PROGRESS',attempt_count=attempt_count+1,last_attempt_at=?,updated_at=?,error_details=NULL WHERE job_id=?", (stamp, stamp, job["job_id"])); repo.connection.commit()
            params = urlencode({"begin": date.fromisoformat(job["requested_begin"]).strftime("%d.%m.%Y"), "end": date.fromisoformat(job["requested_end"]).strftime("%d.%m.%Y"), "search_key": job["isin"], "mkt_id": job["market_code"], "locale": "en"})
            base = f"https://www.uzse.uz/trade_results?{params}"
            page = 1; all_records = []
            while True:
                url = base if page == 1 else base + f"&page={page}"
                payload = fetch(url, timeout=settings.request_timeout_seconds, attempts=settings.retry_attempts, backoff=settings.retry_backoff_seconds)
                parsed, last_page = parse_trade_results_html(payload); retrieved_at = utc_now()
                with Repository(settings.database_path) as repo:
                    repo.initialize(); document_id = _archive_html(settings, repo, run_id, url, payload, retrieved_at)
                    security = repo.connection.execute("SELECT security_id FROM identifier_history WHERE identifier_type='ISIN' AND identifier_value=? ORDER BY known_at DESC LIMIT 1", (job["isin"],)).fetchone()
                    if not security: raise ValueError(f"unresolved ISIN {job['isin']}")
                    capture_id = stable_id("rse-html-page", f"{job['job_id']}:{page}")
                    repo.connection.execute("INSERT OR IGNORE INTO rse_trade_html_pages VALUES(?,?,?,?,?,?,?,?)", (capture_id, job["job_id"], page, document_id, url, retrieved_at, len(parsed), HTML_PARSER_VERSION))
                    for index, row in enumerate(parsed, 1):
                        observed = date.fromisoformat(row["exchange_timestamp"][:10])
                        if row["isin"] != job["isin"] or row["market_code"] != job["market_code"] or not date.fromisoformat(job["requested_begin"]) <= observed <= date.fromisoformat(job["requested_end"]):
                            raise ValueError("RSE row outside requested identity/date/market scope")
                        trade_id = stable_id("rse-html-trade", f"{capture_id}:{index}")
                        repo.connection.execute("INSERT OR IGNORE INTO rse_trade_html_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (trade_id,capture_id,index,security[0],row["exchange_timestamp"],"Asia/Tashkent",row["isin"],row["ticker"],row["issuer_name"],row["source_security_type"],row["market_code"],row["board_code"],row["price"],row["quantity"],row["turnover_value"],row["currency"],document_id,HTML_PARSER_VERSION))
                        all_records.append((trade_id, document_id, row))
                    repo.connection.commit()
                pages_fetched += 1
                if page >= last_page: break
                page += 1; time.sleep(pause_seconds)
            with Repository(settings.database_path) as repo:
                repo.initialize(); now = utc_now()
                market_run = stable_id("rse-html-market-run", job["job_id"])
                repo.connection.execute("INSERT OR IGNORE INTO market_ingestion_runs(market_run_id,source_id,started_at,finished_at,status,securities_requested,securities_succeeded,records_processed,errors,parser_version) VALUES(?,'uzse-public-web',?,?, 'SUCCEEDED',1,1,?,0,?)", (market_run, now, now, len(all_records), HTML_PARSER_VERSION))
                by_day = {}
                for trade_id, document_id, row in all_records: by_day.setdefault(row["exchange_timestamp"][:10], []).append((trade_id, document_id, row))
                from decimal import Decimal
                for trade_date, day in by_day.items():
                    ordered = sorted(day, key=lambda item: item[2]["exchange_timestamp"])
                    prices = [Decimal(item[2]["price"]) for item in ordered]
                    volume = sum(Decimal(item[2]["quantity"]) for item in ordered); turnover = sum(Decimal(item[2]["turnover_value"]) for item in ordered)
                    values = {"open":str(prices[0]),"high":str(max(prices)),"low":str(min(prices)),"close":str(prices[-1]),"share_volume":str(volume),"turnover_value":str(turnover),"trade_count":len(day)}
                    payload_hash = hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest(); observation_id = stable_id("rse-html-observation", f"{job['isin']}:{trade_date}:{payload_hash}")
                    repo.connection.execute("""INSERT OR IGNORE INTO market_observations(observation_id,security_id,trade_date,source_timestamp,timezone,open,high,low,close,share_volume,turnover_value,trade_count,currency,source_id,document_id,market_run_id,series_type,parser_version,payload_hash,first_seen_at,last_seen_at,observation_status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'uzse-public-web',?,?,'RAW_OBSERVED',?,?,?,?,'TRADE_REPORTED')""", (observation_id,security[0],trade_date,now,"Asia/Tashkent",values["open"],values["high"],values["low"],values["close"],values["share_volume"],values["turnover_value"],values["trade_count"],day[0][2]["currency"],day[0][1],market_run,HTML_PARSER_VERSION,payload_hash,now,now))
                    for trade_id, _, _ in day: repo.connection.execute("INSERT OR IGNORE INTO market_observation_trade_lineage VALUES(?,?)", (observation_id,trade_id))
                final = "EMPTY" if not all_records else "IMPORTED"
                repo.connection.execute("UPDATE rse_history_acquisition_jobs SET status=?,error_details=NULL,updated_at=? WHERE job_id=?", (final,now,job["job_id"])); repo.finish_run(run_id,"SUCCEEDED",len(all_records),0); repo.connection.commit()
            empty += not all_records; completed += bool(all_records); trades += len(all_records)
            time.sleep(pause_seconds)
        except KeyboardInterrupt:
            with Repository(settings.database_path) as repo:
                repo.initialize(); repo.connection.execute("UPDATE rse_history_acquisition_jobs SET status='PENDING',error_details='collector interrupted; safe to resume',updated_at=? WHERE job_id=?", (utc_now(),job["job_id"]));
                if run_id: repo.finish_run(run_id,"FAILED",0,1,"collector interrupted; safe to resume")
                repo.connection.commit()
            raise
        except Exception as exc:
            failed += 1
            with Repository(settings.database_path) as repo:
                repo.initialize(); repo.connection.execute("UPDATE rse_history_acquisition_jobs SET status='FAILED',error_details=?,updated_at=? WHERE job_id=?", (str(exc),utc_now(),job["job_id"]));
                if run_id: repo.finish_run(run_id,"FAILED",0,1,str(exc))
                repo.connection.commit()
    return {"status":"SUCCEEDED" if not failed else "PARTIAL","jobs_imported":completed,"jobs_empty":empty,"jobs_failed":failed,"pages_fetched":pages_fetched,"trades":trades}


def _month_windows(begin: date, end: date):
    cursor = begin
    while cursor <= end:
        month_end = date(cursor.year, cursor.month, monthrange(cursor.year, cursor.month)[1])
        stop = min(month_end, end)
        yield cursor, stop
        cursor = stop + timedelta(days=1)


def plan_history(database_path: Path, begin: date, end: date, market_code: str = "STK") -> dict:
    if begin > end:
        raise ValueError("history begin date is after end date")
    created = existing = 0
    stamp = utc_now()
    with Repository(database_path) as repo:
        repo.initialize()
        securities = repo.connection.execute("""
            SELECT DISTINCT h.identifier_value isin,
              (SELECT identifier_value FROM identifier_history t WHERE t.security_id=h.security_id AND t.identifier_type='TICKER' ORDER BY known_at DESC LIMIT 1) ticker
            FROM identifier_history h
            WHERE h.identifier_type='ISIN'
              AND EXISTS(SELECT 1 FROM listings l WHERE l.security_id=h.security_id AND l.exchange_code='UZSE' AND l.board_code=? AND l.listing_status='ACTIVE')
            ORDER BY isin
        """, (market_code,)).fetchall()
        for security in securities:
            for start, stop in _month_windows(begin, end):
                job_id = stable_id("rse-history-job", f"{security['isin']}:{start}:{stop}:{market_code}")
                result = repo.connection.execute(
                    "INSERT OR IGNORE INTO rse_history_acquisition_jobs(job_id,isin,ticker,requested_begin,requested_end,market_code,status,created_at,updated_at) VALUES(?,?,?,?,?,?,'PENDING',?,?)",
                    (job_id, security["isin"], security["ticker"], start.isoformat(), stop.isoformat(), market_code, stamp, stamp),
                )
                created += result.rowcount
                existing += result.rowcount == 0
        repo.connection.commit()
        return {"status": "SUCCEEDED", "securities": len(securities), "jobs_created": created, "jobs_existing": existing, "begin": begin.isoformat(), "end": end.isoformat(), "market": market_code}


def next_job(database_path: Path) -> dict:
    with Repository(database_path) as repo:
        repo.initialize()
        row = repo.connection.execute("SELECT * FROM rse_history_acquisition_jobs WHERE status IN('PENDING','FAILED') ORDER BY CASE status WHEN 'PENDING' THEN 0 ELSE 1 END,requested_begin,isin LIMIT 1").fetchone()
        if row is None:
            return {"status": "QUEUE_EMPTY"}
        stamp = utc_now()
        repo.connection.execute("UPDATE rse_history_acquisition_jobs SET status='IN_PROGRESS',attempt_count=attempt_count+1,last_attempt_at=?,updated_at=?,error_details=NULL WHERE job_id=?", (stamp, stamp, row["job_id"]))
        repo.connection.commit()
        params = urlencode({"begin": date.fromisoformat(row["requested_begin"]).strftime("%d.%m.%Y"), "end": date.fromisoformat(row["requested_end"]).strftime("%d.%m.%Y"), "search_key": row["isin"], "mkt_id": row["market_code"]})
        return {"status": "READY", "job_id": row["job_id"], "isin": row["isin"], "ticker": row["ticker"], "begin": row["requested_begin"], "end": row["requested_end"], "market": row["market_code"], "export_url": f"https://www.uzse.uz/trade_results/export?{params}", "expected_inbox_name": f"{row['job_id']}.xlsx"}


def mark_job(database_path: Path, job_id: str, status: str, details: str | None = None) -> dict:
    if status not in {"SOURCE_BLOCKED", "FAILED", "PENDING"}:
        raise ValueError("unsupported manual job status")
    with Repository(database_path) as repo:
        repo.initialize()
        result = repo.connection.execute("UPDATE rse_history_acquisition_jobs SET status=?,error_details=?,updated_at=? WHERE job_id=?", (status, details, utc_now(), job_id))
        repo.connection.commit()
        if result.rowcount != 1:
            raise ValueError(f"unknown acquisition job {job_id}")
    return {"status": "SUCCEEDED", "job_id": job_id, "job_status": status}


def import_inbox(settings, inbox: Path) -> dict:
    inbox.mkdir(parents=True, exist_ok=True)
    imported = empty = failed = 0
    results = []
    with Repository(settings.database_path) as repo:
        repo.initialize()
        jobs = {row["job_id"]: dict(row) for row in repo.connection.execute("SELECT * FROM rse_history_acquisition_jobs WHERE status IN('IN_PROGRESS','DOWNLOADED','FAILED','VALIDATION_FAILED')")}
    for path in sorted(inbox.glob("*.xlsx")):
        job = jobs.get(path.stem)
        if job is None:
            continue
        try:
            payload = path.read_bytes()
            rows = parse_trade_export(payload)
            for row in rows:
                observed = date.fromisoformat(row["exchange_timestamp"][:10])
                if row["isin"] != job["isin"]:
                    raise ValueError(f"expected ISIN {job['isin']}, observed {row['isin']}")
                if row["market_code"] != job["market_code"]:
                    raise ValueError(f"expected market {job['market_code']}, observed {row['market_code']}")
                if not date.fromisoformat(job["requested_begin"]) <= observed <= date.fromisoformat(job["requested_end"]):
                    raise ValueError(f"trade timestamp outside requested range: {observed}")
            result = ingest_trade_export(settings, path, date.fromisoformat(job["requested_begin"]), date.fromisoformat(job["requested_end"]), job["market_code"], job["isin"])
            final_status = "EMPTY" if not rows else "IMPORTED"
            with Repository(settings.database_path) as repo:
                repo.initialize()
                repo.connection.execute("UPDATE rse_history_acquisition_jobs SET status=?,downloaded_path=?,file_sha256=?,capture_id=?,error_details=NULL,updated_at=? WHERE job_id=?", (final_status, str(path), hashlib.sha256(payload).hexdigest(), result["capture_id"], utc_now(), job["job_id"]))
                repo.connection.commit()
            empty += not rows
            imported += bool(rows)
            results.append({"job_id": job["job_id"], "status": final_status, "records": len(rows)})
        except Exception as exc:
            with Repository(settings.database_path) as repo:
                repo.initialize()
                repo.connection.execute("UPDATE rse_history_acquisition_jobs SET status='VALIDATION_FAILED',downloaded_path=?,error_details=?,updated_at=? WHERE job_id=?", (str(path), str(exc), utc_now(), job["job_id"]))
                repo.connection.commit()
            failed += 1
            results.append({"job_id": job["job_id"], "status": "VALIDATION_FAILED", "error": str(exc)})
    return {"status": "SUCCEEDED" if not failed else "PARTIAL", "imported_files": imported, "empty_files": empty, "failed_files": failed, "results": results}


def queue_status(database_path: Path) -> dict:
    with Repository(database_path) as repo:
        repo.initialize()
        counts = {row[0]: row[1] for row in repo.connection.execute("SELECT status,count(*) FROM rse_history_acquisition_jobs GROUP BY status")}
        return {"status": "SUCCEEDED", "total": sum(counts.values()), "by_status": counts}
