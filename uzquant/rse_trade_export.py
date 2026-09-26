from __future__ import annotations

import hashlib
import io
import shutil
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .repository import Repository, stable_id, utc_now

SOURCE_ID = "uzse-public-web"
PARSER_VERSION = "rse-trade-export/1.0.0"
MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
HEADERS = ["Время", "Код ЦБ", "Тикер", "Эмитент", "Тип ценной бумаги", "Рынок", "Площадка", "Торговая цена", "Кол-во ЦБ", "Объём торгов"]


def _column_index(reference: str) -> int:
    letters = "".join(ch for ch in reference if ch.isalpha())
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter.upper()) - 64
    return value - 1


def _xlsx_rows(payload: bytes) -> list[list[str]]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(io.BytesIO(payload)) as archive:
        strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(node.text or "" for node in item.findall(".//m:t", ns)) for item in root.findall("m:si", ns)]
        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in root.findall(".//m:row", ns):
            values = [""] * 10
            for cell in row.findall("m:c", ns):
                index = _column_index(cell.attrib.get("r", "A1"))
                if index >= len(values):
                    continue
                inline = cell.find("m:is", ns)
                node = cell.find("m:v", ns)
                if inline is not None:
                    value = "".join(item.text or "" for item in inline.findall(".//m:t", ns))
                else:
                    value = "" if node is None else node.text or ""
                    if cell.attrib.get("t") == "s" and value:
                        value = strings[int(value)]
                values[index] = value.strip()
            rows.append(values)
        return rows


def parse_trade_export(payload: bytes) -> list[dict[str, str]]:
    rows = _xlsx_rows(payload)
    if not rows or rows[0] != HEADERS:
        raise ValueError(f"unexpected RSE trade-export headers: {rows[0] if rows else 'EMPTY'}")
    parsed = []
    for row_number, row in enumerate(rows[1:], start=2):
        if not any(row):
            continue
        if len(row) != 10 or any(value == "" for value in row):
            raise ValueError(f"missing field in source row {row_number}")
        try:
            stamp = datetime.strptime(row[0], "%d.%m.%Y %H:%M:%S")
            price, quantity, turnover = Decimal(row[7]), Decimal(row[8]), Decimal(row[9])
        except (ValueError, InvalidOperation) as exc:
            raise ValueError(f"invalid typed value in source row {row_number}") from exc
        if price <= 0 or quantity <= 0 or turnover < 0:
            raise ValueError(f"impossible trade value in source row {row_number}")
        if abs(price * quantity - turnover) > Decimal("0.011"):
            raise ValueError(f"turnover mismatch in source row {row_number}")
        parsed.append({
            "source_row_number": str(row_number), "exchange_timestamp": stamp.isoformat(),
            "isin": row[1], "ticker": row[2], "issuer_name": row[3],
            "source_security_type": row[4], "market_code": row[5], "board_code": row[6],
            "price": str(price), "quantity": str(quantity), "turnover_value": str(turnover),
        })
    return parsed


def ingest_trade_export(settings, source_file: Path, requested_begin: date, requested_end: date, market_code: str = "STK", search_key: str | None = None) -> dict:
    payload = source_file.read_bytes()
    rows = parse_trade_export(payload)
    digest = hashlib.sha256(payload).hexdigest()
    retrieved_at = utc_now()
    source_url = "https://www.uzse.uz/trade_results?locale=en"
    with Repository(settings.database_path) as repo:
        repo.initialize()
        run_id = repo.start_run(SOURCE_ID, PARSER_VERSION)
        raw_path = settings.raw_data_dir / "uzse" / retrieved_at[:10] / f"trade-results-{digest}.xlsx"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if not raw_path.exists():
            shutil.copyfile(source_file, raw_path)
        captures = repo.connection.execute("SELECT c.capture_id,c.raw_document_id FROM rse_trade_export_captures c JOIN raw_documents r ON r.document_id=c.raw_document_id WHERE r.sha256=? AND c.requested_begin=? AND c.requested_end=? AND c.market_code=? AND coalesce(c.search_key,'')=coalesce(?,'')", (digest, requested_begin.isoformat(), requested_end.isoformat(), market_code, search_key)).fetchone()
        if captures:
            repo.finish_run(run_id, "SUCCEEDED", 0, 0, "idempotent existing capture")
            return {"run_id": run_id, "capture_id": captures[0], "status": "SUCCEEDED", "records_inserted": 0, "idempotent": True}
        document_id = stable_id("rse-trade-export", f"{digest}:{requested_begin}:{requested_end}:{market_code}:{search_key or ''}")
        existing = repo.connection.execute("SELECT 1 FROM raw_documents WHERE document_id=?", (document_id,)).fetchone()
        if not existing:
            repo.add_raw_document((document_id, SOURCE_ID, run_id, source_url, retrieved_at, None, MEDIA_TYPE, digest, str(raw_path)))
        identities = {}
        ambiguous = set()
        for row in repo.connection.execute("SELECT identifier_value,security_id FROM identifier_history WHERE identifier_type='ISIN'"):
            prior = identities.get(row[0])
            if prior and prior != row[1]:
                ambiguous.add(row[0])
            else:
                identities[row[0]] = row[1]
        capture_id = stable_id("rse-trade-capture", f"{digest}:{requested_begin}:{requested_end}:{market_code}:{search_key or ''}")
        matched = sum(row["isin"] in identities and row["isin"] not in ambiguous for row in rows)
        unresolved = sum(row["isin"] not in identities and row["isin"] not in ambiguous for row in rows)
        if rows:
            first_stamp = min(row["exchange_timestamp"] for row in rows)
            last_stamp = max(row["exchange_timestamp"] for row in rows)
            coverage = "OFFICIAL_EXPORT_PARTIAL_CURRENT_DAY" if requested_end >= date.fromisoformat(retrieved_at[:10]) else "OFFICIAL_EXPORT_HISTORICAL_RANGE"
        else:
            first_stamp = last_stamp = retrieved_at
            coverage = "EMPTY"
        repo.connection.execute(
            "INSERT INTO rse_trade_export_captures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (capture_id, document_id, SOURCE_ID, requested_begin.isoformat(), requested_end.isoformat(), market_code, search_key, retrieved_at,
             first_stamp, last_stamp, len(rows), matched, unresolved, coverage, PARSER_VERSION),
        )
        for row in rows:
            isin = row["isin"]
            if isin in ambiguous:
                security_id, identity_status = None, "AMBIGUOUS_ISIN"
            elif isin in identities:
                security_id, identity_status = identities[isin], "MATCHED_ISIN"
            else:
                security_id, identity_status = None, "UNRESOLVED_ISIN"
            repo.connection.execute(
                "INSERT INTO rse_trade_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (stable_id("rse-trade-row", f"{capture_id}:{row['source_row_number']}"), capture_id, int(row["source_row_number"]), security_id,
                 identity_status, row["exchange_timestamp"], "Asia/Tashkent", isin, row["ticker"], row["issuer_name"], row["source_security_type"],
                 row["market_code"], row["board_code"], row["price"], row["quantity"], row["turnover_value"], "UZS", document_id, PARSER_VERSION),
            )
        repo.connection.commit()
        repo.finish_run(run_id, "SUCCEEDED", len(rows), 0)
        return {"run_id": run_id, "capture_id": capture_id, "status": "SUCCEEDED", "records_inserted": len(rows),
                "identity_matched": matched, "identity_unresolved": unresolved, "coverage_status": coverage,
                "sha256": digest, "raw_path": str(raw_path), "idempotent": False}
