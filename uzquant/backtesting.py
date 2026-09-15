from __future__ import annotations

import json
import math
import statistics
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from .repository import Repository, utc_now

D = Decimal
MODEL_VERSION = "pit-liquidity-backtest/1.0.0"
STRATEGIES = ("Equal Weight Universe","Value","Quality","Value + Quality","Top Overall Ranking","Overall Ranking + Liquidity Gates","Overall Ranking + Confidence Threshold")
METRICS = ("Total Return","CAGR","Volatility","Sharpe","Sortino","Maximum Drawdown","Calmar","Win Rate","Average Winner","Average Loser","Profit Factor","Turnover","Transaction Costs","Slippage","Average Holding Period","Liquidity-Adjusted Return","Capacity")


@dataclass(frozen=True)
class CostModel:
    transaction_fee_rate: Decimal = D("0")
    broker_fee_rate: Decimal = D("0")
    exchange_fee_rate: Decimal = D("0")
    depository_fee_rate: Decimal = D("0")
    slippage_rate: Decimal = D("0")


@dataclass(frozen=True)
class TradeBar:
    observation_id: str
    trade_date: date
    price: Decimal | None
    volume: Decimal | None
    is_trade: bool = True
    spread: Decimal | None = None


@dataclass(frozen=True)
class Fill:
    observation_id: str
    fill_date: date
    shares: Decimal
    reference_price: Decimal
    fill_price: Decimal
    transaction_fee: Decimal
    broker_fee: Decimal
    exchange_fee: Decimal
    depository_fee: Decimal
    slippage_value: Decimal


@dataclass(frozen=True)
class OrderResult:
    status: str
    requested_shares: Decimal
    filled_shares: Decimal
    unfilled_shares: Decimal
    fills: tuple[Fill, ...]
    reason: str | None


def records_known_as_of(records, as_of: datetime, known_field: str):
    return [record for record in records if datetime.fromisoformat(str(record[known_field]).replace("Z","+00:00")) <= as_of]


def financial_documents_as_of(records, as_of: date):
    eligible=[r for r in records if date.fromisoformat(r["publication_date"])<=as_of]
    latest={}
    for row in sorted(eligible,key=lambda r:(r["issuer_id"],r["period_end"],r["publication_date"])):
        latest[(row["issuer_id"],row["period_end"],row.get("reporting_perimeter"),row.get("accounting_standard"))]=row
    return list(latest.values())


def macro_vintages_as_of(records, as_of: datetime):
    eligible=records_known_as_of(records,as_of,"vintage_known_at"); latest={}
    for row in sorted(eligible,key=lambda r:(r["series_id"],r["period_start"],r["vintage_known_at"])):
        if date.fromisoformat(row["period_end"])<=as_of.date(): latest[(row["series_id"],row["period_start"],row["period_end"])]=row
    return list(latest.values())


def universe_as_of(listings, as_of: date):
    securities=set()
    for row in listings:
        known=date.fromisoformat(str(row["known_at"])[:10])
        listed=date.fromisoformat(row["listing_date"]) if row.get("listing_date") else None
        delisted=date.fromisoformat(row["delisting_date"]) if row.get("delisting_date") else None
        if known<=as_of and (listed is None or listed<=as_of) and (delisted is None or as_of<delisted): securities.add(row["security_id"])
    return securities


