from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .liquidity import MODEL_VERSION as LIQUIDITY_VERSION
from .repository import Repository, utc_now
from .valuation import MODEL_VERSION as VALUATION_VERSION

D = Decimal
MODEL_VERSION = "research-ranking/1.1.0"
SCORING_VERSION = "factor-scoring/1.1.0"
FACTORS = ("Valuation","Quality","Growth","Momentum","Dividend","Liquidity","Governance",
           "Catalyst","Balance-Sheet Risk","Data Quality")
SIGNAL_STATES = ("STRONG_BUY","BUY","ACCUMULATE","WATCH","HOLD","REDUCE","AVOID",
                 "LIQUIDITY_TRAP","GOVERNANCE_RISK","DATA_INSUFFICIENT")
DEFAULT_WEIGHTS = {"Valuation":D("0.25"),"Quality":D("0.15"),"Growth":D("0.10"),
    "Momentum":D("0.05"),"Dividend":D("0.05"),"Liquidity":D("0.15"),
    "Governance":D("0.10"),"Catalyst":D("0.00"),"Balance-Sheet Risk":D("0.10"),
    "Data Quality":D("0.05")}


@dataclass(frozen=True)
class FactorScore:
    name: str
    raw_metric: dict
    transformation: str
    score: Decimal | None
    reason: str | None = None
    source_ids: tuple[str, ...] = ()
    @property
    def status(self): return "AVAILABLE" if self.score is not None else "UNAVAILABLE"


@dataclass(frozen=True)
class Evidence:
    financial_document_count: int = 0
    late_report_count: int = 0
    conflict_count: int = 0
    ocr_dependency: bool = False
    shares_outstanding_verified: bool = False
    market_observation_count: int = 0
    ownership_known: bool = False
    rights_confidence: str | None = None
    valuation_available: bool = False
    liquidity_confidence: str | None = None


@dataclass(frozen=True)
class SignalResult:
    state: str
    attractiveness: Decimal | None
    confidence: Decimal
    gates: tuple[str, ...]
    tentative_state: str | None


def cross_sectional_scores(values: dict[str, Decimal], minimum_peers: int = 5):
    if len(values) < minimum_peers:
        return {key: FactorScore("Cross-sectional", {"value":str(value),"peer_count":len(values)},
            f"PERCENTILE_REQUIRES_{minimum_peers}_PEERS", None, "SMALL_PEER_GROUP") for key,value in values.items()}
    ordered=sorted(values.items(),key=lambda item:(item[1],item[0])); n=len(ordered)
    return {key:FactorScore("Cross-sectional",{"value":str(value),"peer_count":n},
        "EMPIRICAL_PERCENTILE_NO_WINSORIZATION",D("100")*D(rank)/D(n-1))
        for rank,(key,value) in enumerate(ordered)}


def data_quality_score(e: Evidence) -> FactorScore:
    score=D("100"); penalties=[]
    def penalize(points,reason):
        nonlocal score; score-=D(points); penalties.append({"reason":reason,"points":points})
    if e.financial_document_count == 0: penalize(30,"MISSING_STATEMENTS")
    elif e.financial_document_count < 3: penalize(15,"SHORT_FINANCIAL_HISTORY")
    if e.late_report_count: penalize(min(15,5*e.late_report_count),"LATE_REPORTS")
    if e.conflict_count: penalize(min(20,10*e.conflict_count),"CONFLICTING_VALUES")
    if e.ocr_dependency: penalize(5,"OCR_DEPENDENCY")
    if not e.shares_outstanding_verified: penalize(15,"UNCERTAIN_SHARES_OUTSTANDING")
    if e.market_observation_count < 60: penalize(15,"WEAK_MARKET_HISTORY")
    if not e.ownership_known: penalize(10,"UNKNOWN_OWNERSHIP")
    if e.rights_confidence is not None and e.rights_confidence != "HIGH": penalize(10,"UNKNOWN_OR_WEAK_SHARE_RIGHTS")
    if not e.valuation_available: penalize(5,"VALUATION_UNAVAILABLE")
    return FactorScore("Data Quality",{"evidence":e.__dict__,"penalties":penalties},
                       "100_MINUS_DOCUMENTED_EVIDENCE_PENALTIES",max(D("0"),score))


