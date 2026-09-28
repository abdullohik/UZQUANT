from __future__ import annotations

import json
from pathlib import Path

from .repository import Repository

API_VERSION = "research-api/1.1.0"

FACTOR_NAMES = ("Valuation", "Quality", "Growth", "Momentum", "Dividend",
                "Governance", "Catalyst", "Balance-Sheet Risk", "Liquidity",
                "Data Quality")


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


def _health_context(connection):
    rows=_rows(connection,"SELECT pipeline,status,source,latest_error,last_success_at,expected_refresh_at,updated_at FROM pipeline_health ORDER BY pipeline")
    rank={"HEALTHY":0,"DEGRADED":1,"STALE":2,"FAILED":3}; state=max((r["status"] for r in rows),key=lambda x:rank[x],default="STALE")
    affected=[r for r in rows if r["status"]!="HEALTHY"]
    return {"upstream_health":state,"data_freshness":{r["pipeline"]:r["last_success_at"] for r in rows},"degraded_reason":[r["latest_error"] or r["status"] for r in affected],"affected_source":sorted({r["source"] for r in affected}),"affected_dependencies":[r["pipeline"] for r in affected],"generated_at":max((r["updated_at"] for r in rows),default=None),"as_of":max((r["last_success_at"] or "" for r in rows),default=None) or None}


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
        "Data Health": str(detail.get("health_context") or "Unavailable"),
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
                valuation=_row(repo.connection,"SELECT valuation_id,status,valuation_date,bear_value,base_value,bull_value,confidence,method,currency FROM valuation_records WHERE security_id=? ORDER BY (status='AVAILABLE') DESC,created_at DESC LIMIT 1",(sid,))
                factors=(signal or {}).get("factor_scores_json",{})
                available_factors=[name for name,value in factors.items() if value.get("status")=="AVAILABLE" and value.get("score") is not None]
                factor_count=len(available_factors)
                valuation_status=valuation["status"] if valuation else "VALUATION_INSUFFICIENT"
                signal_state=signal.get("signal_state") if signal else "DATA_INSUFFICIENT"
                if valuation_status=="AVAILABLE" and factor_count>=4 and signal_state!="DATA_INSUFFICIENT": coverage="RESEARCH_READY"
                elif market or factors: coverage="PARTIALLY_RESEARCHABLE"
                else: coverage="DATA_INSUFFICIENT"
                market_flags=[r[0] for r in repo.connection.execute("SELECT flag_type FROM market_quality_flags WHERE security_id=? AND flag_type IN('STALE_PRICE','VERY_STALE_PRICE') ORDER BY created_at DESC",(sid,)).fetchall()]
                freshness="STALE" if market_flags else ("CURRENT_OBSERVATION" if market else "NO_MARKET_DATA")
                blockers=[]
                if valuation_status!="AVAILABLE": blockers.append("VALUATION_INSUFFICIENT")
                if factor_count<4: blockers.append("INSUFFICIENT_FACTOR_COVERAGE")
                if signal_state=="DATA_INSUFFICIENT": blockers.append("DATA_INSUFFICIENT")
                if freshness=="STALE": blockers.append("STALE")
                result.append({**item,"market":market,"valuation":valuation,"valuation_status":valuation_status,
                    "quality":factors.get("Quality"),"growth":factors.get("Growth"),"data_quality":factors.get("Data Quality"),
                    "confidence":signal.get("confidence") if signal else None,"signal":signal_state,
                    "risk_gates":signal.get("triggered_gates_json",[]) if signal else [],"liquidity":liquidity,
                    "factor_count":factor_count,"available_factors":available_factors,"required_factor_count":4,
                    "coverage_state":coverage,"coverage_blockers":sorted(set(blockers)),"freshness":freshness})
            def keep(x):
                return (not filters.get("sector") or x.get("sector")==filters["sector"]) and (not filters.get("signal") or x["signal"]==filters["signal"]) and (not filters.get("liquidity") or (x.get("liquidity") or {}).get("liquidity_state")==filters["liquidity"]) and (not filters.get("valuation") or x["valuation_status"]==filters["valuation"]) and (not filters.get("security_class") or x["security_class_code"]==filters["security_class"]) and (not filters.get("freshness") or x["freshness"]==filters["freshness"]) and (not filters.get("coverage") or x["coverage_state"]==filters["coverage"])
            return {"api_version":API_VERSION,"status":"OK","health_context":_health_context(repo.connection),"count":sum(keep(x) for x in result),"securities":[x for x in result if keep(x)]}

    def overview(self):
        universe=self.universe()["securities"]
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection
            def counts(items,key):
                result={}
                for item in items:
                    value=item.get(key) or "UNAVAILABLE"; result[value]=result.get(value,0)+1
                return result
            latest_market=_rows(c,"""WITH tickers AS (
                SELECT security_id,identifier_value,ROW_NUMBER() OVER(PARTITION BY security_id ORDER BY known_at DESC) rn
                FROM identifier_history WHERE identifier_type='TICKER'), ranked AS (
                SELECT m.*,ROW_NUMBER() OVER(PARTITION BY m.security_id ORDER BY m.trade_date DESC,m.last_seen_at DESC) rn
                FROM market_observations m WHERE m.series_type='RAW_OBSERVED')
                SELECT t.identifier_value ticker,m.security_id,m.trade_date,coalesce(m.last,m.close,m.individual_trade_price) price,
                m.share_volume,m.turnover_value,m.currency,m.observation_status FROM ranked m JOIN tickers t USING(security_id)
                WHERE m.rn=1 AND t.rn=1 ORDER BY m.trade_date DESC,t.identifier_value LIMIT 20""")
            valuations=_rows(c,"""WITH tickers AS (
                SELECT security_id,identifier_value,ROW_NUMBER() OVER(PARTITION BY security_id ORDER BY known_at DESC) rn
                FROM identifier_history WHERE identifier_type='TICKER'), ranked AS (
                SELECT v.*,ROW_NUMBER() OVER(PARTITION BY security_id,method ORDER BY created_at DESC) rn FROM valuation_records v)
                SELECT t.identifier_value ticker,v.method,v.status,v.valuation_date,v.bear_value,v.base_value,v.bull_value,v.confidence,v.currency
                FROM ranked v JOIN tickers t USING(security_id) WHERE v.rn=1 AND t.rn=1
                ORDER BY (v.status='AVAILABLE') DESC,v.valuation_date DESC,t.identifier_value,v.method LIMIT 12""")
            snapshots=_rows(c,"SELECT prospective_snapshot_id,decision_timestamp,trigger_type,upstream_state,created_at FROM prospective_decision_snapshots ORDER BY decision_timestamp DESC LIMIT 5")
            backfill={row["status"]:row["count"] for row in _rows(c,"SELECT status,count(*) count FROM rse_history_acquisition_jobs GROUP BY status")}
            alerts=_rows(c,"SELECT alert_type,severity,entity_type,entity_id,title,message,created_at FROM research_alerts WHERE status='OPEN' ORDER BY created_at DESC LIMIT 10")
            transitions=_rows(c,"SELECT * FROM signal_state_transitions ORDER BY changed_at DESC LIMIT 10")
            health=_rows(c,"SELECT pipeline,status,last_success_at,expected_refresh_at,latest_error,source FROM pipeline_health ORDER BY pipeline")
            return {"api_version":API_VERSION,"status":"OK","generated_from":"CANONICAL_BACKEND_RECORDS",
                    "health_context":_health_context(c),"pipeline_counts":counts(health,"status"),
                    "coverage_counts":counts(universe,"coverage_state"),"signal_counts":counts(universe,"signal"),
                    "valuation_counts":counts(universe,"valuation_status"),"liquidity_counts":counts([{"state":(x.get("liquidity") or {}).get("liquidity_state")} for x in universe],"state"),
                    "security_count":len(universe),"latest_market":latest_market,"latest_valuations":valuations,
                    "latest_transitions":transitions,"alerts":alerts,"snapshots":snapshots,"backfill":backfill,
                    "pipelines":health}

    def lineage(self, ticker: str):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection; identity=self._identity(c,ticker)
            if not identity: raise KeyError(ticker)
            sid=identity["security_id"]
            signal=_row(c,"SELECT * FROM research_signals WHERE security_id=? ORDER BY generated_at DESC LIMIT 1",(sid,))
            factors=_rows(c,"SELECT * FROM factor_scores WHERE security_id=? AND data_snapshot_id=? ORDER BY factor_name",(sid,signal["data_snapshot_id"] if signal else ""))
            valuations=_rows(c,"SELECT * FROM valuation_records WHERE security_id=? ORDER BY (status='AVAILABLE') DESC,created_at DESC",(sid,))
            version_ids=[]
            if signal:
                from .financial_lineage import exact_signal_version_ids
                version_ids=list(exact_signal_version_ids(repo,signal["signal_id"]))
            versions=[]
            if version_ids:
                marks=",".join("?" for _ in version_ids)
                versions=_rows(c,f"""SELECT v.*,r.raw_label,r.raw_value source_raw_value,r.source_location raw_source_location,
                    d.source_url,d.publication_date document_publication_date,d.retrieved_at,d.content_hash
                    FROM financial_observation_versions v LEFT JOIN financial_raw_values r USING(raw_value_id)
                    JOIN financial_documents d USING(document_id) WHERE v.version_id IN ({marks}) ORDER BY v.period_end,v.canonical_concept""",version_ids)
            assumption_lineage=_rows(c,"""SELECT a.assumption_id,a.input_name,a.scenario,a.value,a.provenance_class,a.source,
                d.nominal_real_basis,d.source_date,d.source_url,d.methodology,d.derivation_json,d.confidence assumption_confidence,d.assumption_version,
                l.input_role,l.transformation,l.observation_version_id
                FROM valuation_assumption_inputs a JOIN valuation_assumption_details d USING(assumption_id)
                LEFT JOIN valuation_assumption_observation_lineage l USING(assumption_id)
                WHERE a.security_id=? ORDER BY a.input_name,a.scenario,l.input_role""",(sid,))
            metrics=_rows(c,"""SELECT DISTINCT m.* FROM fundamental_metrics m JOIN factor_scores f
                ON f.security_id=? AND f.data_snapshot_id=?
                WHERE m.metric_id IN (SELECT value FROM json_each(f.source_record_ids_json)) ORDER BY m.metric_name""",(sid,signal["data_snapshot_id"] if signal else ""))
            return {"api_version":API_VERSION,"status":"OK","identity":identity,"signal":signal,"factors":factors,
                    "fundamental_metrics":metrics,"valuations":valuations,"assumption_lineage":assumption_lineage,
                    "normalized_versions":versions,"exact_version_count":len(versions),
                    "lineage_standard":"EXACT_SIGNAL_DEPENDENCY_TRAVERSAL"}

    def security(self, ticker: str):
        with Repository(self.database) as repo:
            repo.initialize(); c=repo.connection; identity=self._identity(c,ticker)
            if not identity: raise KeyError(ticker)
            sid,iid=identity["security_id"],identity["issuer_id"]
            market=_rows(c,"SELECT * FROM market_observations WHERE security_id=? AND series_type='RAW_OBSERVED' ORDER BY trade_date DESC LIMIT 100",(sid,))
            quality=_row(c,"SELECT * FROM market_quality_metrics WHERE security_id=? ORDER BY as_of_date DESC,created_at DESC LIMIT 1",(sid,))
            flags=_rows(c,"SELECT * FROM market_quality_flags WHERE security_id=? ORDER BY created_at DESC",(sid,))
            documents=_rows(c,"SELECT d.*,c.validation_status,c.reason entity_check_reason FROM financial_documents d JOIN financial_document_entity_checks c ON c.document_id=d.document_id JOIN financial_document_identity_assignments a ON a.document_id=d.document_id WHERE d.issuer_id=? AND c.validation_status='MATCHED' AND a.assignment_status='VERIFIED' ORDER BY d.period_end DESC",(iid,))
            financials=_rows(c,"SELECT o.* FROM financial_observation_versions o JOIN financial_document_entity_checks c ON c.document_id=o.document_id AND c.validation_status='MATCHED' JOIN financial_document_identity_assignments a ON a.document_id=o.document_id AND a.assignment_status='VERIFIED' WHERE o.issuer_id=? AND o.superseded_by_version_id IS NULL ORDER BY o.period_end DESC,o.canonical_concept LIMIT 300",(iid,))
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
            stale=[r[0] for r in c.execute("SELECT pipeline FROM pipeline_health WHERE status IN('DEGRADED','STALE','FAILED')")]
            if "market_data" in stale: warnings.append("STALE_DATA")
            if "financial_documents" in stale or "financial_normalization" in stale: warnings.append("STALE_FINANCIALS")
            detail={"api_version":API_VERSION,"as_of":signal["generated_at"] if signal else (market[0]["trade_date"] if market else None),"status":"OK","health_context":_health_context(c),"identity":identity,"market_observations":market,"market_quality":quality,"market_flags":flags,"financial_documents":documents,"normalized_financials":financials,"fundamentals":metrics,"valuation":valuations,"valuation_methods":attempts,"valuation_assumptions":assumptions,"valuation_status":valuation_status,"liquidity":liquidity,"capacity":capacity,"ownership":ownership,"ownership_metrics":ownership_metrics,"rights":rights,"rights_assessment":rights_assessment,"governance":governance,"corporate_actions":actions,"dividends":dividends,"events":events,"factors":factors,"data_quality":next((f for f in factors if f["factor_name"]=="Data Quality"),None),"signal":signal,"signal_history":history,"warnings":warnings,"sources":sources,"source_record_ids":[s["document_id"] for s in sources]}
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
            return {"api_version":API_VERSION,"status":"OK","health_context":_health_context(c),"runs":runs}

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
            return {"api_version":API_VERSION,"status":"OK","health_context":_health_context(c),"portfolios":portfolios,"snapshots":_rows(c,"SELECT s.*,e.standard evidence_standard,e.payload_sha256 FROM prospective_decision_snapshots s JOIN prospective_snapshot_evidence e USING(prospective_snapshot_id) ORDER BY decision_timestamp DESC LIMIT 100"),"security_states":_rows(c,"SELECT * FROM prospective_security_states ORDER BY rowid DESC LIMIT 500"),"orders":_rows(c,"SELECT * FROM paper_orders ORDER BY submitted_at DESC LIMIT 500"),"fills":_rows(c,"SELECT * FROM paper_fills ORDER BY fill_timestamp DESC LIMIT 500"),"signal_outcomes":_rows(c,"SELECT * FROM paper_signal_outcomes ORDER BY evaluation_timestamp DESC LIMIT 500"),"drift":_rows(c,"SELECT * FROM paper_drift_assessments ORDER BY assessed_at DESC LIMIT 100")}