def simulate_order(side: str, shares: Decimal, signal_date: date, bars: list[TradeBar], participation_rate: Decimal, costs: CostModel, execution_delay_days: int = 1, max_fill_days: int = 20) -> OrderResult:
    if side not in {"BUY","SELL"}: raise ValueError("invalid side")
    if shares<=0 or not D("0")<participation_rate<=D("1") or execution_delay_days<0 or max_fill_days<1: raise ValueError("invalid order assumptions")
    eligible=[bar for bar in sorted(bars,key=lambda b:b.trade_date) if (bar.trade_date-signal_date).days>=execution_delay_days]
    remaining=shares; fills=[]; attempted=0
    for bar in eligible:
        if attempted>=max_fill_days or remaining<=0: break
        attempted+=1
        if not bar.is_trade or bar.price is None or bar.volume is None or bar.volume<=0: continue
        quantity=min(remaining,bar.volume*participation_rate)
        if quantity<=0: continue
        spread_half=(bar.spread or D("0"))/D("2")
        impact=spread_half+costs.slippage_rate
        fill_price=bar.price*(D("1")+impact if side=="BUY" else D("1")-impact)
        gross=quantity*fill_price
        fills.append(Fill(bar.observation_id,bar.trade_date,quantity,bar.price,fill_price,gross*costs.transaction_fee_rate,gross*costs.broker_fee_rate,gross*costs.exchange_fee_rate,gross*costs.depository_fee_rate,quantity*abs(fill_price-bar.price)))
        remaining-=quantity
    filled=shares-remaining
    if remaining==0: status,reason="FILLED",None
    elif filled>0: status,reason="PARTIALLY_FILLED","VOLUME_LIMIT_OR_WINDOW_EXHAUSTED"
    else: status,reason="REJECTED","NO_EXECUTABLE_OBSERVED_VOLUME"
    return OrderResult(status,shares,filled,remaining,tuple(fills),reason)


def verified_cash_dividend(shares: Decimal, dividend_per_share: Decimal, announcement_date: date, payment_date: date, decision_cutoff: date) -> Decimal:
    if announcement_date>decision_cutoff or payment_date<announcement_date: return D("0")
    return shares*dividend_per_share


def apply_verified_split(shares: Decimal, factor: Decimal | None, announcement_date: date, effective_date: date, decision_cutoff: date, verified: bool) -> Decimal:
    if not verified or factor is None or factor<=0 or announcement_date>decision_cutoff or effective_date<announcement_date: return shares
    return shares*factor


def delisting_outcome(shares: Decimal, verified_cash_per_share: Decimal | None):
    if verified_cash_per_share is None: return {"status":"UNRESOLVED_DELISTING","cash":None,"shares":shares}
    return {"status":"CASH_SETTLED","cash":shares*verified_cash_per_share,"shares":D("0")}


