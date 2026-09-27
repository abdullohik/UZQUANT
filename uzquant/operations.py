from __future__ import annotations

import json, time, uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from .repository import Repository, utc_now

VERSION="continuous-operations/1.0.0"
DETECTOR_VERSION="research-anomalies/1.0.0"
ALERT_TYPES=("NEW_MATERIAL_DISCLOSURE","NEW_FINANCIAL_REPORT","DIVIDEND_ANNOUNCEMENT","CAPITAL_CHANGE","OWNERSHIP_EVENT","GOVERNANCE_EVENT","VALUATION_STATE_CHANGE","SIGNAL_STATE_CHANGE","LIQUIDITY_DETERIORATION","DATA_QUALITY_DETERIORATION","PIPELINE_FAILED","PIPELINE_STALE","PIPELINE_DEGRADED","SOURCE_SCHEMA_CHANGE","ANOMALY")


@dataclass(frozen=True)
class Pipeline:
    name:str; source:str; handler_group:str; interval_seconds:int; dependencies:tuple[str,...]=()


PIPELINES=(
 Pipeline("security_master","RSE","security",86400), Pipeline("market_data","RSE","market",21600,("security_master",)),
 Pipeline("financial_documents","Openinfo","financial",86400,("security_master",)),
 Pipeline("corporate_actions","Openinfo/RSE","corporate",86400,("security_master",)), Pipeline("dividends","Openinfo/RSE","corporate",86400,("security_master",)),
 Pipeline("ownership","Openinfo/RSE","corporate",604800,("security_master",)), Pipeline("security_rights","Openinfo/RSE","corporate",604800,("security_master",)),
 Pipeline("events","Openinfo","events",21600,("security_master",)), Pipeline("macro","CBU","macro",86400),
 Pipeline("financial_normalization","internal","normalize",86400,("financial_documents",)), Pipeline("fundamentals","internal","fundamentals",86400,("financial_normalization",)),
 Pipeline("valuation","internal","valuation",86400,("fundamentals","security_rights")), Pipeline("liquidity","internal","liquidity",21600,("market_data",)),
 Pipeline("factors","internal","signals",21600,("valuation","liquidity","fundamentals")), Pipeline("confidence","internal","signals",21600,("factors",)),
 Pipeline("risk_gates","internal","signals",21600,("confidence",)), Pipeline("signals","internal","signals",21600,("risk_gates",)),
)


def _dt(value): return datetime.fromisoformat(value.replace("Z","+00:00")) if value else None


