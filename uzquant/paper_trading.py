from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from .backtesting import CostModel, TradeBar, simulate_order
from .portfolio import CONFIGS
from .repository import Repository, utc_now

D=Decimal
MODEL_VERSION="prospective-shadow/1.0.0"
EXECUTION_VERSION="prospective-execution/1.0.0"
BLOCKING_PIPELINES={"security_master","market_data","financial_documents","financial_normalization","fundamentals","valuation","liquidity","factors","confidence","risk_gates","signals"}


@dataclass(frozen=True)
class AccountState:
    cash:Decimal
    shares:Decimal=D("0")
    cost_basis:Decimal=D("0")
    realized_pnl:Decimal=D("0")
    fees:Decimal=D("0")
    dividends:Decimal=D("0")


def apply_fill(state:AccountState,side:str,shares:Decimal,fill_price:Decimal,fees:Decimal)->AccountState:
    if shares<=0 or fill_price<=0 or fees<0 or side not in {"BUY","SELL"}: raise ValueError("invalid fill")
    gross=shares*fill_price
    if side=="BUY":
        if gross+fees>state.cash: raise ValueError("insufficient cash")
        return AccountState(state.cash-gross-fees,state.shares+shares,state.cost_basis+gross+fees,state.realized_pnl,state.fees+fees,state.dividends)
    if shares>state.shares: raise ValueError("insufficient shares")
    allocated=state.cost_basis*(shares/state.shares) if state.shares else D("0")
    return AccountState(state.cash+gross-fees,state.shares-shares,state.cost_basis-allocated,state.realized_pnl+gross-fees-allocated,state.fees+fees,state.dividends)


def apply_dividend(state:AccountState,dividend_per_share:Decimal,announcement:date,payment:date,known_at:datetime)->AccountState:
    if dividend_per_share<0 or payment<announcement: raise ValueError("invalid dividend")
    if announcement>known_at.date() or payment>known_at.date(): return state
    amount=state.shares*dividend_per_share
    return AccountState(state.cash+amount,state.shares,state.cost_basis,state.realized_pnl,state.fees,state.dividends+amount)


def execute_with_future_bars(side:str,shares:Decimal,submitted_at:datetime,bars:list[TradeBar],participation_rate:Decimal,costs:CostModel,max_fill_days:int=20):
    future=[bar for bar in bars if bar.trade_date>=submitted_at.date()]
    return simulate_order(side,shares,submitted_at.date(),future,participation_rate,costs,execution_delay_days=0,max_fill_days=max_fill_days)


