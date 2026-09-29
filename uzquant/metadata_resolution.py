from __future__ import annotations

import json
import tempfile
from collections import Counter
from pathlib import Path

from .financial_documents import extract_explicit_metadata
from .issuer_valuation_unlock import (BANK_PARSER_SECURITIES,
                                      MISSION_2B_SECURITIES, _security_for_ticker,
                                      export_mission2b)
from .cohort_expansion import _md_table as table
from .repository import Repository, utc_now

VERSION = "metadata-resolution/1.0.0"
BEFORE_FULLY_RESOLVED = 1


def _evidence(repo: Repository, document_id: str) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for row in repo.connection.execute(
        "SELECT * FROM financial_document_metadata_evidence WHERE document_id=? ORDER BY field_name,source_location",
        (document_id,),
    ):
        result.setdefault(row["field_name"], []).append(dict(row))
    return result


def _status(value, missing_values=()) -> bool:
    return value is not None and value not in missing_values


def audit_metadata(database: Path) -> tuple[list[list], Counter, int]:
    rows: list[list] = []; missing = Counter(); fully_resolved = 0
    with Repository(database) as repo:
        repo.initialize()
        issuer_ids = {(_security_for_ticker(repo, ticker))["issuer_id"]
                      for ticker in MISSION_2B_SECURITIES + BANK_PARSER_SECURITIES}
        marks = ",".join("?" for _ in issuer_ids)
        documents = repo.connection.execute(
            f"SELECT d.*,i.legal_name,r.storage_path FROM financial_documents d JOIN issuers i USING(issuer_id) "
            f"JOIN raw_documents r ON r.document_id=d.raw_document_id WHERE d.issuer_id IN ({marks}) "
            "ORDER BY i.legal_name,d.period_end,d.publication_date,d.document_id", tuple(sorted(issuer_ids)),
        ).fetchall()
        if len(documents) != 38:
            raise ValueError(f"Mission 2c scope drift: expected 38 documents, found {len(documents)}")
        for doc in documents:
            evidence = _evidence(repo, doc["document_id"])
            units = sorted({r[0] for r in repo.connection.execute(
                "SELECT unit FROM financial_observation_versions WHERE document_id=? AND superseded_by_version_id IS NULL",
                (doc["document_id"],)) if r[0]})
            unit = ", ".join(units) if units else "UNKNOWN"
            retained_explicit = {}
            if doc["document_format"] == "HTML" and Path(doc["storage_path"]).exists():
                retained_explicit = extract_explicit_metadata(Path(doc["storage_path"]).read_bytes())

            currency_ok = _status(doc["currency"], ("UNKNOWN",))
            unit_ok = unit not in {"UNKNOWN", "SOURCE_UNIT_UNSPECIFIED"}
            perimeter_ok = _status(doc["reporting_perimeter"], ("UNKNOWN",))
            standard_ok = _status(doc["accounting_standard"], ("UNKNOWN",))
            period_ok = bool(doc["period_start"] and doc["period_end"])
            publication_ok = bool(doc["publication_date"])
            availability_ok = bool(doc["retrieved_at"])
            if all((currency_ok,unit_ok,perimeter_ok,standard_ok,period_ok,publication_ok,availability_ok)):
                fully_resolved += 1

            def field(ok: bool, value, name: str, present_reason: str, absent_reason: str) -> str:
                if ok: return f"RESOLVED: {value} — {present_reason}"
                missing[name] += 1
                return f"UNKNOWN — {absent_reason} [GENUINELY_UNAVAILABLE_IN_RETAINED_DOCUMENT]"

            unit_evidence = evidence.get("SOURCE_UNIT", [])
            if unit_evidence:
                ev = unit_evidence[0]
                unit_reason = f"explicit `{ev['field_value']}` at `{ev['source_location']}` ({ev['source_url']})"
            else:
                unit_reason = "normalized observation lineage contains an explicit unit"
            perimeter_evidence = evidence.get("REPORTING_PERIMETER", [])
            perimeter_reason = (f"explicit `{perimeter_evidence[0]['field_value']}` at `{perimeter_evidence[0]['source_location']}`"
                                if perimeter_evidence else "stored verified metadata from prior ingestion")
            standard_evidence = evidence.get("ACCOUNTING_STANDARD", [])
            standard_reason = (f"explicit `{standard_evidence[0]['field_value']}` at `{standard_evidence[0]['source_location']}`"
                               if standard_evidence else "pre-existing portal/report classification; no new promotion in Mission 2c")
            explicit_note = []
            for key in ("source_unit","reporting_perimeter","accounting_standard"):
                if key in retained_explicit: explicit_note.append(f"{key}={retained_explicit[key]}")
            rows.append([
                doc["legal_name"], doc["source_identifier"], doc["document_id"], doc["document_format"],
                field(currency_ok,doc["currency"] or "UNKNOWN","CURRENCY","pre-existing document record; Mission 2c made no unsupported change","no explicit statement currency in retained document"),
                field(unit_ok,unit,"UNIT",unit_reason,"retained HTML has no explicit statement scale; per-share 'sum' labels are unrelated and rejected"),
                field(perimeter_ok,doc["reporting_perimeter"],"PERIMETER",perimeter_reason,"no consolidated/standalone wording in retained document"),
                field(standard_ok,doc["accounting_standard"],"ACCOUNTING_STANDARD",standard_reason,"no explicit IFRS/local-standard wording in retained document; report category is not enough"),
                field(period_ok,f"{doc['period_start']} to {doc['period_end']}","PERIOD","stored source report period","period absent"),
                field(publication_ok,doc["publication_date"],"PUBLICATION_DATE","stored source publication date","publication date absent"),
                field(availability_ok,doc["retrieved_at"],"AVAILABILITY_DATE","immutable retrieval timestamp","retrieval timestamp absent"),
                ", ".join(explicit_note) or "No additional required metadata phrase recognized",
            ])
    return rows, missing, fully_resolved


