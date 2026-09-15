from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

from .liquidity import LiquidityFeatures, assess_capacity
from .repository import Repository, utc_now

D = Decimal
MODEL_VERSION = "execution-intelligence/1.0.0"
INTRADAY_UNRELIABLE = "INTRADAY_TIMING_NOT_RELIABLE"
CANNOT_ESTIMATE = "CANNOT_ESTIMATE_EXECUTION_RELIABLY"


@dataclass(frozen=True)
class ExecutionConfig:
    investable_participation: Decimal = D("0.10")
    limited_participation: Decimal = D("0.05")
    high_risk_participation: Decimal = D("0.02")
    minimum_intraday_trade_days: int = 60
    wide_spread: Decimal = D("0.10")


@dataclass(frozen=True)
class ExecutionInputs:
    proposed_shares: Decimal
    side: str
    security_class: str
    liquidity_state: str | None
    features: LiquidityFeatures
    mark_price: Decimal | None
    bid: Decimal | None = None
    ask: Decimal | None = None
    intraday_trade_days: int = 0
    intraday_pattern_robust: bool = False
    price_limit_active: bool | None = None
    entry_low: Decimal | None = None
    entry_high: Decimal | None = None


@dataclass(frozen=True)
class ExecutionResult:
    status: str
    preferred_execution_style: str
    maximum_suggested_child_order: Decimal | None
    maximum_participation_rate: Decimal
    estimated_execution_horizon_days: Decimal | None
    acceptable_entry_low: Decimal | None
    acceptable_entry_high: Decimal | None
    expected_slippage_low: Decimal | None
    expected_slippage_high: Decimal | None
    execution_confidence: str
    intraday_timing_status: str
    flags: tuple[str, ...]
    uncertainty: tuple[str, ...]


def partial_fill_schedule(order_shares: Decimal, daily_capacity: Decimal | None) -> tuple[Decimal, ...]:
    if order_shares < 0 or daily_capacity is not None and daily_capacity <= 0:
        raise ValueError("invalid order or daily capacity")
    if order_shares == 0: return ()
    if daily_capacity is None: return ()
    remaining, fills = order_shares, []
    while remaining > 0:
        fill = min(remaining, daily_capacity); fills.append(fill); remaining -= fill
    return tuple(fills)


def assess_execution(inputs: ExecutionInputs, config: ExecutionConfig = ExecutionConfig()) -> ExecutionResult:
    if inputs.proposed_shares <= 0: raise ValueError("proposed shares must be positive")
    if inputs.side not in {"ENTER", "EXIT"}: raise ValueError("side must be ENTER or EXIT")
    if (inputs.bid is None) != (inputs.ask is None): raise ValueError("bid and ask must be provided together")
    if inputs.bid is not None and (inputs.bid <= 0 or inputs.ask < inputs.bid): raise ValueError("invalid market quote")
    flags, uncertainty = [], []
    participation = {"INVESTABLE":config.investable_participation,"LIMITED_LIQUIDITY":config.limited_participation,"HIGH_LIQUIDITY_RISK":config.high_risk_participation,"LIQUIDITY_TRAP":D("0"),"UNASSESSABLE":D("0")}.get(inputs.liquidity_state, D("0"))
    adv = inputs.features.average_daily_share_volume
    daily_capacity = adv * participation if adv is not None and adv > 0 and participation > 0 else None
    horizon = (inputs.proposed_shares / daily_capacity).to_integral_value(rounding=ROUND_CEILING) if daily_capacity is not None else None
    if inputs.features.observation_count == 0 or inputs.features.trading_frequency in (None, D("0")):
        flags.append("ZERO_OR_UNKNOWN_TRADING_FREQUENCY")
    if inputs.liquidity_state in {None,"LIQUIDITY_TRAP","UNASSESSABLE"}:
        flags.append("CRITICAL_LIQUIDITY_FAILURE")
    spread = None
    if inputs.bid is not None:
        spread = (inputs.ask-inputs.bid)/((inputs.ask+inputs.bid)/D("2"))
        if spread >= config.wide_spread: flags.append("VERY_WIDE_SPREAD")
    else:
        uncertainty.append("ORDER_BOOK_AND_SPREAD_UNAVAILABLE")
    if inputs.features.depth_shares is None:
        uncertainty.append("DEPTH_UNAVAILABLE")
    if inputs.price_limit_active is True:
        flags.append("PRICE_LIMIT_ACTIVE")
    elif inputs.price_limit_active is None:
        uncertainty.append("PRICE_LIMIT_STATUS_UNAVAILABLE")
    intraday_ok = inputs.intraday_trade_days >= config.minimum_intraday_trade_days and inputs.intraday_pattern_robust and inputs.features.trading_frequency is not None and inputs.features.trading_frequency >= D("0.8")
    intraday_status = "INTRADAY_TIMING_SUPPORTED" if intraday_ok else INTRADAY_UNRELIABLE
    if not intraday_ok: uncertainty.append("NO_ROBUST_INTRADAY_HISTORY")
    child = None
    if daily_capacity is not None and inputs.features.depth_shares is not None:
        child = min(daily_capacity, inputs.features.depth_shares)
    else:
        uncertainty.append("CHILD_ORDER_SIZE_NOT_ESTIMABLE")
    acceptable_low = acceptable_high = None
    if inputs.entry_low is not None and inputs.entry_high is not None and inputs.bid is not None:
        acceptable_low, acceptable_high = inputs.entry_low, min(inputs.entry_high, inputs.ask)
        if acceptable_low > acceptable_high: acceptable_low = acceptable_high = None; flags.append("NO_ACCEPTABLE_QUOTED_ENTRY_RANGE")
    else:
        uncertainty.append("ACCEPTABLE_ENTRY_RANGE_UNAVAILABLE")
    capacity = assess_capacity(inputs.features, inputs.proposed_shares, inputs.mark_price, participation if participation > 0 else D("0.01"))
    slippage_low, slippage_high = capacity.expected_slippage_low, capacity.expected_slippage_high
    cannot = "CRITICAL_LIQUIDITY_FAILURE" in flags or "ZERO_OR_UNKNOWN_TRADING_FREQUENCY" in flags or inputs.mark_price is None
    if cannot:
        return ExecutionResult(CANNOT_ESTIMATE, "NO_EXECUTION_ESTIMATE", child, participation, horizon, acceptable_low, acceptable_high, None, None, "LOW", intraday_status, tuple(flags), tuple(dict.fromkeys(uncertainty)))
    if "PRICE_LIMIT_ACTIVE" in flags:
        style = "WAIT_OR_LIMIT_ORDER_AFTER_VENUE_RULE_VERIFICATION"
    elif spread is not None and spread >= config.wide_spread:
        style = "PATIENT_LIMIT_ORDER_NO_FILL_ASSUMPTION"
    elif inputs.features.depth_shares is None:
        style = "DAILY_PARTICIPATION_SCHEDULE_LIMIT_ORDER_IF_SUPPORTED"
    else:
        style = "LIMIT_ORDER_WITH_CHILD_ORDERS"
    confidence = "LOW" if uncertainty or (horizon is not None and horizon > 5) else "MEDIUM"
    return ExecutionResult("ESTIMATE_AVAILABLE", style, child, participation, horizon, acceptable_low, acceptable_high, slippage_low, slippage_high, confidence, intraday_status, tuple(flags), tuple(dict.fromkeys(uncertainty)))


