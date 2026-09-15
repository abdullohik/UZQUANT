from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .repository import Repository, stable_id, utc_now

D = Decimal
MODEL_VERSION = "liquidity-capacity/1.0.0"
THRESHOLD_VERSION = "uzse-provisional/1.0.0"
STATES = ("INVESTABLE", "LIMITED_LIQUIDITY", "HIGH_LIQUIDITY_RISK", "LIQUIDITY_TRAP", "UNASSESSABLE")


@dataclass(frozen=True)
class Thresholds:
    status: str = "PROVISIONAL"
    very_low_adv_shares: Decimal = D("1000")
    stale_days: int = 5
    extreme_stale_days: int = 20
    zero_volume_dominance: Decimal = D("0.80")
    limited_horizon_days: Decimal = D("5")
    high_risk_horizon_days: Decimal = D("20")
    trap_horizon_days: Decimal = D("100")
    very_wide_spread: Decimal = D("0.10")
    tiny_free_float: Decimal = D("0.05")
    extreme_ownership_concentration: Decimal = D("0.90")


@dataclass(frozen=True)
class LiquidityFeatures:
    observation_count: int
    average_daily_share_volume: Decimal | None
    median_daily_share_volume: Decimal | None
    average_daily_trading_value: Decimal | None
    median_daily_trading_value: Decimal | None
    trading_frequency: Decimal | None
    zero_trade_day_ratio: Decimal | None
    average_trade_count: Decimal | None
    median_trade_count: Decimal | None
    bid_ask_spread: Decimal | None
    depth_shares: Decimal | None
    days_since_last_trade: int | None
    free_float: Decimal | None
    free_float_turnover: Decimal | None
    ownership_concentration: Decimal | None
    observed_daily_volatility: Decimal | None
    calendar_basis: str
    source_observation_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapacityResult:
    mark_to_market_value: Decimal | None
    position_value_to_adv: Decimal | None
    liquidation_horizon_days: Decimal | None
    estimated_realizable_value_low: Decimal | None
    estimated_realizable_value_high: Decimal | None
    expected_slippage_low: Decimal | None
    expected_slippage_high: Decimal | None
    liquidity_state: str
    liquidity_confidence: str
    hard_flags: tuple[str, ...]
    uncertainty: tuple[str, ...]


def _avg(values): return sum(values, D("0")) / len(values) if values else None
def _median(values): return D(str(statistics.median(values))) if values else None


def calculate_features(rows: list[dict], as_of: date,
                       free_float: Decimal | None = None,
                       ownership_concentration: Decimal | None = None) -> LiquidityFeatures:
    ordered = sorted(rows, key=lambda r: r["trade_date"])
    volumes = [D(str(r["share_volume"])) for r in ordered if r.get("share_volume") is not None]
    turnovers = [D(str(r["turnover_value"])) for r in ordered if r.get("turnover_value") is not None]
    counts = [D(str(r["trade_count"])) for r in ordered if r.get("trade_count") is not None]
    traded = [r for r in ordered if r.get("observation_status", "TRADE_REPORTED") == "TRADE_REPORTED"]
    frequency = D(len(traded)) / D(len(ordered)) if ordered else None
    zero_ratio = D(len(ordered) - len(traded)) / D(len(ordered)) if ordered else None
    last_trade = date.fromisoformat(traded[-1]["trade_date"]) if traded else None
    days_since = (as_of - last_trade).days if last_trade else None
    latest = traded[-1] if traded else (ordered[-1] if ordered else {})
    bid = D(str(latest["bid"])) if latest.get("bid") is not None else None
    ask = D(str(latest["ask"])) if latest.get("ask") is not None else None
    spread = (ask - bid) / ((ask + bid) / D("2")) if bid and ask and ask >= bid else None
    depth = None
    if latest.get("bid_size") is not None and latest.get("ask_size") is not None:
        depth = D(str(latest["bid_size"])) + D(str(latest["ask_size"]))
    closes = [D(str(r["close"])) for r in traded if r.get("close") is not None]
    returns = [float(closes[i] / closes[i-1] - 1) for i in range(1, len(closes)) if closes[i-1] > 0]
    volatility = D(str(statistics.stdev(returns))) if len(returns) >= 2 else None
    adv = _avg(volumes)
    fft = adv / free_float if adv is not None and free_float and free_float > 0 else None
    basis = "SOURCE_REPORTED_DATES" if ordered else "UNAVAILABLE"
    return LiquidityFeatures(len(ordered), adv, _median(volumes), _avg(turnovers), _median(turnovers),
        frequency, zero_ratio, _avg(counts), _median(counts), spread, depth, days_since,
        free_float, fft, ownership_concentration, volatility, basis,
        tuple(str(r["observation_id"]) for r in ordered if r.get("observation_id")))


