from __future__ import annotations

import hashlib
import json
import uuid

from .repository import Repository, utc_now

TAXONOMY_VERSION="financial-taxonomy/2.0.0"
NORMALIZATION_VERSION="financial-normalization/2.0.0"


def append_version(repo:Repository, observation_id:str, document_id:str, issuer_id:str,
                   statement_type:str, concept:str, period_start, period_end:str,
                   raw_value:str, normalized_value:str, currency, unit:str,
                   source_location:str, extraction_method:str, confidence:str,
                   value_status:str, parser_version:str, validation_state="VERIFIED",
                   taxonomy_version=TAXONOMY_VERSION,
                   normalization_version=NORMALIZATION_VERSION,
                   knowledge_date=None,created_at=None):
    doc=repo.connection.execute("SELECT publication_date,retrieved_at,reporting_perimeter,accounting_standard,audit_status FROM financial_documents WHERE document_id=?",(document_id,)).fetchone()
    if not doc: raise ValueError("unknown financial document")
    existing=repo.connection.execute("SELECT version_id FROM financial_observation_versions WHERE document_id=? AND canonical_concept=? AND source_location=? AND parser_version=? AND taxonomy_version=? AND normalization_version=?",(document_id,concept,source_location,parser_version,taxonomy_version,normalization_version)).fetchone()
    if existing: return existing[0]
    prior=repo.connection.execute("SELECT version_id FROM financial_observation_versions WHERE document_id=? AND canonical_concept=? AND source_location=? ORDER BY created_at DESC LIMIT 1",(document_id,concept,source_location)).fetchone()
    version_id=str(uuid.uuid4()); raw_id=repo.connection.execute("SELECT raw_value_id FROM financial_raw_values WHERE document_id=? AND source_location=?",(document_id,source_location)).fetchone()
    knowledge_date=knowledge_date or utc_now(); created_at=created_at or utc_now()
    repo.connection.execute("INSERT INTO financial_observation_versions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(
      version_id,observation_id,document_id,issuer_id,raw_id[0] if raw_id else None,concept,statement_type,
      period_start,period_end,doc[0],knowledge_date,raw_value,normalized_value,currency,unit,doc[2],doc[3],doc[4],
      extraction_method,parser_version,taxonomy_version,normalization_version,confidence,validation_state,
      value_status,source_location,created_at,prior[0] if prior else None,None))
    if prior: repo.connection.execute("UPDATE financial_observation_versions SET superseded_by_version_id=? WHERE version_id=?",(version_id,prior[0]))
    return version_id


def current_versions(repo:Repository, document_id:str):
    return repo.connection.execute("SELECT v.* FROM financial_observation_versions v WHERE v.document_id=? AND v.superseded_by_version_id IS NULL ORDER BY v.canonical_concept,v.source_location",(document_id,)).fetchall()


def exact_signal_version_ids(repo:Repository, signal_id:str):
    """Return only normalized observations consumed by a signal's stored factors.

    Factor source IDs may identify fundamental metrics or valuation records.  The
    former have relational analytical lineage; the latter retain exact immutable
    financial version IDs in their source payload.  Contextual issuer observations
    are intentionally excluded.
    """
    signal=repo.connection.execute(
        "SELECT security_id,data_snapshot_id,generated_at FROM research_signals WHERE signal_id=?",
        (signal_id,),
    ).fetchone()
    if not signal: raise KeyError(signal_id)
    source_ids=set()
    for row in repo.connection.execute(
        "SELECT source_record_ids_json FROM factor_scores "
        "WHERE security_id=? AND data_snapshot_id=? AND created_at=?",
        (signal[0],signal[1],signal[2]),
    ):
        source_ids.update(value for value in json.loads(row[0]) if value)
    if not source_ids: return ()
    marks=",".join("?" for _ in source_ids); args=tuple(sorted(source_ids))
    versions={r[0] for r in repo.connection.execute(
        f"SELECT observation_version_id FROM analytical_observation_lineage "
        f"WHERE analytical_record_id IN ({marks})",args
    )}
    for row in repo.connection.execute(
        f"SELECT source_observation_ids_json FROM valuation_records "
        f"WHERE valuation_id IN ({marks})",args
    ):
        versions.update(value for value in json.loads(row[0]) if value)
    # Legacy valuation rows used stable observation IDs in this field before
    # immutable version lineage was introduced.  They remain valid historical
    # records, but must never be mislabeled as exact version IDs or inserted
    # through the version foreign key.
    return tuple(sorted(
        version_id for version_id in versions
        if repo.connection.execute(
            "SELECT 1 FROM financial_observation_versions WHERE version_id=?",
            (version_id,),
        ).fetchone()
    ))


def link_signal_exact_versions(repo:Repository, signal_id:str, created_at=None):
    created_at=created_at or utc_now()
    versions=exact_signal_version_ids(repo,signal_id)
    for version_id in versions:
        repo.connection.execute(
            "INSERT OR IGNORE INTO signal_observation_lineage VALUES(?,?,?,?)",
            (signal_id,version_id,"EXACT",created_at),
        )
    return versions


def reconstruct_signal(repo:Repository, signal_id:str):
    signal=repo.connection.execute("SELECT * FROM research_signals WHERE signal_id=?",(signal_id,)).fetchone()
    if not signal: raise KeyError(signal_id)
    versions=[dict(r) for r in repo.connection.execute("SELECT v.* FROM signal_observation_lineage l JOIN financial_observation_versions v ON v.version_id=l.observation_version_id WHERE l.signal_id=? ORDER BY v.version_id",(signal_id,))]
    return {"signal":dict(signal),"normalized_financial_versions":versions,"payload_sha256":hashlib.sha256(json.dumps(versions,sort_keys=True,default=str).encode()).hexdigest()}