def liquidity_score(state: str | None, confidence: str | None, source_id: str | None = None):
    mapping={"INVESTABLE":D("80"),"LIMITED_LIQUIDITY":D("50"),
             "HIGH_LIQUIDITY_RISK":D("20"),"LIQUIDITY_TRAP":D("0")}
    if state not in mapping:
        return FactorScore("Liquidity",{"state":state,"confidence":confidence},
                           "ABSOLUTE_STATE_MAPPING",None,"LIQUIDITY_UNASSESSABLE")
    score=mapping[state]
    if confidence == "LOW": score=min(score,D("60"))
    return FactorScore("Liquidity",{"state":state,"confidence":confidence},
                       "ABSOLUTE_STATE_MAPPING_WITH_CONFIDENCE_CAP",score,
                       source_ids=(source_id,) if source_id else ())


def sector_factor_metrics(sector: str):
    sector=sector.upper()
    if sector == "BANK": return {"Quality":("ROE","NIM","Cost/Income"),"Growth":("Loan Growth","Deposit Growth"),"Balance-Sheet Risk":("NPL","Capital Adequacy")}
    if sector == "INSURANCE": return {"Quality":("Combined Ratio","ROE"),"Growth":("Premium Growth",),"Balance-Sheet Risk":("Solvency","Reserves")}
    if sector in {"MINING","COMMODITY"}: return {"Quality":("ROIC","Operating Leverage"),"Growth":("Production","Revenue Growth"),"Balance-Sheet Risk":("Net Debt/EBITDA",)}
    return {"Quality":("ROIC","Gross Margin","Net Margin"),"Growth":("Revenue Growth","EBIT Growth"),"Balance-Sheet Risk":("Net Debt/EBITDA","Interest Coverage")}


def catalyst_factor(rows):
    supported=[r for r in rows if r["catalyst_score"] is not None]
    raw={"events":[{"event_id":r["event_id"],"event_type":r["event_type"],"publication_at":r["publication_at"],"materiality":r["event_materiality"],"relevance":r["catalyst_relevance"],"confidence":r["catalyst_confidence"],"score":r["catalyst_score"]} for r in rows]}
    if not supported: return FactorScore("Catalyst",raw,"MAX_SUPPORTED_EVENT_RELEVANCE",None,"NO_DIRECTIONALLY_SUPPORTED_CATALYST")
    best=max(supported,key=lambda r:D(r["catalyst_score"]))
    return FactorScore("Catalyst",raw,"MAX_SUPPORTED_EVENT_RELEVANCE",D(best["catalyst_score"]),source_ids=tuple(r["event_id"] for r in supported))

def governance_factor(rows):
    """Score only explicitly adverse, high-confidence stored governance evidence."""
    adverse={"RELATED_PARTY":D("30"),"AUDITOR_CHANGE":D("40"),"LATE_FILING":D("35"),
             "DILUTION":D("25"),"RESTATEMENT":D("30"),"MINORITY_HOLDER_ISSUE":D("10")}
    supported=[r for r in rows if r[1] in adverse and r[2] in {"HIGH","MEDIUM"}]
    raw={"events":[{"event_id":r[0],"event_type":r[1],"confidence":r[2]} for r in rows]}
    if not supported: return _unavailable("Governance","NO_DIRECTIONALLY_SUPPORTED_GOVERNANCE_EVIDENCE",tuple(r[0] for r in rows))
    score=min(adverse[r[1]] for r in supported)
    return FactorScore("Governance",raw,"MIN_DOCUMENTED_ADVERSE_EVENT_SCORE",score,source_ids=tuple(r[0] for r in supported))


def aggregate_attractiveness(factors: dict[str,FactorScore], weights=DEFAULT_WEIGHTS,
                             minimum_available_factors: int = 4):
    available=[f for f in factors.values() if f.score is not None and weights.get(f.name,D("0"))>0]
    if len(available)<minimum_available_factors: return None,"INSUFFICIENT_FACTOR_COVERAGE"
    total=sum((weights[f.name] for f in available),D("0"))
    if total==0: return None,"ZERO_AVAILABLE_WEIGHT"
    return sum((f.score*weights[f.name] for f in available),D("0"))/total,None


def confidence_score(data_quality: Decimal, reporting_history: Decimal,
                     liquidity_evidence: Decimal, ownership_transparency: Decimal,
                     share_rights_certainty: Decimal, valuation_stability: Decimal,
                     model_coverage: Decimal):
    values=(data_quality,reporting_history,liquidity_evidence,ownership_transparency,
            share_rights_certainty,valuation_stability,model_coverage)
    if any(v<0 or v>100 for v in values): raise ValueError("confidence inputs must be 0..100")
    weights=(D(".30"),D(".15"),D(".15"),D(".10"),D(".10"),D(".10"),D(".10"))
    return sum((v*w for v,w in zip(values,weights)),D("0"))