def submit_paper_order(repo:Repository,portfolio_id:str,snapshot_id:str,security_id:str,side:str,shares:Decimal,participation_rate:Decimal,submitted_at:datetime,decision_price:Decimal|None=None):
    if submitted_at.tzinfo is None or shares<=0 or not D("0")<participation_rate<=D("1"): raise ValueError("invalid order")
    state=repo.connection.execute("SELECT * FROM prospective_security_states WHERE prospective_snapshot_id=? AND security_id=?",(snapshot_id,security_id)).fetchone()
    snapshot=repo.connection.execute("SELECT * FROM prospective_decision_snapshots WHERE prospective_snapshot_id=?",(snapshot_id,)).fetchone()
    if not state or not snapshot: raise ValueError("order must reference a captured prospective state")
    eligible=state["admission_status"]=="ELIGIBLE" and snapshot["upstream_state"]=="HEALTHY"
    status,reason=("OPEN",None) if eligible else ("REJECTED","PROSPECTIVE_ADMISSION_BLOCKED")
    versions=json.loads(state["model_versions_json"]); order_id=str(uuid.uuid4())
    repo.connection.execute("INSERT INTO paper_orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(order_id,portfolio_id,snapshot_id,security_id,state["signal_id"],submitted_at.isoformat(),side,str(shares),str(participation_rate),str(decision_price) if decision_price is not None else None,status,reason,json.dumps({"future_observations_only":True,"no_trade":"NO_FILL"},sort_keys=True),versions.get("model_version"),EXECUTION_VERSION,utc_now()))
    return order_id


def settle_paper_order(repo:Repository,order_id:str,as_of:datetime,costs:CostModel=CostModel(),max_fill_days:int=20):
    if as_of.tzinfo is None: raise ValueError("as_of must be timezone-aware")
    order=repo.connection.execute("SELECT * FROM paper_orders WHERE paper_order_id=?",(order_id,)).fetchone()
    if not order or order["status"]!="OPEN": raise ValueError("order is not open")
    submitted=datetime.fromisoformat(order["submitted_at"].replace("Z","+00:00"))
    if as_of<submitted: raise ValueError("cannot use future knowledge")
    rows=repo.connection.execute("SELECT * FROM market_observations WHERE security_id=? AND first_seen_at>? AND first_seen_at<=? AND trade_date>=? AND series_type='RAW_OBSERVED' ORDER BY trade_date,first_seen_at",(order["security_id"],order["submitted_at"],as_of.isoformat(),submitted.date().isoformat())).fetchall()
    bars=[]
    for row in rows:
        price=next((row[k] for k in ("individual_trade_price","last","close") if row[k] is not None),None)
        spread=(D(row["ask"])-D(row["bid"]))/D(price) if price is not None and row["bid"] is not None and row["ask"] is not None else None
        bars.append(TradeBar(row["observation_id"],date.fromisoformat(row["trade_date"]),D(price) if price is not None else None,D(row["share_volume"]) if row["share_volume"] is not None else None,row["observation_status"]=="TRADE_REPORTED",spread))
    result=execute_with_future_bars(order["side"],D(order["requested_shares"]),submitted,bars,D(order["participation_rate"]),costs,max_fill_days)
    status="NO_FILL" if not result.fills else result.status
    repo.connection.execute("UPDATE paper_orders SET status=?,reason=? WHERE paper_order_id=?",(status,result.reason,order_id))
    portfolio=repo.connection.execute("SELECT * FROM shadow_portfolios WHERE shadow_portfolio_id=?",(order["shadow_portfolio_id"],)).fetchone()
    position=repo.connection.execute("SELECT * FROM paper_positions WHERE shadow_portfolio_id=? AND security_id=?",(order["shadow_portfolio_id"],order["security_id"])).fetchone()
    state=AccountState(D(portfolio["current_cash"]),D(position["shares"]) if position else D("0"),D(position["cost_basis"]) if position else D("0"),D(position["realized_pnl"]) if position else D("0"),D(position["fees_paid"]) if position else D("0"),D(position["dividends_received"]) if position else D("0"))
    for fill in result.fills:
        total_fees=fill.transaction_fee+fill.broker_fee+fill.exchange_fee+fill.depository_fee
        state=apply_fill(state,order["side"],fill.shares,fill.fill_price,total_fees); fill_id=str(uuid.uuid4()); created=utc_now()
        source=next(r for r in rows if r["observation_id"]==fill.observation_id)
        repo.connection.execute("INSERT INTO paper_fills VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(fill_id,order_id,fill.observation_id,source["first_seen_at"],str(fill.shares),str(fill.reference_price),str(fill.fill_price),str(fill.shares*fill.fill_price),str(total_fees),str(fill.slippage_value),str(source["share_volume"]),order["participation_rate"],created))
        repo.connection.execute("INSERT INTO paper_portfolio_ledger VALUES(?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),order["shadow_portfolio_id"],source["first_seen_at"],"FILL",str(-(fill.shares*fill.fill_price+total_fees) if order["side"]=="BUY" else fill.shares*fill.fill_price-total_fees),str(state.cash),order["security_id"],fill_id,fill.observation_id,json.dumps({"side":order["side"],"reference_price":str(fill.reference_price),"slippage":str(fill.slippage_value)},sort_keys=True),created))
    if result.fills:
        repo.connection.execute("UPDATE shadow_portfolios SET current_cash=? WHERE shadow_portfolio_id=?",(str(state.cash),order["shadow_portfolio_id"]))
        repo.connection.execute("INSERT INTO paper_positions VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(shadow_portfolio_id,security_id) DO UPDATE SET shares=excluded.shares,cost_basis=excluded.cost_basis,realized_pnl=excluded.realized_pnl,dividends_received=excluded.dividends_received,fees_paid=excluded.fees_paid,updated_at=excluded.updated_at",(order["shadow_portfolio_id"],order["security_id"],str(state.shares),str(state.cost_basis),str(state.realized_pnl),str(state.dividends),str(state.fees),utc_now()))
    return result


def _ids(connection,sql,args=()): return [r[0] for r in connection.execute(sql,args)]


def _json_row(row): return {k:row[k] for k in row.keys()} if row else None


def capture_prospective_state(database:Path,decision_timestamp:datetime|None=None,initial_cash:Decimal=D("20000000")):
    decision_timestamp=decision_timestamp or datetime.now(timezone.utc)
    if decision_timestamp.tzinfo is None: raise ValueError("decision timestamp must be timezone-aware")
    stamp=decision_timestamp.isoformat(); day=decision_timestamp.date().isoformat(); created=utc_now()
    with Repository(database) as repo:
        repo.initialize(); c=repo.connection
        health=[dict(r) for r in c.execute("SELECT * FROM pipeline_health ORDER BY pipeline")]
        relevant=[r for r in health if r["pipeline"] in BLOCKING_PIPELINES]
        rank={"HEALTHY":0,"DEGRADED":1,"STALE":2,"FAILED":3}; upstream=max((r["status"] for r in relevant),key=lambda x:rank[x],default="STALE")
        blockers=[f"{r['pipeline']}:{r['status']}" for r in relevant if r["status"]!="HEALTHY"]
        universe=_ids(c,"SELECT DISTINCT security_id FROM securities ORDER BY security_id")
        market=_ids(c,"SELECT observation_id FROM market_observations WHERE first_seen_at<=? ORDER BY trade_date,observation_id",(stamp,))
        financials=_ids(c,"SELECT document_id FROM financial_documents WHERE publication_date<=? ORDER BY publication_date,document_id",(day,))
        valuations=_ids(c,"SELECT valuation_id FROM valuation_records WHERE valuation_date<=? AND created_at<=? ORDER BY created_at,valuation_id",(day,stamp))
        factors=_ids(c,"SELECT factor_score_id FROM factor_scores WHERE as_of_date<=? AND created_at<=? ORDER BY created_at,factor_score_id",(day,stamp))
        signals=_ids(c,"SELECT signal_id FROM research_signals WHERE generated_at<=? ORDER BY generated_at,signal_id",(stamp,))
        snapshot_id=str(uuid.uuid4())
        execution={"participation_rate":"0.10","max_fill_days":20,"future_observations_only":True,"spread":"ONLY_IF_OBSERVED","fees":"EXPLICIT_CONFIG_REQUIRED","no_trade":"NO_FILL"}
        versions={"snapshot":MODEL_VERSION,"portfolio":"transparent-portfolio/1.1.0","execution":EXECUTION_VERSION}
        c.execute("INSERT INTO prospective_decision_snapshots VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(snapshot_id,stamp,"INITIALIZATION",json.dumps(health,sort_keys=True),upstream,json.dumps(universe),json.dumps(market),json.dumps(financials),json.dumps(valuations),json.dumps(factors),json.dumps(signals),json.dumps({"initial_cash":str(initial_cash),"styles":list(CONFIGS)},sort_keys=True),json.dumps(execution,sort_keys=True),json.dumps(versions,sort_keys=True),json.dumps(sorted(set(market+financials+valuations+factors+signals))),created))
        captured=0
        for sid in universe:
            signal=c.execute("SELECT * FROM research_signals WHERE security_id=? AND generated_at<=? ORDER BY generated_at DESC,signal_id DESC LIMIT 1",(sid,stamp)).fetchone()
            if not signal: continue
            valuation=c.execute("SELECT * FROM valuation_records WHERE security_id=? AND valuation_date<=? AND created_at<=? ORDER BY created_at DESC LIMIT 1",(sid,day,stamp)).fetchone()
            liquidity=c.execute("SELECT * FROM liquidity_assessments WHERE security_id=? AND as_of_date<=? AND created_at<=? ORDER BY created_at DESC LIMIT 1",(sid,day,stamp)).fetchone()
            position=c.execute("SELECT * FROM position_sizing_records WHERE security_id=? AND as_of_date<=? AND created_at<=? ORDER BY created_at DESC LIMIT 1",(sid,day,stamp)).fetchone()
            observation=c.execute("SELECT * FROM market_observations WHERE security_id=? AND first_seen_at<=? ORDER BY trade_date DESC,first_seen_at DESC LIMIT 1",(sid,stamp)).fetchone()
            docs=[dict(r) for r in c.execute("SELECT document_id,publication_date,period_end,document_type,audit_status,reporting_perimeter FROM financial_documents WHERE issuer_id=(SELECT issuer_id FROM securities WHERE security_id=?) AND publication_date<=? ORDER BY publication_date DESC",(sid,day))]
            factor_rows=[dict(r) for r in c.execute("SELECT factor_name,score,status,transformation,factor_score_id FROM factor_scores WHERE security_id=? AND data_snapshot_id=? ORDER BY factor_name",(sid,signal["data_snapshot_id"]))]
            reasons=list(blockers)
            if signal["signal_state"] not in {"STRONG_BUY","BUY","ACCUMULATE"}: reasons.append("SIGNAL_NOT_ELIGIBLE")
            validation=c.execute("SELECT classification FROM validation_runs ORDER BY created_at DESC LIMIT 1").fetchone()
            if not validation or validation[0] not in {"ROBUST","PROMISING_BUT_UNPROVEN"}: reasons.append("MODEL_NOT_VALIDATED")
            if not valuation or valuation["status"]!="AVAILABLE": reasons.append("VALUATION_INSUFFICIENT")
            admission="STALE_BLOCKED" if blockers else "INELIGIBLE" if reasons else "ELIGIBLE"
            model_versions={k:signal[k] for k in ("model_version","scoring_version","valuation_version","liquidity_version")}
            values=(str(uuid.uuid4()),snapshot_id,sid,signal["signal_id"],valuation["valuation_id"] if valuation else None,liquidity["assessment_id"] if liquidity else None,signal["signal_state"],signal["confidence"],signal["triggered_gates_json"],json.dumps(_json_row(position),default=str,sort_keys=True),json.dumps(_json_row(observation),default=str,sort_keys=True),json.dumps(docs,default=str,sort_keys=True),json.dumps(_json_row(valuation),default=str,sort_keys=True),json.dumps(factor_rows,default=str,sort_keys=True),json.dumps(_json_row(liquidity),default=str,sort_keys=True),json.dumps(execution,sort_keys=True),json.dumps(model_versions,sort_keys=True),admission,json.dumps(sorted(set(reasons))))
            c.execute("INSERT INTO prospective_security_states VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",values)
            captured+=1
        portfolios=[]
        for style in CONFIGS:
            pid=str(uuid.uuid4()); status="ACTIVE" if upstream=="HEALTHY" else "DEGRADED"
            c.execute("INSERT INTO shadow_portfolios VALUES(?,?,?,?,?,?,?,?)",(pid,style,"UZS",str(initial_cash),str(initial_cash),status,"transparent-portfolio/1.1.0",created))
            c.execute("INSERT INTO paper_portfolio_ledger VALUES(?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),pid,stamp,"INITIAL_CASH",str(initial_cash),str(initial_cash),None,None,None,json.dumps({"snapshot_id":snapshot_id,"upstream_state":upstream},sort_keys=True),created));portfolios.append(pid)
        c.execute("INSERT INTO paper_drift_assessments VALUES(?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),stamp,captured,json.dumps({}),json.dumps({}),json.dumps({}),json.dumps({}),json.dumps({}),json.dumps({}),"INSUFFICIENT_SAMPLE",MODEL_VERSION))
        c.commit()
        return {"snapshot_id":snapshot_id,"timestamp":stamp,"upstream_state":upstream,"blockers":blockers,"shadow_portfolios":len(portfolios),"signals_captured":captured,"paper_orders":0,"fills":0,"no_fills":0,"cash_weight":"1","initial_cash":str(initial_cash)}
