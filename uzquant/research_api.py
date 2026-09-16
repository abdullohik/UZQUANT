from __future__ import annotations

import json
from pathlib import Path

from .repository import Repository

API_VERSION = "research-api/1.0.0"


def _decode(row):
    if row is None:
        return None
    value = dict(row)
    for key, item in list(value.items()):
        if key.endswith("_json") and isinstance(item, str):
            try:
                value[key] = json.loads(item)
            except json.JSONDecodeError:
                pass
    return value


def _rows(connection, sql, args=()):
    return [_decode(row) for row in connection.execute(sql, args).fetchall()]


def _row(connection, sql, args=()):
    return _decode(connection.execute(sql, args).fetchone())


def grounded_report(detail: dict) -> dict:
    identity = detail["identity"]
    signal = detail.get("signal") or {}
    valuation = detail.get("valuation", [])
    liquidity = detail.get("liquidity") or {}
    warnings = detail.get("warnings", [])
    sections = {
        "Executive Research Summary": f"{identity['ticker']} is currently classified {signal.get('signal_state', 'DATA_INSUFFICIENT')}. "
        f"Confidence is {signal.get('confidence', 'Unavailable')}; valuation status is {detail['valuation_status']}.",
        "Security / Share Class": f"{identity['ticker']} — {identity['security_class_code']} security of {identity['legal_name']}.",
        "Investment State": signal.get("signal_state", "DATA_INSUFFICIENT"),
        "Business / Sector": identity.get("sector") or "Unavailable",
        "Financials": f"{len(detail.get('financial_documents', []))} verified documents and {len(detail.get('fundamentals', []))} available metric records.",
        "Valuation": f"{detail['valuation_status']}; {len(valuation)} method records are exposed with exact rejection reasons.",
        "Liquidity & Capacity": f"{liquidity.get('liquidity_state', 'Unavailable')}; capacity remains {detail.get('capacity', {}).get('status', 'Unavailable') if detail.get('capacity') else 'Unavailable'}.",
        "Ownership": f"{len(detail.get('ownership', []))} disclosed ownership records.",
        "Share Rights": (detail.get("rights_assessment") or {}).get("classification", "Unavailable"),
        "Governance": f"{len(detail.get('governance', []))} source-linked governance events.",
        "Catalysts": f"{len(detail.get('events', []))} structured research events.",
        "Risks": ", ".join(signal.get("triggered_gates_json", [])) or "No stored gate beyond missing-evidence controls.",
        "Data Quality": str(detail.get("data_quality") or "Unavailable"),
        "Confidence": signal.get("confidence", "Unavailable"),
        "Thesis Invalidators": "No executable thesis is asserted while required evidence or validation is unavailable.",
        "Missing Evidence": ", ".join(warnings) or "None recorded.",
    }
    return {"status": "GROUNDED", "api_version": API_VERSION, "security_id": identity["security_id"], "sections": sections,
            "source_record_ids": detail.get("source_record_ids", [])}


