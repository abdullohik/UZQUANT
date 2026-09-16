from __future__ import annotations

import json
import uuid
from collections import Counter

from .financial_documents import REPORT_ISINS, REPORTS
from .identity import RESOLVED, record_conflict, resolve_security_pair
from .repository import Repository, utc_now


def _record(repo, table, record_id, issuer_id, canonical_id, determination, reason):
    repo.connection.execute(
        "INSERT INTO identity_contamination_audit VALUES(?,?,?,?,?,?,?,?) "
        "ON CONFLICT(table_name,record_id) DO UPDATE SET old_issuer_id=excluded.old_issuer_id,"
        "canonical_issuer_id=excluded.canonical_issuer_id,determination=excluded.determination,"
        "reason=excluded.reason,audited_at=excluded.audited_at",
        (str(uuid.uuid4()), table, str(record_id), issuer_id, canonical_id,
         determination, reason, utc_now()),
    )


def backfill_document_assignments(repo: Repository):
    report_tickers={bits.rsplit("/",1)[-1]:ticker for ticker,bits,*_ in REPORTS}
    counts=Counter()
    for doc in repo.connection.execute("SELECT d.document_id,d.issuer_id,d.source_identifier,d.publication_date,c.validation_status FROM financial_documents d LEFT JOIN financial_document_entity_checks c USING(document_id)").fetchall():
        ticker=report_tickers.get(doc["source_identifier"])
        if not ticker:
            status="QUARANTINED" if doc["validation_status"]=="MISMATCH" else "IDENTITY_UNRESOLVED"; resolution=None
            evidence={"reason":"SOURCE_IDENTIFIER_NOT_IN_VERIFIED_REPORT_CATALOG"}
        else:
            resolution=resolve_security_pair(repo,ticker,REPORT_ISINS[ticker],doc["publication_date"],utc_now())
            status="VERIFIED" if resolution.status==RESOLVED and resolution.issuer_id==doc["issuer_id"] else ("QUARANTINED" if resolution.status==RESOLVED else resolution.status)
            evidence={"ticker":ticker,"isin":REPORT_ISINS[ticker],"resolution":resolution.status,"reason":resolution.reason,"evidence_ids":resolution.evidence_ids}
        canonical=resolution.canonical_issuer_id if resolution and resolution.status==RESOLVED else None
        security=resolution.security_id if resolution and resolution.status==RESOLVED else None
        repo.connection.execute(
            "INSERT INTO financial_document_identity_assignments VALUES(?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(document_id) DO UPDATE SET canonical_issuer_id=excluded.canonical_issuer_id,"
            "security_id=excluded.security_id,publication_date=excluded.publication_date,"
            "assignment_status=excluded.assignment_status,assignment_method=excluded.assignment_method,"
            "evidence_json=excluded.evidence_json,assigned_at=excluded.assigned_at",
            (str(uuid.uuid4()),doc["document_id"],canonical,security,doc["publication_date"],status,
             "EFFECTIVE_DATED_TICKER_AND_ISIN",json.dumps(evidence,sort_keys=True,default=str),utc_now()),
        )
        if status!="VERIFIED":
            existing=repo.connection.execute("SELECT 1 FROM identity_resolution_conflicts WHERE conflict_type='EXISTING_FINANCIAL_DOCUMENT_ASSIGNMENT' AND identifier_value=? AND observation_date=? AND status='UNRESOLVED'",(doc["source_identifier"],doc["publication_date"])).fetchone()
            if not existing:
                record_conflict(repo,"EXISTING_FINANCIAL_DOCUMENT_ASSIGNMENT", "SOURCE_IDENTIFIER",doc["source_identifier"],doc["publication_date"],[doc["issuer_id"]],evidence)
        else:
            repo.connection.execute("UPDATE identity_resolution_conflicts SET status='RESOLVED' WHERE conflict_type='EXISTING_FINANCIAL_DOCUMENT_ASSIGNMENT' AND identifier_value=?",(doc["source_identifier"],))
        counts[status]+=1
    return dict(counts)


