from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repository:
    """Small persistence layer that preserves provenance and point-in-time truth."""

    def __init__(self, database: str | Path = ":memory:") -> None:
        self.connection = sqlite3.connect(str(database))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def initialize(self) -> None:
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        self.connection.executescript(schema)
        self.connection.execute(
            "INSERT OR IGNORE INTO schema_version(version, applied_at) VALUES (1, ?)",
            (_utc_now(),),
        )
        self.connection.commit()

    def add_source(
        self,
        *,
        name: str,
        domain: str,
        authority_level: str,
        access_status: str,
        terms_notes: str | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """INSERT INTO sources(name, domain, authority_level, access_status, terms_notes)
               VALUES (?, ?, ?, ?, ?)""",
            (name, domain, authority_level, access_status, terms_notes),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def archive_snapshot(
        self,
        *,
        source_id: int,
        source_url: str,
        raw_content: bytes,
        media_type: str,
        retrieved_at: str,
        publication_at: str | None = None,
    ) -> int:
        digest = hashlib.sha256(raw_content).hexdigest()
        cursor = self.connection.execute(
            """INSERT INTO source_snapshots(
                   source_id, source_url, retrieved_at, publication_at,
                   media_type, sha256, raw_content
               ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                source_url,
                retrieved_at,
                publication_at,
                media_type,
                digest,
                raw_content,
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def add_issuer(self, canonical_name: str, *, country_code: str = "UZ") -> int:
        cursor = self.connection.execute(
            "INSERT INTO issuers(canonical_name, country_code, created_at) VALUES (?, ?, ?)",
            (canonical_name, country_code, _utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def add_security(
        self,
        *,
        issuer_id: int,
        security_class: str,
        currency: str | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """INSERT INTO securities(issuer_id, security_class, currency, created_at)
               VALUES (?, ?, ?, ?)""",
            (issuer_id, security_class, currency, _utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def add_security_identifier(
        self,
        *,
        security_id: int,
        identifier_type: str,
        identifier_value: str,
        known_at: str,
        snapshot_id: int,
        valid_from: str | None = None,
        valid_to: str | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """INSERT INTO security_identifiers(
                   security_id, identifier_type, identifier_value, valid_from,
                   valid_to, known_at, snapshot_id
               ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                security_id,
                identifier_type,
                identifier_value,
                valid_from,
                valid_to,
                known_at,
                snapshot_id,
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def add_reported_fact(
        self,
        *,
        snapshot_id: int,
        fact_name: str,
        known_at: str,
        value_kind: str,
        confidence: str,
        issuer_id: int | None = None,
        security_id: int | None = None,
        value_numeric: str | None = None,
        value_text: str | None = None,
        unit: str | None = None,
        currency: str | None = None,
        valid_at: str | None = None,
        period_start: str | None = None,
        period_end: str | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """INSERT INTO reported_facts(
                   issuer_id, security_id, snapshot_id, fact_name, value_numeric,
                   value_text, unit, currency, period_start, period_end, valid_at,
                   known_at, value_kind, confidence
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                issuer_id,
                security_id,
                snapshot_id,
                fact_name,
                value_numeric,
                value_text,
                unit,
                currency,
                period_start,
                period_end,
                valid_at,
                known_at,
                value_kind,
                confidence,
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def facts_known_at(
        self,
        *,
        as_of: str,
        fact_name: str | None = None,
        issuer_id: int | None = None,
        security_id: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["known_at <= ?"]
        values: list[Any] = [as_of]
        for column, value in (
            ("fact_name", fact_name),
            ("issuer_id", issuer_id),
            ("security_id", security_id),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                values.append(value)
        rows = self.connection.execute(
            f"SELECT * FROM reported_facts WHERE {' AND '.join(clauses)} ORDER BY known_at, fact_id",
            values,
        ).fetchall()
        return [dict(row) for row in rows]

    def record_validation_issue(
        self,
        *,
        issue_type: str,
        severity: str,
        entity_type: str,
        details: str,
        entity_id: int | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """INSERT INTO validation_issues(
                   issue_type, severity, entity_type, entity_id, detected_at, details
               ) VALUES (?, ?, ?, ?, ?, ?)""",
            (issue_type, severity, entity_type, entity_id, _utc_now(), details),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Repository":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