def liquidation_horizon(position_shares: Decimal, adv_shares: Decimal | None,
                        participation_rate: Decimal) -> Decimal | None:
    if position_shares < 0 or participation_rate <= 0 or participation_rate > 1:
        raise ValueError("invalid position or participation rate")
    if adv_shares is None or adv_shares <= 0:
        return None
    return position_shares / (adv_shares * participation_rate)


def assess_capacity(features: LiquidityFeatures, position_shares: Decimal,
                    mark_price: Decimal | None, participation_rate: Decimal,
                    thresholds: Thresholds = Thresholds(),
                    single_trade_price_move: bool = False) -> CapacityResult:
    if position_shares < 0 or mark_price is not None and mark_price <= 0:
        raise ValueError("invalid position or mark price")
    horizon = liquidation_horizon(position_shares, features.average_daily_share_volume, participation_rate)
    mtm = position_shares * mark_price if mark_price is not None else None
    value_to_adv = None
    if features.average_daily_trading_value and mtm is not None:
        value_to_adv = mtm / features.average_daily_trading_value
    flags = []
    if features.average_daily_share_volume is not None and features.average_daily_share_volume <= thresholds.very_low_adv_shares: flags.append("VERY_LOW_ADV")
    if features.days_since_last_trade is None or features.days_since_last_trade >= thresholds.extreme_stale_days: flags.append("EXTREME_STALENESS")
    if features.zero_trade_day_ratio is not None and features.zero_trade_day_ratio >= thresholds.zero_volume_dominance: flags.append("ZERO_VOLUME_DOMINANCE")
    if features.free_float is not None and features.free_float <= thresholds.tiny_free_float: flags.append("TINY_FREE_FLOAT")
    if features.ownership_concentration is not None and features.ownership_concentration >= thresholds.extreme_ownership_concentration: flags.append("EXTREME_OWNERSHIP_CONCENTRATION")
    if features.bid_ask_spread is not None and features.bid_ask_spread >= thresholds.very_wide_spread: flags.append("VERY_WIDE_SPREAD")
    if single_trade_price_move: flags.append("SINGLE_TRADE_PRICE_MOVE")
    if horizon is None and position_shares > 0 or horizon is not None and horizon > thresholds.high_risk_horizon_days: flags.append("POSITION_EXCEEDS_CAPACITY")
    if "EXTREME_STALENESS" in flags or "SINGLE_TRADE_PRICE_MOVE" in flags: flags.append("UNRELIABLE_LAST_PRICE")

    uncertainty = []
    if features.depth_shares is None: uncertainty.append("ORDER_BOOK_DEPTH_UNAVAILABLE")
    if features.bid_ask_spread is None: uncertainty.append("BID_ASK_SPREAD_UNAVAILABLE")
    if features.free_float is None: uncertainty.append("FREE_FLOAT_UNAVAILABLE")
    if features.ownership_concentration is None: uncertainty.append("OWNERSHIP_CONCENTRATION_UNAVAILABLE")
    if features.average_daily_trading_value is None: uncertainty.append("TRADING_VALUE_ADV_UNAVAILABLE")
    if features.average_trade_count is None: uncertainty.append("TRADE_COUNT_UNAVAILABLE")
    if features.observation_count < 60: uncertainty.append("SHORT_OBSERVATION_WINDOW")

    slippage_low = slippage_high = erv_low = erv_high = None
    if mtm is not None and horizon is not None:
        spread_half = features.bid_ask_spread / D("2") if features.bid_ask_spread is not None else D("0")
        capacity_component = min(D("0.25"), horizon * participation_rate * D("0.005"))
        slippage_low = max(spread_half, capacity_component)
        volatility = features.observed_daily_volatility or D("0")
        missing_depth_penalty = D("0.05") if features.depth_shares is None else D("0")
        missing_spread_penalty = D("0.05") if features.bid_ask_spread is None else D("0")
        slippage_high = min(D("0.90"), slippage_low + D("2") * volatility + missing_depth_penalty + missing_spread_penalty)
        erv_low, erv_high = mtm * (D("1") - slippage_high), mtm * (D("1") - slippage_low)

    if mark_price is None:
        state = "UNASSESSABLE"
    elif "ZERO_VOLUME_DOMINANCE" in flags or "EXTREME_STALENESS" in flags or (horizon is not None and horizon > thresholds.trap_horizon_days):
        state = "LIQUIDITY_TRAP"
    elif horizon is None or horizon > thresholds.high_risk_horizon_days:
        state = "HIGH_LIQUIDITY_RISK"
    elif horizon > thresholds.limited_horizon_days or "VERY_WIDE_SPREAD" in flags:
        state = "LIMITED_LIQUIDITY"
    else:
        state = "INVESTABLE"
    confidence = "LOW" if uncertainty else "HIGH"
    if len(uncertainty) in range(1, 3): confidence = "MEDIUM"
    return CapacityResult(mtm, value_to_adv, horizon, erv_low, erv_high, slippage_low,
                          slippage_high, state, confidence, tuple(dict.fromkeys(flags)), tuple(uncertainty))


