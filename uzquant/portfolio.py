from __future__ import annotations

import json
import math
import uuid
from dataclasses import asdict,dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .repository import Repository,utc_now

D=Decimal
MODEL_VERSION="transparent-portfolio/1.0.0"


@dataclass(frozen=True)
class PortfolioConfig:
    single_name_cap:Decimal
    sector_cap:Decimal
    max_liquidation_horizon:Decimal
    confidence_minimum:Decimal
    government_exposure_cap:Decimal
    commodity_exposure_cap:Decimal
    fx_exposure_cap:Decimal
    factor_concentration_cap:Decimal
    correlated_group_cap:Decimal
    correlation_threshold:Decimal=D("0.80")


CONFIGS={
 "CONSERVATIVE":PortfolioConfig(D("0.03"),D("0.15"),D("5"),D("70"),D("0.20"),D("0.15"),D("0.20"),D("0.20"),D("0.10")),
 "BALANCED":PortfolioConfig(D("0.05"),D("0.25"),D("10"),D("60"),D("0.30"),D("0.25"),D("0.30"),D("0.30"),D("0.15")),
 "HIGH_CONVICTION":PortfolioConfig(D("0.08"),D("0.35"),D("15"),D("55"),D("0.40"),D("0.35"),D("0.40"),D("0.40"),D("0.25")),
}


@dataclass(frozen=True)
class Candidate:
    security_id:str
    ticker:str
    expected_upside:Decimal|None
    estimated_downside:Decimal|None
    confidence:Decimal
    liquidity_capacity_value:Decimal|None
    exit_horizon_days:Decimal|None
    volatility:Decimal|None
    sector:str
    governance_score:Decimal|None
    data_quality_score:Decimal|None
    free_float_maximum_value:Decimal|None
    government_exposure:Decimal|None
    commodity_exposure:Decimal|None
    fx_exposure:Decimal|None
    factor_exposures:dict[str,Decimal]
    thesis_reference:str|None
    validation_classification:str
    signal_state:str


@dataclass(frozen=True)
class Position:
    candidate:Candidate
    target_weight:Decimal
    maximum_weight:Decimal
    binding_constraint:str
    risk_contribution:Decimal|None=None


@dataclass(frozen=True)
class PortfolioResult:
    status:str
    positions:tuple[Position,...]
    cash_weight:Decimal
    reasons:tuple[str,...]
    metrics:dict


def _validate_candidate(c:Candidate):
    if not D("0")<=c.confidence<=D("100"):raise ValueError("confidence must be 0..100")
    for value in (c.liquidity_capacity_value,c.exit_horizon_days,c.volatility,c.free_float_maximum_value):
        if value is not None and value<0:raise ValueError("capacity, horizon and volatility cannot be negative")
    for value in (c.government_exposure,c.commodity_exposure,c.fx_exposure,*c.factor_exposures.values()):
        if value is not None and not D("0")<=value<=D("1"):raise ValueError("exposures must be 0..1")


def _risk_contributions(positions:list[Position],correlations:dict[tuple[str,str],Decimal]):
    variance=D("0"); covariance={}
    for p in positions:
        vi=p.candidate.volatility
        if vi is None:return [None]*len(positions)
        marginal=D("0")
        for q in positions:
            vj=q.candidate.volatility
            corr=D("1") if p.candidate.security_id==q.candidate.security_id else correlations.get((p.candidate.security_id,q.candidate.security_id),correlations.get((q.candidate.security_id,p.candidate.security_id)))
            if corr is None:return [None]*len(positions)
            term=q.target_weight*vi*vj*corr; marginal+=term
        covariance[p.candidate.security_id]=marginal; variance+=p.target_weight*marginal
    if variance<=0:return [None]*len(positions)
    return [p.target_weight*covariance[p.candidate.security_id]/variance for p in positions]