class ResearchService:
    def __init__(self, database: Path):
        self.database = database

    def _identity(self, connection, ticker: str):
        return _row(connection, """
            SELECT s.security_id,s.issuer_id,s.security_class_code,s.security_type,s.nominal_value,s.currency,
                   i.legal_name,i.short_name,i.sector,i.industry,h.identifier_value ticker,h.known_at ticker_known_at
            FROM identifier_history h JOIN securities s ON s.security_id=h.security_id JOIN issuers i ON i.issuer_id=s.issuer_id
            WHERE h.identifier_type='TICKER' AND upper(h.identifier_value)=upper(?) ORDER BY h.known_at DESC LIMIT 1
        """, (ticker,))

    def universe(self, filters: dict | None = None):
        filters = filters or {}
        with Repository(self.database) as repo:
            repo.initialize()
            identities = _rows(repo.connection, """
                WITH latest AS (SELECT security_id,identifier_value,known_at,ROW_NUMBER() OVER(PARTITION BY security_id ORDER BY known_at DESC) n
                FROM identifier_history WHERE identifier_type='TICKER')
                SELECT s.security_id,s.issuer_id,l.identifier_value ticker,s.security_class_code,i.legal_name,i.sector
                FROM securities s JOIN issuers i USING(issuer_id) JOIN latest l ON l.security_id=s.security_id AND l.n=1 ORDER BY l.identifier_value
            """)
            result=[]
            for item in identities:
                sid=item["security_id"]
                market=_row(repo.connection,"SELECT trade_date,coalesce(last,close,individual_trade_price) price,currency,observation_status,source_id,document_id,last_seen_at FROM market_observations WHERE security_id=? AND series_type='RAW_OBSERVED' ORDER BY trade_date DESC LIMIT 1",(sid,))
                signal=_row(repo.connection,"SELECT * FROM research_signals WHERE security_id=? ORDER BY generated_at DESC LIMIT 1",(sid,))
                liquidity=_row(repo.connection,"SELECT liquidity_state,liquidity_confidence,as_of_date FROM liquidity_assessments WHERE security_id=? ORDER BY created_at DESC LIMIT 1",(sid,))
                valuation=_row(repo.connection,"SELECT status,valuation_date FROM valuation_records WHERE security_id=? ORDER BY (status='AVAILABLE') DESC,created_at DESC LIMIT 1",(sid,))
                factors=(signal or {}).get("factor_scores_json",{})
                result.append({**item,"market":market,"valuation_status":valuation["status"] if valuation else "VALUATION_INSUFFICIENT",
                    "quality":factors.get("Quality"),"growth":factors.get("Growth"),"data_quality":factors.get("Data Quality"),
                    "confidence":signal.get("confidence") if signal else None,"signal":signal.get("signal_state") if signal else "DATA_INSUFFICIENT",
                    "risk_gates":signal.get("triggered_gates_json",[]) if signal else [],"liquidity":liquidity})
            def keep(x):
                return (not filters.get("sector") or x.get("sector")==filters["sector"]) and (not filters.get("signal") or x["signal"]==filters["signal"]) and (not filters.get("liquidity") or (x.get("liquidity") or {}).get("liquidity_state")==filters["liquidity"])
            return {"api_version":API_VERSION,"status":"OK","count":sum(keep(x) for x in result),"securities":[x for x in result if keep(x)]}

    def security(self, ticker: str):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection; identity=self._identity(c,ticker)
            if not identity: raise KeyError(ticker)
            sid,iid=identity["security_id"],identity["issuer_id"]
            market=_rows(c,"SELECT * FROM market_observations WHERE security_id=? AND series_type='RAW_OBSERVED' ORDER BY trade_date DESC LIMIT 100",(sid,))
            quality=_row(c,"SELECT * FROM market_quality_metrics WHERE security_id=? ORDER BY as_of_date DESC,created_at DESC LIMIT 1",(sid,))
            flags=_rows(c,"SELECT * FROM market_quality_flags WHERE security_id=? ORDER BY created_at DESC",(sid,))
            documents=_rows(c,"SELECT d.*,c.validation_status,c.reason entity_check_reason FROM financial_documents d JOIN financial_document_entity_checks c ON c.document_id=d.document_id JOIN financial_document_identity_assignments a ON a.document_id=d.document_id WHERE d.issuer_id=? AND c.validation_status='MATCHED' AND a.assignment_status='VERIFIED' ORDER BY d.period_end DESC",(iid,))
            financials=_rows(c,"SELECT o.* FROM financial_observations o JOIN financial_document_entity_checks c ON c.document_id=o.document_id AND c.validation_status='MATCHED' JOIN financial_document_identity_assignments a ON a.document_id=o.document_id AND a.assignment_status='VERIFIED' WHERE o.issuer_id=? ORDER BY o.period_end DESC,o.canonical_concept LIMIT 300",(iid,))
            metrics=_rows(c,"SELECT * FROM fundamental_metrics WHERE issuer_id=? AND status='AVAILABLE' ORDER BY period_end DESC,metric_name",(iid,))
            valuations=_rows(c,"SELECT * FROM valuation_records WHERE security_id=? ORDER BY valuation_date DESC,method",(sid,))
            attempts=_rows(c,"SELECT * FROM valuation_model_attempts WHERE security_id=? ORDER BY valuation_date DESC,model_name",(sid,))
            assumptions=_rows(c,"SELECT * FROM valuation_assumption_inputs WHERE security_id=? OR security_id IS NULL ORDER BY as_of_date DESC,method,input_name,scenario",(sid,))
            liquidity=_row(c,"SELECT * FROM liquidity_assessments WHERE security_id=? ORDER BY created_at DESC LIMIT 1",(sid,))
            capacity=_row(c,"SELECT * FROM position_sizing_records WHERE security_id=? ORDER BY created_at DESC LIMIT 1",(sid,))
            ownership=_rows(c,"SELECT * FROM ownership_positions WHERE issuer_id=? AND (security_id=? OR security_id IS NULL) ORDER BY disclosure_date DESC",(iid,sid))
            ownership_metrics=_rows(c,"SELECT * FROM ownership_metrics WHERE issuer_id=? ORDER BY as_of_date DESC",(iid,))
            rights=_rows(c,"SELECT * FROM security_rights WHERE security_id=? ORDER BY disclosure_date DESC",(sid,))
            rights_assessment=_row(c,"SELECT * FROM security_rights_assessments WHERE security_id=? ORDER BY as_of_date DESC LIMIT 1",(sid,))
            governance=_rows(c,"SELECT * FROM governance_events WHERE issuer_id=? AND (security_id=? OR security_id IS NULL) ORDER BY disclosure_date DESC",(iid,sid))
            actions=_rows(c,"SELECT * FROM corporate_actions WHERE issuer_id=? AND (security_id=? OR security_id IS NULL) ORDER BY announcement_date DESC",(iid,sid))
            dividends=_rows(c,"SELECT * FROM dividends WHERE security_id=? ORDER BY announcement_date DESC",(sid,))
            events=_rows(c,"SELECT e.* FROM research_events e LEFT JOIN research_event_securities s ON s.event_id=e.event_id WHERE e.issuer_id=? AND (s.security_id=? OR s.security_id IS NULL) ORDER BY e.publication_at DESC",(iid,sid))
            signal=_row(c,"SELECT * FROM research_signals WHERE security_id=? ORDER BY generated_at DESC LIMIT 1",(sid,))
            history=_rows(c,"SELECT * FROM research_signals WHERE security_id=? ORDER BY generated_at DESC",(sid,))
            factors=_rows(c,"SELECT * FROM factor_scores WHERE security_id=? AND data_snapshot_id=? ORDER BY factor_name",(sid,signal["data_snapshot_id"] if signal else ""))
            sources=_rows(c,"SELECT DISTINCT r.document_id,r.source_id,r.source_url,r.publication_at,r.retrieved_at,r.sha256 FROM raw_documents r WHERE r.document_id IN (SELECT raw_document_id FROM financial_documents WHERE issuer_id=?) OR r.document_id IN (SELECT document_id FROM market_observations WHERE security_id=?)",(iid,sid))
            valuation_status="AVAILABLE" if any(v["status"]=="AVAILABLE" for v in valuations) else "VALUATION_INSUFFICIENT"
            warnings=[]
            if not signal or signal["signal_state"]=="DATA_INSUFFICIENT": warnings.append("DATA_INSUFFICIENT")
            if valuation_status!="AVAILABLE": warnings.append("VALUATION_INSUFFICIENT")
            if liquidity and liquidity["liquidity_state"] in {"LIQUIDITY_TRAP","UNASSESSABLE"}: warnings.append(liquidity["liquidity_state"])
            if signal and float(signal["confidence"])<50: warnings.append("LOW_CONFIDENCE")
            if identity["security_class_code"]=="PREFERRED" and (not rights_assessment or rights_assessment["classification"]!="RIGHTS_VERIFIED"): warnings.append("RIGHTS_UNVERIFIED")
            stale=[r[0] for r in c.execute("SELECT pipeline FROM pipeline_health WHERE status IN('STALE','FAILED')")]
            if "market_data" in stale: warnings.append("STALE_DATA")
            if "financial_documents" in stale or "financial_normalization" in stale: warnings.append("STALE_FINANCIALS")
            detail={"api_version":API_VERSION,"as_of":signal["generated_at"] if signal else (market[0]["trade_date"] if market else None),"status":"OK","identity":identity,"market_observations":market,"market_quality":quality,"market_flags":flags,"financial_documents":documents,"normalized_financials":financials,"fundamentals":metrics,"valuation":valuations,"valuation_methods":attempts,"valuation_assumptions":assumptions,"valuation_status":valuation_status,"liquidity":liquidity,"capacity":capacity,"ownership":ownership,"ownership_metrics":ownership_metrics,"rights":rights,"rights_assessment":rights_assessment,"governance":governance,"corporate_actions":actions,"dividends":dividends,"events":events,"factors":factors,"data_quality":next((f for f in factors if f["factor_name"]=="Data Quality"),None),"signal":signal,"signal_history":history,"warnings":warnings,"sources":sources,"source_record_ids":[s["document_id"] for s in sources]}
            detail["report"]=grounded_report(detail)
            return detail

    def issuer(self, issuer_id: str):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection
            issuer=_row(c,"SELECT * FROM issuers WHERE issuer_id=?",(issuer_id,))
            if not issuer: raise KeyError(issuer_id)
            return {"api_version":API_VERSION,"status":"OK","issuer":issuer,"securities":_rows(c,"SELECT * FROM securities WHERE issuer_id=?",(issuer_id,)),"names":_rows(c,"SELECT * FROM issuer_name_history WHERE issuer_id=? ORDER BY known_at DESC",(issuer_id,))}

    def macro(self):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection
            return {"api_version":API_VERSION,"status":"OK","regimes":_rows(c,"SELECT * FROM macro_regimes ORDER BY as_of_date DESC,label LIMIT 100"),"observations":_rows(c,"SELECT o.*,s.name series_name FROM macro_observations o JOIN macro_series s USING(series_id) ORDER BY o.vintage_known_at DESC LIMIT 300")}

    def portfolios(self):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection
            runs=_rows(c,"SELECT r.*,v.classification validation_classification,v.evidence_outcome FROM portfolio_runs r LEFT JOIN validation_runs v USING(validation_run_id) ORDER BY r.created_at DESC LIMIT 27")
            for run in runs: run["positions"]=_rows(c,"SELECT * FROM portfolio_positions WHERE portfolio_id=? ORDER BY target_weight DESC",(run["portfolio_id"],))
            return {"api_version":API_VERSION,"status":"OK","runs":runs}

    def backtests(self):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection
            return {"api_version":API_VERSION,"status":"BACKTEST_INSUFFICIENT","runs":_rows(c,"SELECT * FROM backtest_runs ORDER BY created_at DESC LIMIT 21"),"orders":c.execute("SELECT count(*) FROM backtest_orders").fetchone()[0],"fills":c.execute("SELECT count(*) FROM backtest_fills").fetchone()[0]}

    def validation(self):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection; run=_row(c,"SELECT * FROM validation_runs ORDER BY created_at DESC LIMIT 1")
            return {"api_version":API_VERSION,"status":"OK","validation":run,"experiments":_rows(c,"SELECT * FROM experiment_registry WHERE validation_run_id=? ORDER BY registered_at,experiment_name",(run["validation_run_id"],)) if run else [],"risks":_rows(c,"SELECT * FROM model_risk_findings WHERE validation_run_id=? ORDER BY severity,risk_type",(run["validation_run_id"],)) if run else []}

    def pipelines(self):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection
            from .operations import register_pipelines
            register_pipelines(repo)
            health=_rows(c,"SELECT * FROM pipeline_health ORDER BY pipeline")
            if any(row.get("last_attempt_at") for row in health):
                return {"api_version":API_VERSION,"status":"OK","pipelines":health,"recent_runs":_rows(c,"SELECT * FROM scheduled_pipeline_runs ORDER BY started_at DESC LIMIT 100"),"open_alerts":_rows(c,"SELECT * FROM research_alerts WHERE status='OPEN' ORDER BY created_at DESC LIMIT 100")}
            def latest_run(source): return _row(c,"SELECT r.*,s.name source_name FROM ingestion_runs r JOIN data_sources s USING(source_id) WHERE r.source_id=? ORDER BY r.started_at DESC LIMIT 1",(source,))
            def analytical(name,table,time_col,source,status="SUCCEEDED"):
                stamp=c.execute(f"SELECT max({time_col}) FROM {table}").fetchone()[0]
                return {"pipeline":name,"status":status if stamp else "FAILED","health":status if stamp and status in {"HEALTHY","STALE","DEGRADED","FAILED"} else "HEALTHY" if stamp else "FAILED","last_successful_update":stamp,"latest_failure":None,"freshness":stamp,"source":source}
            security=latest_run("uzse-public-web")
            market=_row(c,"SELECT * FROM market_ingestion_runs ORDER BY started_at DESC LIMIT 1")
            financial=latest_run("openinfo-disclosure") or latest_run("openinfo-attachment")
            def run_stage(name,row,source):
                raw=(row or {}).get("status","FAILED"); health="HEALTHY" if raw=="SUCCEEDED" else "DEGRADED" if raw=="PARTIAL" else "FAILED"
                return {"pipeline":name,"status":raw,"health":health,"last_successful_update":row.get("finished_at") if row and raw in {"SUCCEEDED","PARTIAL"} else None,"latest_failure":row.get("error_details") if row and row.get("errors") else None,"freshness":row.get("finished_at") if row else None,"source":source,"parser_version":row.get("parser_version") if row else None}
            stages=[run_stage("security master",security,"RSE Toshkent"),run_stage("market data",market,"RSE Toshkent"),run_stage("financials",financial,"Openinfo")]
            stages.extend((analytical("corporate intelligence","governance_events","disclosure_date","Openinfo/RSE"),analytical("valuation","valuation_records","created_at","UZQUANT deterministic engine","DEGRADED"),analytical("liquidity","liquidity_assessments","created_at","RSE market observations"),analytical("events","research_events","created_at","Openinfo"),analytical("macro","macro_observations","retrieved_at","CBU/verified macro sources"),analytical("signals","research_signals","generated_at","UZQUANT deterministic engine")))
            return {"api_version":API_VERSION,"status":"OK","pipelines":stages}

    def operations(self):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection
            return {"api_version":API_VERSION,"status":"OK","health":_rows(c,"SELECT * FROM pipeline_health ORDER BY pipeline"),"runs":_rows(c,"SELECT * FROM scheduled_pipeline_runs ORDER BY started_at DESC LIMIT 200"),"anomalies":_rows(c,"SELECT * FROM research_anomalies ORDER BY created_at DESC LIMIT 200"),"alerts":_rows(c,"SELECT * FROM research_alerts ORDER BY created_at DESC LIMIT 200"),"signal_transitions":_rows(c,"SELECT * FROM signal_state_transitions ORDER BY changed_at DESC LIMIT 200")}

    def paper_trading(self):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection
            portfolios=_rows(c,"SELECT * FROM shadow_portfolios ORDER BY created_at DESC,portfolio_type")
            for portfolio in portfolios:
                portfolio["positions"]=_rows(c,"SELECT * FROM paper_positions WHERE shadow_portfolio_id=?",(portfolio["shadow_portfolio_id"],))
            return {"api_version":API_VERSION,"status":"OK","portfolios":portfolios,"snapshots":_rows(c,"SELECT * FROM prospective_decision_snapshots ORDER BY decision_timestamp DESC LIMIT 100"),"security_states":_rows(c,"SELECT * FROM prospective_security_states ORDER BY rowid DESC LIMIT 500"),"orders":_rows(c,"SELECT * FROM paper_orders ORDER BY submitted_at DESC LIMIT 500"),"fills":_rows(c,"SELECT * FROM paper_fills ORDER BY fill_timestamp DESC LIMIT 500"),"signal_outcomes":_rows(c,"SELECT * FROM paper_signal_outcomes ORDER BY evaluation_timestamp DESC LIMIT 500"),"drift":_rows(c,"SELECT * FROM paper_drift_assessments ORDER BY assessed_at DESC LIMIT 100")}