def run_real_execution_cases(database: Path, proposed_shares: Decimal = D("10000"), as_of: date = date(2026,9,15)):
    tickers=("AGMK","AGMKP","KASU","KASUP","IPKY","UZTL","QZSM"); output=[]
    with Repository(database) as repo:
        repo.initialize()
        securities=repo.connection.execute("SELECT DISTINCT s.security_id,s.security_class_code,h.identifier_value ticker FROM securities s JOIN identifier_history h ON h.security_id=s.security_id AND h.identifier_type='TICKER' WHERE h.identifier_value IN (?,?,?,?,?,?,?) ORDER BY ticker",tickers).fetchall()
        for sec in securities:
            sid,security_class,ticker=sec
            liq=repo.connection.execute("SELECT * FROM liquidity_assessments WHERE security_id=? AND as_of_date<=? AND position_shares='10000' AND participation_rate='0.10' ORDER BY created_at DESC LIMIT 1",(sid,as_of.isoformat())).fetchone()
            rows=repo.connection.execute("SELECT * FROM market_observations WHERE security_id=? AND trade_date<=? AND series_type='RAW_OBSERVED' ORDER BY trade_date",(sid,as_of.isoformat())).fetchall()
            feature_data=json.loads(liq["features_json"]) if liq else {}
            features=LiquidityFeatures(**{key:(D(value) if value is not None and key not in {"observation_count","days_since_last_trade","calendar_basis"} else value) for key,value in feature_data.items()},source_observation_ids=tuple(r["observation_id"] for r in rows)) if liq else LiquidityFeatures(0,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,"UNAVAILABLE")
            traded=[r for r in rows if r["observation_status"]=="TRADE_REPORTED"]
            mark=D(traded[-1]["close"]) if traded and traded[-1]["close"] is not None else None
            entry=repo.connection.execute("SELECT * FROM entry_zone_records WHERE security_id=? AND as_of_date<=? ORDER BY created_at DESC LIMIT 1",(sid,as_of.isoformat())).fetchone()
            entry_low=D(entry["strong_buy_upper"]) if entry and entry["strong_buy_upper"] else None; entry_high=D(entry["accumulate_upper"]) if entry and entry["accumulate_upper"] else None
            inputs=ExecutionInputs(proposed_shares,"ENTER",security_class,liq["liquidity_state"] if liq else None,features,mark,None,None,0,False,None,entry_low,entry_high)
            result=assess_execution(inputs)
            eid=str(uuid.uuid4()); now=utc_now()
            repo.connection.execute("INSERT INTO execution_assessments VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(eid,sid,as_of.isoformat(),inputs.side,str(proposed_shares),result.preferred_execution_style,str(result.maximum_suggested_child_order) if result.maximum_suggested_child_order is not None else None,str(result.maximum_participation_rate),str(result.estimated_execution_horizon_days) if result.estimated_execution_horizon_days is not None else None,str(result.acceptable_entry_low) if result.acceptable_entry_low is not None else None,str(result.acceptable_entry_high) if result.acceptable_entry_high is not None else None,str(result.expected_slippage_low) if result.expected_slippage_low is not None else None,str(result.expected_slippage_high) if result.expected_slippage_high is not None else None,result.execution_confidence,result.intraday_timing_status,result.status,json.dumps(result.flags),json.dumps(result.uncertainty),json.dumps(asdict(ExecutionConfig()),default=str,sort_keys=True),json.dumps(features.source_observation_ids),liq["assessment_id"] if liq else None,entry["entry_zone_id"] if entry else None,MODEL_VERSION,now))
            output.append({"ticker":ticker,"security_class":security_class,"result":result,"mark_price":mark,"adv":features.average_daily_share_volume,"trade_frequency":features.trading_frequency})
        repo.connection.commit()
    return output