def construct_portfolio(candidates:list[Candidate],aum:Decimal,portfolio_type:str="BALANCED",correlations:dict[tuple[str,str],Decimal]|None=None,config:PortfolioConfig|None=None)->PortfolioResult:
    if aum<=0:raise ValueError("AUM must be positive")
    config=config or CONFIGS[portfolio_type]; correlations=correlations or {}; reasons=[]
    eligible=[]
    for c in candidates:
        _validate_candidate(c)
        failures=[]
        if c.validation_classification not in {"ROBUST","PROMISING_BUT_UNPROVEN"}:failures.append("MODEL_NOT_VALIDATED")
        if c.signal_state not in {"STRONG_BUY","BUY","ACCUMULATE"}:failures.append("SIGNAL_NOT_ELIGIBLE")
        if c.confidence<config.confidence_minimum:failures.append("CONFIDENCE_BELOW_MINIMUM")
        if c.expected_upside is None or c.estimated_downside is None:failures.append("VALUATION_UNAVAILABLE")
        if c.liquidity_capacity_value is None:failures.append("LIQUIDITY_CAPACITY_UNAVAILABLE")
        if c.exit_horizon_days is None or c.exit_horizon_days>config.max_liquidation_horizon:failures.append("LIQUIDATION_HORIZON_FAILED")
        if not c.thesis_reference:failures.append("THESIS_REFERENCE_MISSING")
        if c.governance_score is None or c.data_quality_score is None:failures.append("RISK_EVIDENCE_INCOMPLETE")
        if None in (c.government_exposure,c.commodity_exposure,c.fx_exposure):failures.append("MACRO_EXPOSURE_INCOMPLETE")
        if not c.factor_exposures:failures.append("FACTOR_EXPOSURE_INCOMPLETE")
        if failures:reasons.append(f"{c.ticker}:"+"|".join(failures))
        else:eligible.append(c)
    if not eligible:return PortfolioResult("DATA_INSUFFICIENT",(),D("1"),tuple(reasons or ["NO_ELIGIBLE_CANDIDATES"]),portfolio_metrics([],correlations))
    def desirability(c):
        payoff=c.expected_upside/(c.estimated_downside+D("0.01")); vol=c.volatility or D("1")
        return payoff*(c.confidence/D("100"))*min(D("1"),D("0.20")/max(vol,D("0.01")))
    ordered=sorted(eligible,key=lambda c:(-desirability(c),c.ticker)); positions=[]; sector_weights={}; factor_weights={}; gov=commodity=fx=D("0")
    for c in ordered:
        constraints={"SINGLE_NAME":config.single_name_cap,"LIQUIDITY":c.liquidity_capacity_value/aum}
        if c.free_float_maximum_value is not None:constraints["FREE_FLOAT"]=c.free_float_maximum_value/aum
        constraints["SECTOR"]=max(D("0"),config.sector_cap-sector_weights.get(c.sector,D("0")))
        if c.government_exposure is not None and c.government_exposure>0:constraints["GOVERNMENT_EXPOSURE"]=max(D("0"),(config.government_exposure_cap-gov)/c.government_exposure)
        if c.commodity_exposure is not None and c.commodity_exposure>0:constraints["COMMODITY_EXPOSURE"]=max(D("0"),(config.commodity_exposure_cap-commodity)/c.commodity_exposure)
        if c.fx_exposure is not None and c.fx_exposure>0:constraints["FX_EXPOSURE"]=max(D("0"),(config.fx_exposure_cap-fx)/c.fx_exposure)
        for factor,exposure in c.factor_exposures.items():
            if exposure>0:constraints[f"FACTOR:{factor}"]=max(D("0"),(config.factor_concentration_cap-factor_weights.get(factor,D("0")))/exposure)
        correlated=sum((p.target_weight for p in positions if abs(correlations.get((c.security_id,p.candidate.security_id),correlations.get((p.candidate.security_id,c.security_id),D("1"))))>=config.correlation_threshold),D("0"))
        constraints["CORRELATED_GROUP"]=max(D("0"),config.correlated_group_cap-correlated)
        constraints["REMAINING_CAPITAL"]=max(D("0"),D("1")-sum((p.target_weight for p in positions),D("0")))
        binding,maximum=min(constraints.items(),key=lambda item:(item[1],item[0])); target=max(D("0"),maximum)
        if target==0:reasons.append(f"{c.ticker}:NO_REMAINING_CONSTRAINT_CAPACITY");continue
        positions.append(Position(c,target,maximum,binding));sector_weights[c.sector]=sector_weights.get(c.sector,D("0"))+target
        gov+=target*(c.government_exposure or D("0"));commodity+=target*(c.commodity_exposure or D("0"));fx+=target*(c.fx_exposure or D("0"))
        for factor,exposure in c.factor_exposures.items():factor_weights[factor]=factor_weights.get(factor,D("0"))+target*exposure
    contributions=_risk_contributions(positions,correlations)
    positions=[Position(p.candidate,p.target_weight,p.maximum_weight,p.binding_constraint,r) for p,r in zip(positions,contributions)]
    cash=max(D("0"),D("1")-sum((p.target_weight for p in positions),D("0")))
    return PortfolioResult("CONSTRUCTED",tuple(positions),cash,tuple(reasons),portfolio_metrics(positions,correlations))