def contamination_audit(repo: Repository):
    tables={
      "financial_documents":("document_id","issuer_id",None),
      "financial_raw_values":("raw_value_id",None,"document_id"),
      "financial_observations":("observation_id","issuer_id","document_id"),
      "fundamental_metrics":("metric_id","issuer_id","document_id"),
      "share_capital_observations":("observation_id","issuer_id",None),
      "corporate_actions":("action_id","issuer_id",None),
      "dividends":("dividend_id","issuer_id",None),
      "ownership_positions":("ownership_id","issuer_id",None),
      "security_rights":("rights_id",None,None),
      "governance_events":("event_id","issuer_id",None),
      "valuation_records":("valuation_id","issuer_id",None),
      "liquidity_assessments":("assessment_id",None,None),
      "factor_scores":("factor_score_id",None,None),
      "research_signals":("signal_id",None,None),
      "portfolio_runs":("portfolio_id",None,None),
      "portfolio_positions":("portfolio_position_id",None,None),
      "portfolio_metrics":("portfolio_metric_id",None,None),
      "shadow_portfolios":("shadow_portfolio_id",None,None),
      "prospective_decision_snapshots":("prospective_snapshot_id",None,None),
      "prospective_security_states":("state_id",None,None),
      "paper_positions":("shadow_portfolio_id",None,None),
    }
    totals=Counter()
    for table,(pk,issuer_col,document_col) in tables.items():
        columns={r[1] for r in repo.connection.execute(f"PRAGMA table_info({table})")}
        if not columns: continue
        for row in repo.connection.execute(f"SELECT * FROM {table}").fetchall():
            issuer_id=row[issuer_col] if issuer_col else None
            if not issuer_id and "security_id" in columns and row["security_id"]:
                found=repo.connection.execute("SELECT issuer_id FROM securities WHERE security_id=?",(row["security_id"],)).fetchone()
                issuer_id=found[0] if found else None
            canonical=None
            if issuer_id:
                found=repo.connection.execute("SELECT canonical_issuer_id FROM issuers WHERE issuer_id=?",(issuer_id,)).fetchone()
                canonical=found[0] if found else None
            assignment=None
            doc_id=row[document_col] if document_col else (row["document_id"] if "document_id" in columns else None)
            if doc_id:
                assignment=repo.connection.execute("SELECT assignment_status,canonical_issuer_id FROM financial_document_identity_assignments WHERE document_id=?",(doc_id,)).fetchone()
            if assignment and (assignment[0]!="VERIFIED" or (canonical and assignment[1]!=canonical)):
                determination="REQUIRES_RECOMPUTATION" if table not in {"financial_documents","financial_raw_values"} else "AMBIGUOUS"
                reason=f"SOURCE_DOCUMENT_IDENTITY_{assignment[0]}"
            elif issuer_id and not canonical:
                determination="AMBIGUOUS"; reason="NO_CANONICAL_ISSUER_MAPPING"
            else:
                determination="CORRECT"; reason="ONE_TO_ONE_CANONICAL_MAPPING_AND_VERIFIED_LINEAGE" if issuer_id or assignment else "NO_ISSUER_BEARING_CONTENT"
            _record(repo,table,row[pk],issuer_id,canonical,determination,reason); totals[determination]+=1
            if determination=="REQUIRES_RECOMPUTATION":
                repo.connection.execute("INSERT OR IGNORE INTO analytical_identity_invalidations VALUES(?,?,?,?,?,?,?)",(str(uuid.uuid4()),table,str(row[pk]),reason,doc_id,utc_now(),None))
    return dict(totals)


def run_identity_hotfix(database):
    with Repository(database) as repo:
        repo.initialize()
        assignments=backfill_document_assignments(repo)
        audit=contamination_audit(repo)
        repo.connection.commit()
        return {
          "issuer_migrations":repo.connection.execute("SELECT count(*) FROM issuer_identity_migrations").fetchone()[0],
          "assignments":assignments,
          "contamination_audit":audit,
          "conflicts":repo.connection.execute("SELECT count(*) FROM identity_resolution_conflicts WHERE status='UNRESOLVED'").fetchone()[0],
        }