def _latest_mark(rows):
    traded = [r for r in rows if r["observation_status"] == "TRADE_REPORTED" and r["close"] is not None]
    return D(traded[-1]["close"]) if traded else None


def run_liquidity_assessments(database: Path, as_of: date = date(2026, 9, 15),
                              position_shares: Decimal = D("10000"),
                              participation_rate: Decimal = D("0.10")):
    with Repository(database) as repo:
        repo.initialize()
        tickers = ("AGMK", "AGMKP", "KASU", "KASUP", "IPKY", "UZTL", "QZSM")
        securities = repo.connection.execute("SELECT DISTINCT h.identifier_value,s.security_id FROM identifier_history h JOIN securities s ON s.security_id=h.security_id WHERE h.identifier_type='TICKER' AND h.identifier_value IN (?,?,?,?,?,?,?)", tickers).fetchall()
        output = []
        positive_advs = []
        for ticker, security_id in securities:
            dbrows = repo.connection.execute("SELECT * FROM market_observations WHERE security_id=? AND series_type='RAW_OBSERVED' AND trade_date<=? ORDER BY trade_date", (security_id, as_of.isoformat())).fetchall()
            rows = [dict(r) for r in dbrows]
            features = calculate_features(rows, as_of)
            if features.average_daily_share_volume and features.average_daily_share_volume > 0: positive_advs.append(features.average_daily_share_volume)
            single = bool(repo.connection.execute("SELECT 1 FROM market_quality_flags WHERE security_id=? AND flag_type='SINGLE_TRADE_MOVE' AND (trade_date IS NULL OR trade_date<=?) LIMIT 1", (security_id, as_of.isoformat())).fetchone())
            result = assess_capacity(features, position_shares, _latest_mark(rows), participation_rate, single_trade_price_move=single)
            aid = stable_id("liquidity", f"{security_id}:{as_of}:{position_shares}:{participation_rate}:{MODEL_VERSION}")
            assumptions = {"threshold_status":"PROVISIONAL","threshold_version":THRESHOLD_VERSION,"position_basis":"HYPOTHETICAL_STANDARDIZED_CASE","participation_rate":str(participation_rate),"slippage_model":"PROVISIONAL_UNCERTAINTY_BAND_NOT_PRECISE_IMPACT"}
            repo.connection.execute("INSERT INTO liquidity_assessments(assessment_id,security_id,as_of_date,data_cutoff_date,position_shares,participation_rate,mark_price,mark_to_market_value,estimated_realizable_value_low,estimated_realizable_value_high,slippage_low,slippage_high,liquidation_horizon_days,liquidity_state,liquidity_confidence,hard_flags_json,features_json,assumptions_json,uncertainty_json,source_observation_ids_json,liquidity_model_version,created_at,position_value_to_adv) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(security_id,as_of_date,position_shares,participation_rate,liquidity_model_version) DO UPDATE SET mark_price=excluded.mark_price,mark_to_market_value=excluded.mark_to_market_value,estimated_realizable_value_low=excluded.estimated_realizable_value_low,estimated_realizable_value_high=excluded.estimated_realizable_value_high,slippage_low=excluded.slippage_low,slippage_high=excluded.slippage_high,liquidation_horizon_days=excluded.liquidation_horizon_days,liquidity_state=excluded.liquidity_state,liquidity_confidence=excluded.liquidity_confidence,hard_flags_json=excluded.hard_flags_json,features_json=excluded.features_json,uncertainty_json=excluded.uncertainty_json,position_value_to_adv=excluded.position_value_to_adv,created_at=excluded.created_at", (aid,security_id,as_of.isoformat(),as_of.isoformat(),str(position_shares),str(participation_rate),str(_latest_mark(rows)) if _latest_mark(rows) is not None else None,str(result.mark_to_market_value) if result.mark_to_market_value is not None else None,str(result.estimated_realizable_value_low) if result.estimated_realizable_value_low is not None else None,str(result.estimated_realizable_value_high) if result.estimated_realizable_value_high is not None else None,str(result.expected_slippage_low) if result.expected_slippage_low is not None else None,str(result.expected_slippage_high) if result.expected_slippage_high is not None else None,str(result.liquidation_horizon_days) if result.liquidation_horizon_days is not None else None,result.liquidity_state,result.liquidity_confidence,json.dumps(result.hard_flags),json.dumps({k:(str(v) if isinstance(v,D) else v) for k,v in asdict(features).items() if k!="source_observation_ids"},sort_keys=True),json.dumps(assumptions,sort_keys=True),json.dumps(result.uncertainty),json.dumps(features.source_observation_ids),MODEL_VERSION,utc_now(),str(result.position_value_to_adv) if result.position_value_to_adv is not None else None))
            output.append({"ticker":ticker,"security_id":security_id,"features":features,"result":result,"mark_price":_latest_mark(rows)})
        distribution = {"positive_adv_min":str(min(positive_advs)) if positive_advs else None,"positive_adv_median":str(_median(positive_advs)) if positive_advs else None,"positive_adv_max":str(max(positive_advs)) if positive_advs else None,"zero_adv_count":len(securities)-len(positive_advs)}
        thresholds = Thresholds()
        repo.connection.execute("INSERT INTO liquidity_threshold_versions VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(threshold_version) DO UPDATE SET universe_size=excluded.universe_size,empirical_distribution_json=excluded.empirical_distribution_json,created_at=excluded.created_at", (THRESHOLD_VERSION,as_of.isoformat(),"PROVISIONAL",len(securities),json.dumps({k:str(v) if isinstance(v,D) else v for k,v in asdict(thresholds).items()},sort_keys=True),json.dumps(distribution,sort_keys=True),"Initial local thresholds reflect the seven-security verified sample and its natural ADV gap; they are not imported from a developed market.",utc_now()))
        repo.connection.commit()
        return sorted(output,key=lambda x:x["ticker"]),distribution