def portfolio_metrics(positions:list[Position],correlations:dict[tuple[str,str],Decimal]):
    def grouped(key):
        out={}
        for p in positions:out[key(p.candidate)]=out.get(key(p.candidate),D("0"))+p.target_weight
        return out
    sector=grouped(lambda c:c.sector) if positions else {}
    liquidity={"WITHIN_5_DAYS":D("0"),"6_TO_10_DAYS":D("0"),"OVER_10_DAYS":D("0"),"UNAVAILABLE":D("0")}
    for p in positions:
        h=p.candidate.exit_horizon_days; bucket="UNAVAILABLE" if h is None else "WITHIN_5_DAYS" if h<=5 else "6_TO_10_DAYS" if h<=10 else "OVER_10_DAYS";liquidity[bucket]+=p.target_weight
    factor={}
    for p in positions:
        for k,v in p.candidate.factor_exposures.items():factor[k]=factor.get(k,D("0"))+p.target_weight*v
    weighted=lambda field:sum((p.target_weight*(getattr(p.candidate,field) or D("0")) for p in positions),D("0"))
    concentration=sum((p.target_weight*p.target_weight for p in positions),D("0"))
    variance=D("0"); risk_available=bool(positions) and all(p.candidate.volatility is not None for p in positions) and all(p.candidate.security_id==q.candidate.security_id or (p.candidate.security_id,q.candidate.security_id) in correlations or (q.candidate.security_id,p.candidate.security_id) in correlations for p in positions for q in positions)
    if risk_available:
        for p in positions:
            for q in positions:
                corr=D("1") if p.candidate.security_id==q.candidate.security_id else correlations.get((p.candidate.security_id,q.candidate.security_id),correlations.get((q.candidate.security_id,p.candidate.security_id),D("0")))
                variance+=p.target_weight*q.target_weight*p.candidate.volatility*q.candidate.volatility*corr
    return {"sector_exposures":sector,"factor_exposures":factor,"liquidity_distribution":liquidity,"days_to_liquidate":{"weighted_average":sum((p.target_weight*p.candidate.exit_horizon_days for p in positions if p.candidate.exit_horizon_days is not None),D("0")) if positions else None},"fx_exposure":weighted("fx_exposure"),"commodity_exposure":weighted("commodity_exposure"),"government_linked_exposure":weighted("government_exposure"),"concentration_hhi":concentration,"historical_risk":{"volatility":variance.sqrt() if risk_available and variance>=0 else None,"status":"AVAILABLE" if risk_available else "UNAVAILABLE"}}