def _tentative(score):
    if score is None:return None
    for boundary,state in ((80,"STRONG_BUY"),(70,"BUY"),(60,"ACCUMULATE"),(45,"WATCH"),(35,"HOLD"),(20,"REDUCE")):
        if score>=boundary:return state
    return "AVOID"


def apply_risk_gates(attractiveness: Decimal | None, confidence: Decimal,
                     data_quality: Decimal, liquidity_state: str | None,
                     severe_governance: bool = False, rights_unknown: bool = False,
                     stale_price: bool = False) -> SignalResult:
    tentative=_tentative(attractiveness); gates=[]
    if data_quality < 50: gates.append("CRITICAL_DATA_QUALITY")
    if liquidity_state in {"LIQUIDITY_TRAP","UNASSESSABLE"}: gates.append("CRITICAL_LIQUIDITY_FAILURE")
    if severe_governance: gates.append("SEVERE_GOVERNANCE_ISSUE")
    if rights_unknown: gates.append("MATERIALLY_UNKNOWN_SHARE_RIGHTS")
    if stale_price: gates.append("STALE_PRICE_SUPPRESS_MOMENTUM_AND_EXECUTION_CONFIDENCE")
    if "CRITICAL_DATA_QUALITY" in gates: state="DATA_INSUFFICIENT"
    elif "SEVERE_GOVERNANCE_ISSUE" in gates: state="GOVERNANCE_RISK"
    elif "CRITICAL_LIQUIDITY_FAILURE" in gates: state="LIQUIDITY_TRAP"
    elif tentative is None: state="DATA_INSUFFICIENT"
    elif tentative in {"STRONG_BUY","BUY"} and (confidence<50 or rights_unknown or stale_price): state="WATCH"
    else: state=tentative
    return SignalResult(state,attractiveness,confidence,tuple(gates),tentative)


def _snapshot_id(repo):
    pieces=[]
    for table,column in (("ingestion_runs","finished_at"),("market_ingestion_runs","finished_at"),
                         ("financial_documents","retrieved_at"),("liquidity_assessments","created_at"),
                         ("valuation_records","created_at"),("fundamental_metrics","created_at"),
                         ("accounting_quality_flags","created_at"),("security_rights","disclosure_date"),
                         ("ownership_positions","disclosure_date"),("governance_events","disclosure_date"),
                         ("dividends","announcement_date"),("corporate_actions","announcement_date"),
                         ("research_events","created_at"),("catalyst_assessments","created_at"),
                         ("research_event_conflicts","created_at")):
        row=repo.connection.execute(f"SELECT count(*),coalesce(max({column}),'') FROM {table}").fetchone(); pieces.extend(map(str,row))
    return hashlib.sha256("|".join(pieces).encode()).hexdigest()


def _unavailable(name,reason,source_ids=()): return FactorScore(name,{},"NOT_TRANSFORMED",None,reason,tuple(source_ids))


def _fundamental_factor(repo, issuer_id, name, metric_names, as_of):
    placeholders=",".join("?" for _ in metric_names)
    rows=repo.connection.execute(
        f"SELECT metric_id,metric_name,metric_value FROM fundamental_metrics WHERE issuer_id=? "
        f"AND period_end<=? AND status='AVAILABLE' AND metric_name IN ({placeholders}) "
        "ORDER BY period_end DESC,created_at DESC", (issuer_id,as_of.isoformat(),*metric_names)).fetchall()
    latest={}
    for row in rows: latest.setdefault(row[1],row)
    if not latest: return _unavailable(name,"NO_SUPPORTED_FUNDAMENTAL_METRIC")
    values={k:D(v[2]) for k,v in latest.items()}
    if name=="Growth": transformed=[max(D("0"),min(D("100"),D("50")+v*D("100"))) for v in values.values()]
    elif name=="Balance-Sheet Risk": transformed=[max(D("0"),min(D("100"),D("100")-abs(v)*D("50"))) for v in values.values()]
    else: transformed=[max(D("0"),min(D("100"),v*D("100"))) for v in values.values()]
    return FactorScore(name,{"metrics":{k:str(v) for k,v in values.items()}},
        "DOCUMENTED_ABSOLUTE_METRIC_TRANSFORMATION_MEAN",sum(transformed,D("0"))/D(len(transformed)),
        source_ids=tuple(v[0] for v in latest.values()))


