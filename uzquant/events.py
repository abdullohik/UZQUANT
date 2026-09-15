from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .repository import Repository, stable_id, utc_now

EVENT_MODEL_VERSION="event-classification/1.0.0"
CATALYST_MODEL_VERSION="catalyst-relevance/1.0.0"
EVENT_TYPES=("DIVIDEND","PRIVATIZATION","STATE_STAKE_SALE","STRATEGIC_INVESTOR","ACQUISITION","MERGER","CAPITAL_INCREASE","BUYBACK","LARGE_CONTRACT","BORROWING","REFINANCING","MANAGEMENT_CHANGE","AUDITOR_CHANGE","RELATED_PARTY","LEGAL","REGULATORY","PRODUCTION_EXPANSION","ASSET_SALE","RESTRUCTURING","BANKRUPTCY","OTHER")
DIRECTIONS=("STRONG_NEGATIVE","NEGATIVE","NEUTRAL","POSITIVE","STRONG_POSITIVE")


@dataclass(frozen=True)
class EventCandidate:
    issuer_id:str; affected_security_ids:tuple[str,...]; publication_at:str
    effective_date:str|None; event_type:str; summary:str; materiality:str
    direction:str; time_horizon:str; confidence:str; classification_method:str
    source_document_id:str; source_record_type:str; source_record_id:str
    source_url:str; evidence_text:str; canonical_key:str
    model_version:str|None=None; prompt_version:str|None=None


def validate_candidate(c:EventCandidate):
    if c.event_type not in EVENT_TYPES or c.direction not in DIRECTIONS: raise ValueError("invalid taxonomy value")
    if not re.match(r"^\d{4}-\d{2}-\d{2}(T.*)?$",c.publication_at): raise ValueError("publication date/time required")
    if c.classification_method.startswith("LLM") and (not c.model_version or not c.prompt_version): raise ValueError("LLM lineage required")
    if not c.evidence_text or not c.source_url: raise ValueError("evidence and source required")