def run_sample_portfolios(database:Path,aums=(D("20000000"),D("1000000000"),D("20000000000")),as_of:date=date(2026,9,15)):
    output=[]
    with Repository(database) as repo:
        repo.initialize(); validation=repo.connection.execute("SELECT * FROM validation_runs ORDER BY created_at DESC LIMIT 1").fetchone(); classification=validation["classification"] if validation else "UNRELIABLE"
        rows=repo.connection.execute("SELECT DISTINCT s.security_id,h.identifier_value ticker,coalesce(i.sector,'UNKNOWN') sector FROM securities s JOIN issuers i USING(issuer_id) JOIN identifier_history h ON h.security_id=s.security_id AND h.identifier_type='TICKER' WHERE EXISTS(SELECT 1 FROM market_observations m WHERE m.security_id=s.security_id) ORDER BY ticker").fetchall();candidates=[]
        for row in rows:
            signal=repo.connection.execute("SELECT * FROM research_signals WHERE security_id=? ORDER BY generated_at DESC LIMIT 1",(row[0],)).fetchone();size=repo.connection.execute("SELECT * FROM position_sizing_records WHERE security_id=? ORDER BY created_at DESC LIMIT 1",(row[0],)).fetchone();liq=repo.connection.execute("SELECT * FROM liquidity_assessments WHERE security_id=? AND position_shares='10000' AND participation_rate='0.10' ORDER BY created_at DESC LIMIT 1",(row[0],)).fetchone();valuation=repo.connection.execute("SELECT * FROM valuation_records WHERE security_id=? ORDER BY created_at DESC LIMIT 1",(row[0],)).fetchone();execution=repo.connection.execute("SELECT * FROM execution_assessments WHERE security_id=? ORDER BY created_at DESC LIMIT 1",(row[0],)).fetchone()
            factors=json.loads(signal["factor_scores_json"]) if signal else {};dq=D(factors.get("Data Quality",{}).get("score")) if factors.get("Data Quality",{}).get("score") is not None else None
            capacity=D(size["final_position_value"]) if size and size["status"]=="AVAILABLE" else None; horizon=D(execution["estimated_execution_horizon_days"]) if execution and execution["estimated_execution_horizon_days"] else None
            candidates.append(Candidate(row[0],row[1],None,None,D(signal["confidence"]) if signal else D("0"),capacity,horizon,None,row[2],None,dq,None,None,None,None,{},signal["signal_id"] if signal else None,classification,signal["signal_state"] if signal else "DATA_INSUFFICIENT"))
        for kind in CONFIGS:
            for aum in aums:
                result=construct_portfolio(candidates,aum,kind);pid=str(uuid.uuid4());now=utc_now()
                repo.connection.execute("INSERT INTO portfolio_runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(pid,kind,as_of.isoformat(),str(aum),"UZS",result.status,str(result.cash_weight),json.dumps(asdict(CONFIGS[kind]),default=str,sort_keys=True),json.dumps(result.reasons),validation["validation_run_id"] if validation else None,MODEL_VERSION,now))
                for p in result.positions:repo.connection.execute("INSERT INTO portfolio_positions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),pid,p.candidate.security_id,p.candidate.ticker,str(p.target_weight),str(p.maximum_weight),p.binding_constraint,p.candidate.thesis_reference,json.dumps({"expected_upside":str(p.candidate.expected_upside),"estimated_downside":str(p.candidate.estimated_downside)}),str(p.candidate.confidence),str(p.candidate.liquidity_capacity_value),str(p.candidate.exit_horizon_days) if p.candidate.exit_horizon_days is not None else None,str(p.risk_contribution) if p.risk_contribution is not None else None,p.candidate.sector,json.dumps(p.candidate.factor_exposures,default=str),json.dumps({"government":p.candidate.government_exposure,"commodity":p.candidate.commodity_exposure,"fx":p.candidate.fx_exposure},default=str),json.dumps({"thesis":p.candidate.thesis_reference}),))
                for name,value in result.metrics.items():repo.connection.execute("INSERT INTO portfolio_metrics VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),pid,name,json.dumps(value,default=str,sort_keys=True),"AVAILABLE" if result.positions else "UNAVAILABLE","NO_ELIGIBLE_POSITIONS" if not result.positions else None))
                output.append({"portfolio_id":pid,"type":kind,"aum":aum,"result":result})
        repo.connection.commit();return output