def score_real_universe(database: Path, as_of: date | None = None):
    as_of = as_of or date.today()
    with Repository(database) as repo:
        repo.initialize(); snapshot=_snapshot_id(repo)
        securities=repo.connection.execute("SELECT DISTINCT s.security_id,s.issuer_id,s.security_class_code,h.identifier_value ticker FROM securities s JOIN identifier_history h ON h.security_id=s.security_id AND h.identifier_type='TICKER' WHERE EXISTS(SELECT 1 FROM market_observations m WHERE m.security_id=s.security_id) ORDER BY h.identifier_value").fetchall()
        output=[]
        for s in securities:
            sid,issuer_id,security_class,ticker=s
            docs=repo.connection.execute("SELECT d.document_id FROM financial_documents d JOIN financial_document_entity_checks c USING(document_id) JOIN financial_document_identity_assignments a USING(document_id) WHERE d.issuer_id=? AND d.publication_date<=? AND c.validation_status='MATCHED' AND a.assignment_status='VERIFIED'",(issuer_id,as_of.isoformat())).fetchall()
            observations=repo.connection.execute("SELECT count(*) FROM market_observations WHERE security_id=? AND trade_date<=? AND series_type='RAW_OBSERVED'",(sid,as_of.isoformat())).fetchone()[0]
            rights=repo.connection.execute("SELECT rights_id,rights_confidence FROM security_rights WHERE security_id=? AND disclosure_date<=? ORDER BY disclosure_date DESC LIMIT 1",(sid,as_of.isoformat())).fetchone()
            ownership=repo.connection.execute("SELECT count(*) FROM ownership_positions WHERE issuer_id=? AND disclosure_date<=? AND ownership_percentage IS NOT NULL",(issuer_id,as_of.isoformat())).fetchone()[0]
            conflicts=repo.connection.execute("SELECT count(*) FROM financial_validation_issues v JOIN financial_documents d USING(document_id) WHERE d.issuer_id=? AND v.issue_type LIKE '%CONFLICT%'",(issuer_id,)).fetchone()[0]
            valuation=repo.connection.execute("SELECT valuation_id,status,base_value FROM valuation_records WHERE security_id=? AND data_cutoff_date<=? ORDER BY (status='AVAILABLE') DESC,created_at DESC LIMIT 1",(sid,as_of.isoformat())).fetchone()
            liq=repo.connection.execute("SELECT assessment_id,liquidity_state,liquidity_confidence,hard_flags_json FROM liquidity_assessments WHERE security_id=? AND as_of_date<=? AND participation_rate='0.10' AND position_shares='10000' ORDER BY as_of_date DESC LIMIT 1",(sid,as_of.isoformat())).fetchone()
            ocr=bool(repo.connection.execute("SELECT 1 FROM financial_observations WHERE issuer_id=? AND extraction_method='OCR' LIMIT 1",(issuer_id,)).fetchone())
            verified_shares=bool(repo.connection.execute("SELECT 1 FROM share_capital_observations WHERE security_id=? AND disclosure_date<=? AND effective_date<=? AND verification_status='VERIFIED' AND class_shares_outstanding IS NOT NULL LIMIT 1",(sid,as_of.isoformat(),as_of.isoformat())).fetchone())
            rights_evidence=(rights[1] if rights else "MISSING") if security_class=="PREFERRED" else None
            evidence=Evidence(len(docs),0,conflicts,ocr,verified_shares,observations,bool(ownership),rights_evidence,bool(valuation and valuation[1]=="AVAILABLE"),liq[2] if liq else None)
            dq=data_quality_score(evidence); lq=liquidity_score(liq[1] if liq else None,liq[2] if liq else None,liq[0] if liq else None)
            factors={name:_unavailable(name,"INSUFFICIENT_VERIFIED_INPUTS") for name in FACTORS}
            factors["Data Quality"]=dq; factors["Liquidity"]=lq
            if valuation and valuation[1]=="AVAILABLE" and valuation[2] is not None:
                price=repo.connection.execute("SELECT coalesce(close,last,individual_trade_price) FROM market_observations WHERE security_id=? AND trade_date<=? ORDER BY trade_date DESC LIMIT 1",(sid,as_of.isoformat())).fetchone()
                if price and price[0] and D(str(price[0]))>0:
                    upside=D(valuation[2])/D(str(price[0]))-D("1")
                    score=max(D("0"),min(D("100"),D("50")+upside*D("100")))
                    factors["Valuation"]=FactorScore("Valuation",{"valuation_id":valuation[0],"base_value":valuation[2],"price":str(price[0]),"upside":str(upside)},"ABSOLUTE_UPSIDE_SCORE_50_PLUS_100X_UPSIDE_CAPPED_0_100",score,source_ids=(valuation[0],))
            else: factors["Valuation"]=_unavailable("Valuation","VALUATION_INSUFFICIENT",(valuation[0],) if valuation else ())
            sector_row=repo.connection.execute("SELECT coalesce(i.sector,'GENERAL'),coalesce((SELECT source_url FROM financial_documents WHERE issuer_id=i.issuer_id ORDER BY publication_date DESC LIMIT 1),'') FROM issuers i WHERE issuer_id=?",(issuer_id,)).fetchone()
            routed_sector="BANK" if "/bank/" in sector_row[1] else "INSURANCE" if "/insurance/" in sector_row[1] else sector_row[0]
            metrics=sector_factor_metrics(routed_sector)
            factors["Quality"]=_fundamental_factor(repo,issuer_id,"Quality",metrics["Quality"],as_of)
            factors["Growth"]=_fundamental_factor(repo,issuer_id,"Growth",metrics["Growth"],as_of)
            factors["Balance-Sheet Risk"]=_fundamental_factor(repo,issuer_id,"Balance-Sheet Risk",metrics["Balance-Sheet Risk"],as_of)
            factors["Momentum"]=_unavailable("Momentum","MARKET_HISTORY_BELOW_60_OBSERVATIONS")
            factors["Dividend"]=_unavailable("Dividend","NO_DATE_COMPATIBLE_DIVIDEND_SCORE")
            catalyst_rows=repo.connection.execute("SELECT e.event_id,e.event_type,e.publication_at,c.event_materiality,c.catalyst_relevance,c.catalyst_confidence,c.catalyst_score FROM research_events e JOIN research_event_securities es USING(event_id) JOIN catalyst_assessments c USING(event_id) WHERE es.security_id=? AND e.publication_at<=? ORDER BY e.publication_at",(sid,as_of.isoformat())).fetchall()
            factors["Catalyst"]=catalyst_factor(catalyst_rows)
            governance_rows=repo.connection.execute("SELECT event_id,event_type,confidence FROM governance_events WHERE issuer_id=? AND disclosure_date<=? ORDER BY disclosure_date",(issuer_id,as_of.isoformat())).fetchall()
            factors["Governance"]=governance_factor(governance_rows)
            attractiveness,_=aggregate_attractiveness(factors)
            available_count=sum(f.score is not None for f in factors.values())
            conf=confidence_score(dq.score,D("0") if len(docs)<3 else D("100"),D("25") if evidence.liquidity_confidence=="LOW" else D("75"),D("100") if ownership else D("0"),D("100") if evidence.rights_confidence=="HIGH" else D("0"),D("100") if evidence.valuation_available else D("0"),D(available_count)*D("10"))
            hard_flags=json.loads(liq[3]) if liq else []
            stale="UNRELIABLE_LAST_PRICE" in hard_flags or "EXTREME_STALENESS" in hard_flags
            result=apply_risk_gates(attractiveness,conf,dq.score,liq[1] if liq else None,False,security_class=="PREFERRED" and evidence.rights_confidence!="HIGH",stale)
            generated=utc_now(); factor_json={name:{"score":str(f.score) if f.score is not None else None,"status":f.status,"reason":f.reason,"raw_metric":f.raw_metric,"transformation":f.transformation} for name,f in factors.items()}
            for name,f in factors.items():
                repo.connection.execute("INSERT INTO factor_scores VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),sid,snapshot,as_of.isoformat(),name,json.dumps(f.raw_metric,sort_keys=True,default=str),f.transformation,str(f.score) if f.score is not None else None,f.status,f.reason,None,json.dumps(f.source_ids),SCORING_VERSION,generated))
            signal_id=str(uuid.uuid4()); explanation={"ticker":ticker,"tentative_state":result.tentative_state,"available_factor_count":available_count,"missing_factors":[n for n,f in factors.items() if f.score is None],"research_classification_not_order":True}
            repo.connection.execute("INSERT INTO research_signals VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(signal_id,sid,result.state,str(result.attractiveness) if result.attractiveness is not None else None,str(result.confidence),json.dumps(factor_json,sort_keys=True),json.dumps(result.gates),json.dumps(explanation,sort_keys=True),MODEL_VERSION,SCORING_VERSION,VALUATION_VERSION,LIQUIDITY_VERSION,snapshot,generated))
            output.append({"ticker":ticker,"security_id":sid,"signal_id":signal_id,"result":result,"factors":factors,"snapshot":snapshot,"generated_at":generated})
        repo.connection.commit(); return output