def register_pipelines(repo:Repository):
    now=utc_now()
    for p in PIPELINES:
        repo.connection.execute("INSERT INTO pipeline_definitions VALUES(?,?,?,?,?,?,1,?) ON CONFLICT(pipeline) DO UPDATE SET source=excluded.source,handler_group=excluded.handler_group,refresh_interval_seconds=excluded.refresh_interval_seconds,dependencies_json=excluded.dependencies_json,data_version=excluded.data_version,enabled=1",(p.name,p.source,p.handler_group,p.interval_seconds,json.dumps(p.dependencies),VERSION,now))
        repo.connection.execute("INSERT OR IGNORE INTO pipeline_health VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(p.name,"STALE",None,None,None,now,"NEVER_RUN","NOT_ATTEMPTED",p.source,VERSION,json.dumps([]),now))
    for alert_type in ALERT_TYPES:
        repo.connection.execute("INSERT OR IGNORE INTO alert_rules VALUES(?,1,'INFO',?)",(alert_type,now))
    repo.connection.commit()


def record_alert(repo:Repository,alert_type,severity,entity_type,entity_id,title,message,evidence=None,source_ids=(),dedupe_key=None):
    rule=repo.connection.execute("SELECT enabled,minimum_severity FROM alert_rules WHERE alert_type=?",(alert_type,)).fetchone()
    ranks={"INFO":0,"WARNING":1,"HIGH":2,"CRITICAL":3}
    if rule and (not rule[0] or ranks.get(severity,0)<ranks.get(rule[1],0)): return None
    key=dedupe_key or f"{alert_type}:{entity_type}:{entity_id}:{title}"
    aid=str(uuid.uuid4()); before=repo.connection.total_changes
    repo.connection.execute("INSERT OR IGNORE INTO research_alerts VALUES(?,?,?,?,?,?,?,?,?,'OPEN',?,?,NULL)",(aid,alert_type,severity,entity_type,entity_id,title,message,json.dumps(evidence or {},sort_keys=True,default=str),json.dumps(list(source_ids)),key,utc_now()))
    return aid if repo.connection.total_changes>before else None


def record_anomaly(repo:Repository,kind,severity,entity_type,entity_id,evidence,source_ids=(),dedupe_key=None):
    key=dedupe_key or f"{kind}:{entity_type}:{entity_id}:{json.dumps(evidence,sort_keys=True,default=str)}"
    aid=str(uuid.uuid4()); before=repo.connection.total_changes
    repo.connection.execute("INSERT OR IGNORE INTO research_anomalies VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(aid,kind,severity,entity_type,entity_id,utc_now(),json.dumps(evidence,sort_keys=True,default=str),json.dumps(list(source_ids)),"OPEN",DETECTOR_VERSION,key,utc_now()))
    if repo.connection.total_changes>before: record_alert(repo,"ANOMALY","WARNING",entity_type,entity_id,kind,f"Research anomaly requires investigation: {kind}",evidence,source_ids,"alert:"+key)
    return aid if repo.connection.total_changes>before else None


def numeric_jump(previous,current,multiple=Decimal("10")):
    previous,current=Decimal(str(previous)),Decimal(str(current))
    if previous==0:return current!=0
    return abs(current/previous)>=multiple or abs(previous/current)>=multiple if current!=0 else True


class SourceSchemaChanged(ValueError): pass


def detect_source_schema(expected:set[str],observed:set[str]):
    missing=sorted(expected-observed); unexpected=sorted(observed-expected)
    classification="BREAKING_SCHEMA_CHANGE" if missing else "COMPATIBLE_SCHEMA_CHANGE" if unexpected else "COSMETIC_CHANGE"
    return {"status":"FAILED" if missing else "HEALTHY","classification":classification,"missing":missing,"unexpected":unexpected}


def record_source_schema_check(repo:Repository,pipeline:str,expected:set[str],observed:set[str]):
    result=detect_source_schema(expected,observed)
    if result["status"]=="FAILED":
        record_alert(repo,"SOURCE_SCHEMA_CHANGE","CRITICAL","PIPELINE",pipeline,"Material source schema change",f"Missing expected fields: {', '.join(result['missing'])}",result,dedupe_key=f"schema:{pipeline}:{','.join(result['missing'])}")
    return result


def enforce_source_schema(repo:Repository,pipeline:str,source_id:str,parser_version:str,raw_document_id:str|None,expected:set[str],observed:set[str]):
    result=detect_source_schema(expected,observed); now=utc_now()
    contract_id=f"{pipeline}:{source_id}:{parser_version}"
    repo.connection.execute("INSERT OR IGNORE INTO source_schema_contracts VALUES(?,?,?,?,?,?)",(contract_id,pipeline,source_id,parser_version,json.dumps({"required":sorted(expected)},sort_keys=True),now))
    repo.connection.execute("INSERT INTO source_schema_checks VALUES(?,?,?,?,?,?,?)",(str(uuid.uuid4()),contract_id,raw_document_id,result["classification"],json.dumps(sorted(observed)),json.dumps(result,sort_keys=True),now))
    if result["classification"]=="BREAKING_SCHEMA_CHANGE":
        record_anomaly(repo,"SOURCE_SCHEMA_CHANGED","CRITICAL","PIPELINE",pipeline,result,(raw_document_id,) if raw_document_id else (),f"schema:{pipeline}:{raw_document_id}:{','.join(result['missing'])}")
        record_alert(repo,"SOURCE_SCHEMA_CHANGE","CRITICAL","PIPELINE",pipeline,"Breaking source schema change",f"Missing required fields: {', '.join(result['missing'])}",result,(raw_document_id,) if raw_document_id else (),f"schema-alert:{pipeline}:{raw_document_id}:{','.join(result['missing'])}")
        repo.connection.execute("UPDATE pipeline_health SET status='FAILED',latest_error='SOURCE_SCHEMA_CHANGED',retry_state='SCHEMA_BLOCKED',updated_at=? WHERE pipeline=?",(now,pipeline))
        # Forensic source evidence must survive the caller's rollback of partial
        # domain writes.  Ingestion boundaries call this before producing records.
        repo.connection.commit()
        raise SourceSchemaChanged(f"SOURCE_SCHEMA_CHANGED:{pipeline}:{','.join(result['missing'])}")
    return result


def signal_transition(old_state,new_state): return old_state!=new_state


def detect_production_anomalies(database:Path):
    created=0
    with Repository(database) as repo:
        repo.initialize(); register_pipelines(repo); c=repo.connection
        for sid in [r[0] for r in c.execute("SELECT DISTINCT security_id FROM market_observations")]:
            rows=c.execute("SELECT observation_id,trade_date,coalesce(last,close,individual_trade_price),share_volume FROM market_observations WHERE security_id=? AND series_type='RAW_OBSERVED' AND observation_status='TRADE_REPORTED' ORDER BY trade_date",(sid,)).fetchall()
            for a,b in zip(rows,rows[1:]):
                if a[2] and b[2] and numeric_jump(a[2],b[2],Decimal("3")): created+=bool(record_anomaly(repo,"EXTREME_DAILY_MOVE","HIGH","SECURITY",sid,{"previous":a[2],"current":b[2],"date":b[1]},(a[0],b[0]),f"price:{sid}:{b[1]}"))
                if a[3] and b[3] and numeric_jump(a[3],b[3],Decimal("10")): created+=bool(record_anomaly(repo,"UNUSUAL_VOLUME","MEDIUM","SECURITY",sid,{"previous":a[3],"current":b[3],"date":b[1]},(a[0],b[0]),f"volume:{sid}:{b[1]}"))
        for sid in [r[0] for r in c.execute("SELECT DISTINCT security_id FROM share_capital_observations WHERE security_id IS NOT NULL")]:
            rows=c.execute("SELECT observation_id,effective_date,class_shares_outstanding FROM share_capital_observations WHERE security_id=? AND verification_status='VERIFIED' ORDER BY effective_date",(sid,)).fetchall()
            for a,b in zip(rows,rows[1:]):
                if a[2] and b[2] and Decimal(b[2])!=Decimal(a[2]): created+=bool(record_anomaly(repo,"SHARES_OUTSTANDING_CHANGE","HIGH","SECURITY",sid,{"previous":a[2],"current":b[2],"effective_date":b[1]},(a[0],b[0]),f"shares:{sid}:{b[1]}"))
        repo.connection.commit()
    return created


def capture_signal_transitions(database:Path):
    created=0
    with Repository(database) as repo:
        repo.initialize(); c=repo.connection
        for sid in [r[0] for r in c.execute("SELECT DISTINCT security_id FROM research_signals")]:
            signals=c.execute("SELECT * FROM research_signals WHERE security_id=? ORDER BY generated_at",(sid,)).fetchall()
            for old,new in zip(signals,signals[1:]):
                exists=c.execute("SELECT 1 FROM signal_state_transitions WHERE new_signal_id=?",(new["signal_id"],)).fetchone()
                if exists or not signal_transition(old["signal_state"],new["signal_state"]):continue
                driver={"old_gates":json.loads(old["triggered_gates_json"]),"new_gates":json.loads(new["triggered_gates_json"]),"old_confidence":old["confidence"],"new_confidence":new["confidence"]}
                c.execute("INSERT INTO signal_state_transitions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),sid,old["signal_id"],new["signal_id"],old["signal_state"],new["signal_state"],json.dumps(driver,sort_keys=True),new["generated_at"],new["data_snapshot_id"],new["model_version"],new["scoring_version"],new["valuation_version"],new["liquidity_version"]))
                record_alert(repo,"SIGNAL_STATE_CHANGE","HIGH","SECURITY",sid,"Signal state changed",f"{old['signal_state']} → {new['signal_state']}",driver,(old["signal_id"],new["signal_id"]),f"signal:{new['signal_id']}");created+=1
        c.commit()
    return created


class Scheduler:
    def __init__(self,database:Path,runners:dict[str,callable],max_attempts=3,sleeper=time.sleep): self.database=database;self.runners=runners;self.max_attempts=max_attempts;self.sleeper=sleeper
    def run_due(self,force=False,selected=None,now=None):
        now=now or datetime.now(timezone.utc); results=[]
        with Repository(self.database) as repo:
            repo.initialize();register_pipelines(repo); definitions={p.name:p for p in PIPELINES}; names=[n for n in definitions if not selected or n in selected]; groups={}
            for name in names:
                p=definitions[name]; health=repo.connection.execute("SELECT expected_refresh_at FROM pipeline_health WHERE pipeline=?",(name,)).fetchone()
                if force or not health or not health[0] or _dt(health[0])<=now: groups.setdefault(p.handler_group,[]).append(p)
            for group,pipelines in groups.items():
                same_group={x.name for x in pipelines}
                dependency_states={d:(repo.connection.execute("SELECT status FROM pipeline_health WHERE pipeline=?",(d,)).fetchone() or ["FAILED"])[0] for p in pipelines for d in p.dependencies if d not in same_group}
                blocked=[d for d,status in dependency_states.items() if status in {"FAILED","STALE"}]
                degraded=[d for d,status in dependency_states.items() if status=="DEGRADED"]
                if blocked: outcome={"status":"STALE","attempted":0,"succeeded":0,"failed":0,"error":"UPSTREAM_STALE:"+','.join(sorted(set(blocked))),"retry_state":"BLOCKED"}
                else:
                    runner=self.runners.get(group); outcome=None
                    if not runner: outcome={"status":"FAILED","attempted":0,"succeeded":0,"failed":1,"error":"NO_RUNNER","retry_state":"EXHAUSTED"}
                    for attempt in range(1,self.max_attempts+1) if runner else ():
                        try:
                            raw=runner(); attempted=int(raw.get("attempted",raw.get("records",0))); failed=int(raw.get("failed",raw.get("errors",0))); succeeded=int(raw.get("succeeded",max(0,attempted-failed))); outcome={"status":"HEALTHY" if failed==0 else "DEGRADED","attempted":attempted,"succeeded":succeeded,"failed":failed,"error":raw.get("error"),"retry_state":"NOT_NEEDED" if attempt==1 else f"SUCCEEDED_ATTEMPT_{attempt}"};break
                        except Exception as exc:
                            outcome={"status":"FAILED","attempted":0,"succeeded":0,"failed":1,"error":f"{type(exc).__name__}: {exc}","retry_state":f"ATTEMPT_{attempt}_FAILED"}
                            if attempt<self.max_attempts:self.sleeper(min(2**(attempt-1),8))
                    if degraded and outcome and outcome["status"]=="HEALTHY":
                        outcome["status"]="DEGRADED"; outcome["error"]="UPSTREAM_DEGRADED:"+','.join(sorted(degraded))
                for p in pipelines:
                    started=now.isoformat();finished=utc_now();expected=(now+timedelta(seconds=p.interval_seconds)).isoformat();run_id=str(uuid.uuid4())
                    repo.connection.execute("INSERT INTO scheduled_pipeline_runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(run_id,p.name,started,finished,outcome["status"],p.source,outcome["attempted"],outcome["succeeded"],outcome["failed"],outcome["error"],outcome["retry_state"],VERSION,expected,json.dumps({"blocked":blocked,"degraded":degraded})))
                    last_success=finished if outcome["status"] in {"HEALTHY","DEGRADED"} else None
                    downstream=[x.name for x in PIPELINES if p.name in x.dependencies]
                    repo.connection.execute("UPDATE pipeline_health SET status=?,last_attempt_at=?,last_success_at=coalesce(?,last_success_at),expected_refresh_at=?,stale_since=?,latest_error=?,retry_state=?,source=?,data_version=?,affected_downstream_json=?,updated_at=? WHERE pipeline=?",(outcome["status"],finished,last_success,expected,started if outcome["status"]=="STALE" else None,outcome["error"],outcome["retry_state"],p.source,VERSION,json.dumps(downstream),finished,p.name))
                    if outcome["status"] in {"FAILED","STALE","DEGRADED"}: record_alert(repo,"PIPELINE_"+outcome["status"],"CRITICAL" if outcome["status"]=="FAILED" else "WARNING","PIPELINE",p.name,f"{p.name} is {outcome['status']}",outcome["error"] or outcome["status"],{"downstream":downstream},(),f"pipeline:{p.name}:{outcome['status']}:{started[:13]}")
                    else:
                        repo.connection.execute("UPDATE research_alerts SET status='RESOLVED',resolved_at=? WHERE entity_type='PIPELINE' AND entity_id=? AND status='OPEN' AND alert_type IN ('PIPELINE_FAILED','PIPELINE_STALE','PIPELINE_DEGRADED')",(finished,p.name))
                    results.append({"run_id":run_id,"pipeline":p.name,**outcome})
                repo.connection.commit()
            repo.connection.commit()
        return results


def production_runners(settings):
    from .corporate_intelligence import ingest_corporate_intelligence
    from .events import ingest_archived_events
    from .financial_documents import ingest_financial_documents
    from .fundamental_metrics import calculate_all
    from .liquidity import run_liquidity_assessments
    from .macro import ingest_macro
    from .market_data import ingest_market_data
    from .remediation_c import ingest_financial_attachments
    from .scoring import score_real_universe
    from .security_master import ingest_security_master
    from .valuation import run_real_validation
    def wrap(function,*args):
        result=function(*args)
        if isinstance(result,list): return {"attempted":len(result),"succeeded":len(result),"failed":0}
        if isinstance(result,tuple): return {"attempted":len(result[0]),"succeeded":len(result[0]),"failed":0}
        preferred=("records_processed","observations_processed","securities_requested","documents","cases","attachments","events")
        attempted=next((result[key] for key in preferred if key in result),None)
        if attempted is None:
            count_keys=("actions","dividends","ownership","rights","catalysts","regimes","scaled_observations","bank_observations")
            attempted=sum(int(result.get(key,0) or 0) for key in count_keys)
        errors=result.get("errors",result.get("source_errors",0)); failed=len(errors) if isinstance(errors,(list,tuple,dict,set)) else int(errors or 0)
        return {"attempted":int(attempted or 0),"succeeded":max(0,int(attempted or 0)-failed),"failed":failed}
    return {
        "security":lambda:wrap(ingest_security_master,settings), "market":lambda:wrap(ingest_market_data,settings),
        "financial":lambda:wrap(ingest_financial_documents,settings), "corporate":lambda:wrap(ingest_corporate_intelligence,settings),
        "events":lambda:wrap(ingest_archived_events,settings.database_path), "macro":lambda:wrap(ingest_macro,settings),
        "normalize":lambda:wrap(ingest_financial_attachments,settings), "fundamentals":lambda:wrap(calculate_all,settings.database_path),
        "valuation":lambda:wrap(run_real_validation,settings.database_path), "liquidity":lambda:wrap(run_liquidity_assessments,settings.database_path),
        "signals":lambda:wrap(score_real_universe,settings.database_path),
    }