def store_event(repo:Repository,c:EventCandidate):
    validate_candidate(c); existing=repo.connection.execute("SELECT * FROM research_events WHERE canonical_key=?",(c.canonical_key,)).fetchone()
    event_id=existing[0] if existing else stable_id("research-event",c.canonical_key)
    if not existing:
        repo.connection.execute("INSERT INTO research_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(event_id,c.issuer_id,c.publication_at,c.effective_date,c.event_type,c.summary,c.materiality,c.direction,c.time_horizon,c.confidence,c.classification_method,c.model_version,c.prompt_version,c.canonical_key,utc_now()))
    else:
        incoming={"effective_date":c.effective_date,"event_type":c.event_type,"materiality":c.materiality,"direction":c.direction,"time_horizon":c.time_horizon}
        conflicts={field:{"stored":existing[field],"incoming":value} for field,value in incoming.items() if existing[field]!=value}
        if conflicts:
            payload=json.dumps(conflicts,sort_keys=True); conflict_id=stable_id("event-conflict",f"{event_id}:{c.source_document_id}:{payload}")
            repo.connection.execute("INSERT OR IGNORE INTO research_event_conflicts VALUES(?,?,?,?,?,?)",(conflict_id,event_id,c.source_document_id,payload,"UNRESOLVED",utc_now()))
    for security_id in c.affected_security_ids: repo.connection.execute("INSERT OR IGNORE INTO research_event_securities VALUES(?,?)",(event_id,security_id))
    source_id=stable_id("event-source",f"{event_id}:{c.source_document_id}:{c.source_record_type}:{c.source_record_id}")
    repo.connection.execute("INSERT OR IGNORE INTO research_event_sources VALUES(?,?,?,?,?,?,?,?)",(source_id,event_id,c.source_document_id,c.source_record_type,c.source_record_id,c.source_url,c.publication_at,c.evidence_text))
    return event_id


def classify_with_llm(candidate:EventCandidate,probability:float):
    if not candidate.classification_method.startswith("LLM"): return candidate
    if probability < .75:
        return EventCandidate(**{**candidate.__dict__,"event_type":"OTHER","direction":"NEUTRAL","confidence":"LOW"})
    return candidate


def catalyst_for(event_type,direction,materiality,confidence):
    themes={"PRIVATIZATION":"PRIVATIZATION","STATE_STAKE_SALE":"PRIVATIZATION","STRATEGIC_INVESTOR":"STRATEGIC_INVESTOR","BUYBACK":"BUYBACK","PRODUCTION_EXPANSION":"CAPACITY_EXPANSION","DIVIDEND":"DIVIDEND","REFINANCING":"DEBT_REDUCTION"}
    theme=themes.get(event_type)
    if not theme: return "NONE",None,"LOW","No direct valuation-gap-closing mechanism established from the classified event alone."
    if direction in ("POSITIVE","STRONG_POSITIVE") and confidence=="HIGH": return "DIRECT","80" if materiality=="HIGH" else "70","HIGH",f"High-confidence positive {theme.lower()} event may directly affect a valuation gap; valuation context is still required."
    return "POSSIBLE","40","LOW",f"The event could be relevant to {theme.lower()}, but direction or comparative financial effect is not established."


def event_signal_effect(existing_signal:str,event_direction:str):
    if existing_signal not in ("STRONG_BUY","BUY","ACCUMULATE","WATCH","HOLD","REDUCE","AVOID","LIQUIDITY_TRAP","GOVERNANCE_RISK","DATA_INSUFFICIENT"): raise ValueError("invalid signal")
    if event_direction not in DIRECTIONS: raise ValueError("invalid direction")
    return existing_signal


def _issuer_securities(repo,issuer_id): return tuple(r[0] for r in repo.connection.execute("SELECT security_id FROM securities WHERE issuer_id=? ORDER BY security_id",(issuer_id,)))


def ingest_archived_events(database:Path):
    with Repository(database) as repo:
        repo.initialize(); candidates=[]
        # One issuer disclosure can affect multiple explicitly identified share classes.
        groups={}
        for r in repo.connection.execute("SELECT d.*,i.legal_name FROM dividends d JOIN issuers i USING(issuer_id) ORDER BY announcement_date,dividend_id"):
            key=(r["issuer_id"],r["source_document_id"],r["announcement_date"]); groups.setdefault(key,[]).append(r)
        for (issuer,doc,pub),rows in groups.items():
            securities=tuple(sorted({r["security_id"] for r in rows})); amounts="; ".join(f"{r['dividend_per_share']} {r['currency']} per share ({r['security_id']})" for r in rows)
            candidates.append(EventCandidate(issuer,securities,pub,rows[0]["payment_start_date"],"DIVIDEND",f"Class-specific dividend disclosure: {amounts}","UNKNOWN","NEUTRAL","SHORT_TERM","HIGH","DETERMINISTIC_DIVIDEND_RECORD",doc,"dividends","|".join(sorted(r["dividend_id"] for r in rows)),rows[0]["source_url"],amounts,f"{issuer}:DIVIDEND:{pub}:{doc}"))
        for r in repo.connection.execute("SELECT * FROM corporate_actions ORDER BY announcement_date"):
            event_type="CAPITAL_INCREASE" if r["action_type"]=="NEW_ISSUANCE" else "OTHER"; securities=(r["security_id"],) if r["security_id"] else _issuer_securities(repo,r["issuer_id"])
            candidates.append(EventCandidate(r["issuer_id"],securities,r["announcement_date"],r["effective_date"],event_type,"Registered new share issuance; purpose and financial effect are not inferred.","MEDIUM","NEUTRAL","MEDIUM_TERM",r["confidence"],"DETERMINISTIC_CORPORATE_ACTION_MAP",r["source_document_id"],"corporate_actions",r["action_id"],r["source_url"],r["details_json"],f"{r['issuer_id']}:{event_type}:{r['effective_date'] or r['announcement_date']}"))
        for r in repo.connection.execute("SELECT * FROM governance_events ORDER BY disclosure_date"):
            # The issuance has already been normalized from the authoritative corporate-action record.
            if r["event_type"]=="DILUTION": continue
            event_type="MANAGEMENT_CHANGE" if r["event_type"]=="MANAGEMENT_CHANGE" else "OTHER"; securities=(r["security_id"],) if r["security_id"] else _issuer_securities(repo,r["issuer_id"])
            summary="Management appointments and terminations disclosed." if event_type=="MANAGEMENT_CHANGE" else "Shareholder-meeting decision disclosed; economic direction is not inferred."
            candidates.append(EventCandidate(r["issuer_id"],securities,r["disclosure_date"],r["event_date"],event_type,summary,"MEDIUM" if event_type=="MANAGEMENT_CHANGE" else "LOW","NEUTRAL","MEDIUM_TERM" if event_type=="MANAGEMENT_CHANGE" else "SHORT_TERM",r["confidence"],r["classification_method"],r["source_document_id"],"governance_events",r["event_id"],r["source_url"],r["evidence_text"],f"{r['issuer_id']}:{event_type}:{r['event_date']}"))
        event_ids=[]
        for candidate in candidates:
            eid=store_event(repo,candidate); event_ids.append(eid); relevance,score,confidence,rationale=catalyst_for(candidate.event_type,candidate.direction,candidate.materiality,candidate.confidence)
            catalyst_id=stable_id("catalyst",f"{eid}:{CATALYST_MODEL_VERSION}"); theme={"DIVIDEND":"DIVIDEND","CAPITAL_INCREASE":"CAPACITY_EXPANSION"}.get(candidate.event_type) if relevance!="NONE" else None
            repo.connection.execute("INSERT OR IGNORE INTO catalyst_assessments VALUES(?,?,?,?,?,?,?,?,?,?)",(catalyst_id,eid,candidate.materiality,theme,relevance,score,confidence,rationale,CATALYST_MODEL_VERSION,utc_now()))
        repo.connection.commit(); return {"events":len(set(event_ids)),"source_links":repo.connection.execute("SELECT count(*) FROM research_event_sources").fetchone()[0],"catalysts":repo.connection.execute("SELECT count(*) FROM catalyst_assessments").fetchone()[0]}


def events_as_of(repo:Repository,issuer_id:str,as_of:str):
    return repo.connection.execute("SELECT * FROM research_events WHERE issuer_id=? AND publication_at<=? ORDER BY publication_at,effective_date",(issuer_id,as_of)).fetchall()
