from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date,datetime,timezone

from .repository import Repository,utc_now

RESOLVED="RESOLVED"
IDENTITY_UNRESOLVED="IDENTITY_UNRESOLVED"
IDENTITY_CONFLICT="IDENTITY_CONFLICT"
IDENTIFIER_OUT_OF_RANGE="IDENTIFIER_OUT_OF_RANGE"


@dataclass(frozen=True)
class Resolution:
    status:str
    security_id:str|None=None
    issuer_id:str|None=None
    canonical_issuer_id:str|None=None
    evidence_ids:tuple[str,...]=()
    reason:str|None=None


def create_opaque_issuer(repo:Repository,legal_name:str,created_at:str,source_id:str,source_document_id:str|None=None):
    issuer_id=str(uuid.uuid4()); canonical=str(uuid.uuid4())
    repo.connection.execute("INSERT INTO canonical_issuers VALUES(?,'ACTIVE',?)",(canonical,created_at))
    repo.connection.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at,canonical_issuer_id) VALUES(?,?,?, ?,?)",(issuer_id,legal_name,"OPAQUE_INTERNAL_ID_UNRESOLVED_SOURCE_LINK",created_at,canonical))
    repo.connection.execute("INSERT INTO issuer_identity_migrations VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),issuer_id,canonical,"CREATED_OPAQUE_NOT_NAME_DERIVED",json.dumps([source_document_id] if source_document_id else []),created_at))
    repo.connection.execute("INSERT INTO effective_identifier_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),"ISSUER",canonical,None,"LEGAL_NAME",legal_name,created_at[:10],None,created_at,source_id,source_document_id,"LOW","CANDIDATE"))
    return issuer_id,canonical


def _at(value): return value.isoformat() if isinstance(value,(date,datetime)) else str(value)


def resolve_security_identifier(repo:Repository,identifier_type:str,value:str,observation_date,knowledge_timestamp=None)->Resolution:
    day=_at(observation_date)[:10]; known=_at(knowledge_timestamp or datetime.now(timezone.utc))
    rows=repo.connection.execute("""SELECT e.evidence_id,e.security_id,s.issuer_id,i.canonical_issuer_id,e.valid_from,e.valid_to
      FROM effective_identifier_evidence e JOIN securities s USING(security_id) JOIN issuers i USING(issuer_id)
      WHERE e.entity_type='SECURITY' AND e.identifier_type=? AND e.identifier_value=?
        AND e.evidence_status='VERIFIED' AND e.known_at<=?
        AND (e.valid_from IS NULL OR e.valid_from<=?) AND (e.valid_to IS NULL OR e.valid_to>?)
      ORDER BY e.known_at DESC""",(identifier_type,value,known,day,day)).fetchall()
    unique={r[1]:r for r in rows}
    if len(unique)==1:
        row=next(iter(unique.values())); return Resolution(RESOLVED,row[1],row[2],row[3],tuple(r[0] for r in rows))
    if len(unique)>1:return Resolution(IDENTITY_CONFLICT,evidence_ids=tuple(r[0] for r in rows),reason="MULTIPLE_EFFECTIVE_SECURITY_MAPPINGS")
    any_rows=repo.connection.execute("SELECT 1 FROM effective_identifier_evidence WHERE entity_type='SECURITY' AND identifier_type=? AND identifier_value=? AND evidence_status='VERIFIED' LIMIT 1",(identifier_type,value)).fetchone()
    return Resolution(IDENTIFIER_OUT_OF_RANGE if any_rows else IDENTITY_UNRESOLVED,reason="NO_IDENTIFIER_MAPPING_VALID_AT_OBSERVATION_DATE")


def resolve_security_pair(repo:Repository,ticker:str,isin:str,observation_date,knowledge_timestamp=None)->Resolution:
    ticker_result=resolve_security_identifier(repo,"TICKER",ticker,observation_date,knowledge_timestamp)
    isin_result=resolve_security_identifier(repo,"ISIN",isin,observation_date,knowledge_timestamp)
    if ticker_result.status!=RESOLVED or isin_result.status!=RESOLVED:
        status=IDENTITY_CONFLICT if IDENTITY_CONFLICT in {ticker_result.status,isin_result.status} else IDENTIFIER_OUT_OF_RANGE if IDENTIFIER_OUT_OF_RANGE in {ticker_result.status,isin_result.status} else IDENTITY_UNRESOLVED
        return Resolution(status,reason=f"TICKER:{ticker_result.status};ISIN:{isin_result.status}")
    if ticker_result.security_id!=isin_result.security_id:
        return Resolution(IDENTITY_CONFLICT,evidence_ids=ticker_result.evidence_ids+isin_result.evidence_ids,reason="TICKER_ISIN_DISAGREEMENT")
    return Resolution(RESOLVED,ticker_result.security_id,ticker_result.issuer_id,ticker_result.canonical_issuer_id,ticker_result.evidence_ids+isin_result.evidence_ids)


def record_conflict(repo:Repository,kind:str,identifier_type:str|None,value:str|None,observation_date,candidates,evidence):
    conflict_id=str(uuid.uuid4())
    repo.connection.execute("INSERT INTO identity_resolution_conflicts VALUES(?,?,?,?,?,?,?,'UNRESOLVED',?)",(conflict_id,kind,identifier_type,value,_at(observation_date)[:10],json.dumps(list(candidates)),json.dumps(evidence,sort_keys=True,default=str),utc_now()))
    return conflict_id