def persist_order_result(repo: Repository, backtest_run_id: str, snapshot_id: str | None,
                         security_id: str, signal_timestamp: datetime, side: str,
                         decision_price: Decimal | None, participation_rate: Decimal,
                         result: OrderResult) -> str:
    """Append a simulated order and its fills to the auditable ledger."""
    order_id=str(uuid.uuid4()); created=utc_now()
    status=result.status if result.status in {"FILLED","PARTIALLY_FILLED","REJECTED"} else "EXPIRED"
    repo.connection.execute("INSERT INTO backtest_orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(order_id,backtest_run_id,snapshot_id,security_id,signal_timestamp.isoformat(),side,str(result.requested_shares),str(decision_price) if decision_price is not None else None,str(participation_rate),status,result.reason,MODEL_VERSION,created))
    for fill in result.fills:
        observed=repo.connection.execute("SELECT share_volume FROM market_observations WHERE observation_id=?",(fill.observation_id,)).fetchone()
        if not observed or observed[0] is None: raise ValueError("fill lacks source volume observation")
        gross=fill.shares*fill.fill_price
        repo.connection.execute("INSERT INTO backtest_fills VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),order_id,fill.fill_date.isoformat(),str(fill.shares),str(fill.reference_price),str(fill.fill_price),str(gross),str(fill.transaction_fee),str(fill.broker_fee),str(fill.exchange_fee),str(fill.depository_fee),str(fill.slippage_value),str(observed[0]),str(participation_rate),fill.observation_id,created))
    return order_id


def performance_metrics(equity: list[tuple[date,Decimal]], completed_returns: list[Decimal], turnover: Decimal, costs: Decimal, slippage: Decimal, average_holding_days: Decimal | None, capacity: Decimal | None, periods_per_year: int=252, annual_risk_free_rate: Decimal | None=None):
    unavailable={name:None for name in METRICS}
    if len(equity)<2 or equity[0][1]<=0: return unavailable
    values=[x[1] for x in equity]; returns=[values[i]/values[i-1]-1 for i in range(1,len(values)) if values[i-1]>0]
    total=values[-1]/values[0]-1; years=max(D("1")/D(periods_per_year),D((equity[-1][0]-equity[0][0]).days)/D("365.25")); cagr=(D(str(float(values[-1]/values[0])**(1/float(years))))-1) if values[-1]>0 else None
    vol=D(str(statistics.stdev([float(r) for r in returns])*math.sqrt(periods_per_year))) if len(returns)>=2 else None
    mean=D(str(statistics.mean([float(r) for r in returns])*periods_per_year)) if returns else None
    excess=mean-annual_risk_free_rate if mean is not None and annual_risk_free_rate is not None else None
    sharpe=excess/vol if excess is not None and vol and vol>0 else None
    downside=[float(r) for r in returns if r<0]; downvol=D(str(statistics.stdev(downside)*math.sqrt(periods_per_year))) if len(downside)>=2 else None
    sortino=excess/downvol if excess is not None and downvol and downvol>0 else None
    peak=values[0]; maxdd=D("0")
    for value in values: peak=max(peak,value); maxdd=min(maxdd,value/peak-1)
    wins=[r for r in completed_returns if r>0]; losses=[r for r in completed_returns if r<0]
    profit=sum(wins,D("0")); loss=abs(sum(losses,D("0")))
    return {"Total Return":total,"CAGR":cagr,"Volatility":vol,"Sharpe":sharpe,"Sortino":sortino,"Maximum Drawdown":maxdd,"Calmar":cagr/abs(maxdd) if cagr is not None and maxdd<0 else None,"Win Rate":D(len(wins))/D(len(completed_returns)) if completed_returns else None,"Average Winner":sum(wins,D("0"))/len(wins) if wins else None,"Average Loser":sum(losses,D("0"))/len(losses) if losses else None,"Profit Factor":profit/loss if loss>0 else None,"Turnover":turnover,"Transaction Costs":costs,"Slippage":slippage,"Average Holding Period":average_holding_days,"Liquidity-Adjusted Return":total,"Capacity":capacity}


def build_database_snapshot(repo: Repository, decision_timestamp: datetime):
    stamp=decision_timestamp.isoformat(); day=decision_timestamp.date().isoformat()
    listings=[dict(r) for r in repo.connection.execute("SELECT * FROM listings")]; universe=universe_as_of(listings,decision_timestamp.date())
    if not universe: return {"universe":[],"identifiers":[],"prices":[],"financials":[],"ownership":[],"rights":[],"events":[],"actions":[],"dividends":[],"macro":[],"signals":[],"models":[]}
    placeholders=','.join('?'*len(universe)); ids=tuple(universe)
    def query(sql,args=()): return [r[0] for r in repo.connection.execute(sql,args)]
    identifiers=query(f"SELECT identifier_id FROM identifier_history WHERE security_id IN ({placeholders}) AND known_at<=? AND (valid_from IS NULL OR valid_from<=?) AND (valid_to IS NULL OR valid_to>?)",ids+(stamp,day,day))
    prices=query(f"SELECT observation_id FROM market_observations WHERE security_id IN ({placeholders}) AND trade_date<=? AND first_seen_at<=? AND series_type='RAW_OBSERVED'",ids+(day,stamp))
    issuers=query(f"SELECT DISTINCT issuer_id FROM securities WHERE security_id IN ({placeholders})",ids); ip=','.join('?'*len(issuers))
    financials=query(f"SELECT document_id FROM financial_documents WHERE issuer_id IN ({ip}) AND publication_date<=?",tuple(issuers)+(day,))
    ownership=query(f"SELECT ownership_id FROM ownership_positions WHERE issuer_id IN ({ip}) AND disclosure_date<=?",tuple(issuers)+(day,))
    rights=query(f"SELECT rights_id FROM security_rights WHERE security_id IN ({placeholders}) AND disclosure_date<=?",ids+(day,))
    events=query(f"SELECT event_id FROM research_events WHERE issuer_id IN ({ip}) AND publication_at<=?",tuple(issuers)+(stamp,))
    actions=query(f"SELECT action_id FROM corporate_actions WHERE issuer_id IN ({ip}) AND announcement_date<=?",tuple(issuers)+(day,))
    dividends=query(f"SELECT dividend_id FROM dividends WHERE security_id IN ({placeholders}) AND announcement_date<=?",ids+(day,))
    macro=query("SELECT observation_id FROM macro_observations WHERE vintage_known_at<=? AND period_end<=?",(stamp,day))
    signals=query(f"SELECT signal_id FROM research_signals WHERE security_id IN ({placeholders}) AND generated_at<=?",ids+(stamp,))
    models=query(f"SELECT DISTINCT model_version FROM research_signals WHERE security_id IN ({placeholders}) AND generated_at<=?",ids+(stamp,))
    return {"universe":sorted(universe),"identifiers":identifiers,"prices":prices,"financials":financials,"ownership":ownership,"rights":rights,"events":events,"actions":actions,"dividends":dividends,"macro":macro,"signals":signals,"models":models}


def readiness(repo: Repository):
    dates=[r[0] for r in repo.connection.execute("SELECT DISTINCT trade_date FROM market_observations WHERE series_type='RAW_OBSERVED' ORDER BY trade_date")]
    signal_dates=[r[0] for r in repo.connection.execute("SELECT DISTINCT substr(generated_at,1,10) FROM research_signals ORDER BY generated_at")]
    known_dates=[r[0][:10] for r in repo.connection.execute("SELECT DISTINCT known_at FROM listings")]
    reasons=[]
    if len(dates)<60: reasons.append("FEWER_THAN_60_MARKET_DATES")
    if len(signal_dates)<2: reasons.append("NO_HISTORICAL_SIGNAL_SEQUENCE")
    if len(known_dates)<2: reasons.append("NO_HISTORICAL_UNIVERSE_SNAPSHOTS")
    if not repo.connection.execute("SELECT 1 FROM market_observations WHERE series_type='TOTAL_RETURN' LIMIT 1").fetchone(): reasons.append("NO_VERIFIED_TOTAL_RETURN_SERIES")
    reasons.append("NO_VERIFIED_HISTORICAL_BENCHMARK_SERIES")
    return reasons


def run_backtest_readiness(database: Path, initial_capital: Decimal=D("1000000000")):
    output=[]
    with Repository(database) as repo:
        repo.initialize(); reasons=readiness(repo); dates=[r[0] for r in repo.connection.execute("SELECT DISTINCT trade_date FROM market_observations ORDER BY trade_date")]
        for strategy in STRATEGIES:
            run_id=str(uuid.uuid4()); now=utc_now(); assumptions={"participation_rate":"0.10","execution_delay_days":1,"max_fill_days":20,"fee_inputs":"UNVERIFIED_CURRENTLY_NO_PERFORMANCE_RUN","anti_leakage":"STRICT","model_version":MODEL_VERSION}
            repo.connection.execute("INSERT INTO backtest_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)",(run_id,strategy,min(dates) if dates else None,max(dates) if dates else None,str(initial_capital),"UZS","DATA_INSUFFICIENT",json.dumps(assumptions,sort_keys=True),json.dumps(reasons),MODEL_VERSION,now))
            for metric in METRICS: repo.connection.execute("INSERT INTO backtest_metrics VALUES(?,?,?,?,?,?)",(str(uuid.uuid4()),run_id,metric,None,"UNAVAILABLE","BACKTEST_DATA_INSUFFICIENT"))
            output.append({"run_id":run_id,"strategy":strategy,"status":"DATA_INSUFFICIENT","reasons":reasons,"start_date":min(dates) if dates else None,"end_date":max(dates) if dates else None})
        repo.connection.commit()
    return output