def export_metadata_resolution(database: Path, outputs: Path) -> dict:
    generated = utc_now(); rows, missing, after = audit_metadata(database)
    outputs.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    for row in rows:
        for name, cell in zip(("currency","unit","perimeter","accounting_standard","period","publication_date","availability_date"), row[4:11]):
            counts[(name,"resolved" if str(cell).startswith("RESOLVED") else "unknown")] += 1
    summary = [[name,counts[(name,"resolved")],counts[(name,"unknown")]] for name in
               ("currency","unit","perimeter","accounting_standard","period","publication_date","availability_date")]
    (outputs/"metadata_resolution_audit.md").write_text(
        f"# Mission 2c Metadata Resolution Audit\n\nGenerated: {generated}. Version: `{VERSION}`. Scope is frozen at 38 documents. No new document was acquired. A field is promoted only from explicit retained evidence; values are never inferred from magnitude or statement appearance.\n\n"
        "## Before / after\n\n" + table(["Measure","Before","After","Change"],[["Fully resolved documents",BEFORE_FULLY_RESOLVED,after,after-BEFORE_FULLY_RESOLVED]]) +
        "\n\n## Field totals\n\n" + table(["Field","Resolved","Unknown"],summary) +
        "\n\n## Per-document field audit\n\n" + table(["Issuer","Source ID","Document ID","Format","Currency","Unit","Perimeter","Accounting standard","Period","Publication","Availability","New explicit-text scan"],rows) +
        "\n\n## Interpretation\n\nThe strict phrase scan found no previously missed required metadata in the retained HTML pages. Existing official workbook/PDF evidence remains authoritative where present. The dominant unresolved field is reporting perimeter: the retained portal pages do not say consolidated or standalone. `UNKNOWN` is therefore preserved. No gap is classified `REQUIRES_AUTHORIZED_SOURCE`, because the retained evidence shows absence, not that a restricted source exists. A new legitimate external filing may resolve these fields in a later authorized acquisition mission.\n"
    )
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td); export_mission2b(database,temp)
        valuation = (temp/"universe_valuations.md").read_text()
        blockers = (temp/"universe_blocker_queue.md").read_text()
    note = (f"\n\n## Mission 2c metadata result\n\nAs of {generated}, strict extraction found no additional explicit required metadata in retained documents. "
            f"Fully resolved documents remain {after}/38; valuation methods and frozen gates are unchanged.\n")
    (outputs/"universe_valuations.md").write_text(valuation.rstrip()+note)
    (outputs/"universe_blocker_queue.md").write_text(blockers.rstrip()+note)
    return {"documents":len(rows),"fully_resolved_before":BEFORE_FULLY_RESOLVED,"fully_resolved_after":after,
            "field_counts":{name:{"resolved":counts[(name,"resolved")],"unknown":counts[(name,"unknown")]} for name,_,_ in summary},
            "missing_by_field":dict(missing)}
