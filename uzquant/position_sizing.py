from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .repository import Repository, utc_now

D = Decimal
ENTRY_MODEL_VERSION = "valuation-entry-zones/1.0.0"
SIZING_MODEL_VERSION = "constraint-sizing/1.0.0"
ZONE_STATES = ("STRONG_BUY_ZONE", "ACCUMULATE_ZONE", "FAIR_VALUE_ZONE", "TRIM_ZONE", "OVERVALUED_ZONE")


@dataclass(frozen=True)
class EntryConfig:
    base_margin_of_safety: Decimal = D("0.20")
    risk_addon: Decimal = D("0.05")
    uncertainty_weight: Decimal = D("0.25")
    minimum_margin: Decimal = D("0.05")
    maximum_margin: Decimal = D("0.60")


@dataclass(frozen=True)
class EntryZones:
    status: str
    strong_buy_upper: Decimal | None = None
    accumulate_upper: Decimal | None = None
    fair_value_upper: Decimal | None = None
    trim_upper: Decimal | None = None
    effective_margin_of_safety: Decimal | None = None
    observed_zone: str | None = None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class SizingConfig:
    fundamental_cap: Decimal = D("0.05")
    risk_cap: Decimal = D("0.04")
    portfolio_concentration_cap: Decimal = D("0.04")
    target_position_volatility: Decimal = D("0.015")
    participation_rate: Decimal = D("0.10")
    liquidation_days: Decimal = D("5")
    free_float_participation_cap: Decimal = D("0.01")


@dataclass(frozen=True)
class SizingInputs:
    portfolio_value: Decimal
    expected_upside: Decimal | None
    estimated_downside: Decimal | None
    confidence: Decimal | None
    adv_value: Decimal | None
    volatility: Decimal | None
    liquidity_state: str | None
    governance_score: Decimal | None
    data_quality_score: Decimal | None
    existing_security_weight: Decimal = D("0")
    existing_sector_weight: Decimal = D("0")
    sector_limit: Decimal = D("0.25")
    verified_free_float_value: Decimal | None = None


@dataclass(frozen=True)
class SizingResult:
    status: str
    fundamental_maximum: Decimal | None
    liquidity_maximum: Decimal | None
    risk_maximum: Decimal | None
    portfolio_maximum: Decimal
    free_float_maximum: Decimal | None
    final_maximum: Decimal
    final_position_value: Decimal
    binding_constraint: str
    reasons: tuple[str, ...]


def derive_entry_zones(bear: Decimal | None, base: Decimal | None, bull: Decimal | None,
                       confidence: Decimal | None, observed_price: Decimal | None = None,
                       config: EntryConfig = EntryConfig()) -> EntryZones:
    if None in (bear, base, bull, confidence):
        return EntryZones("ENTRY_INSUFFICIENT", reasons=("MISSING_VALUATION_RANGE_OR_CONFIDENCE",))
    if bear <= 0 or base <= 0 or bull <= 0 or not bear <= base <= bull:
        return EntryZones("ENTRY_INSUFFICIENT", reasons=("INVALID_OR_NON_MONOTONIC_VALUATION_RANGE",))
    if confidence < 0 or confidence > 100:
        raise ValueError("confidence must be 0..100")
    if observed_price is not None and observed_price <= 0:
        raise ValueError("observed price must be positive")
    confidence_fraction = confidence / D("100")
    range_uncertainty = (bull - bear) / (D("2") * base)
    margin = config.base_margin_of_safety + config.risk_addon + range_uncertainty * (D("1") - confidence_fraction) * config.uncertainty_weight
    margin = min(config.maximum_margin, max(config.minimum_margin, margin))
    boundaries = (base * (D("1") - margin), base * (D("1") - margin / 2), base * (D("1") + margin / 2), base * (D("1") + margin))
    zone = None
    if observed_price is not None:
        zone = next(name for limit, name in zip((*boundaries, D("Infinity")), ZONE_STATES) if observed_price <= limit)
    return EntryZones("AVAILABLE", *boundaries, margin, zone)


def calculate_position_size(inputs: SizingInputs, config: SizingConfig = SizingConfig()) -> SizingResult:
    if inputs.portfolio_value <= 0:
        raise ValueError("portfolio value must be positive")
    scalar_values = (inputs.expected_upside, inputs.estimated_downside, inputs.volatility)
    if any(value is not None and value < 0 for value in scalar_values):
        raise ValueError("upside, downside and volatility cannot be negative")
    scores = (inputs.confidence, inputs.governance_score, inputs.data_quality_score)
    if any(value is not None and not D("0") <= value <= D("100") for value in scores):
        raise ValueError("scores must be 0..100")
    if min(inputs.existing_security_weight, inputs.existing_sector_weight) < 0:
        raise ValueError("existing weights cannot be negative")
    reasons = []
    fundamental = None
    if None not in (inputs.expected_upside, inputs.estimated_downside, inputs.confidence):
        total_move = inputs.expected_upside + inputs.estimated_downside
        payoff = inputs.expected_upside / total_move if total_move > 0 else D("0")
        fundamental = config.fundamental_cap * payoff * (inputs.confidence / D("100"))
    else:
        reasons.append("FUNDAMENTAL_CONVICTION_UNAVAILABLE")
    liquidity = None
    if inputs.adv_value is not None and inputs.adv_value > 0 and inputs.liquidity_state not in (None, "UNASSESSABLE"):
        liquidity_value = inputs.adv_value * config.participation_rate * config.liquidation_days
        state_cap = {"INVESTABLE": D("1"), "LIMITED_LIQUIDITY": D("0.75"), "HIGH_LIQUIDITY_RISK": D("0.35"), "LIQUIDITY_TRAP": D("0")}.get(inputs.liquidity_state, D("0"))
        liquidity = min(D("1"), liquidity_value / inputs.portfolio_value * state_cap)
    else:
        reasons.append("LIQUIDITY_CAPACITY_UNAVAILABLE")
    risk = None
    if inputs.volatility is not None and inputs.confidence is not None and inputs.governance_score is not None and inputs.data_quality_score is not None:
        volatility_scalar = D("1") if inputs.volatility == 0 else min(D("1"), config.target_position_volatility / inputs.volatility)
        evidence_scalar = min(inputs.confidence, inputs.governance_score, inputs.data_quality_score) / D("100")
        risk = config.risk_cap * volatility_scalar * evidence_scalar
    else:
        reasons.append("RISK_CAPACITY_INCOMPLETE")
    portfolio = max(D("0"), min(config.portfolio_concentration_cap - inputs.existing_security_weight, inputs.sector_limit - inputs.existing_sector_weight))
    free_float = None
    if inputs.verified_free_float_value is not None:
        if inputs.verified_free_float_value < 0:
            raise ValueError("free-float value cannot be negative")
        free_float = inputs.verified_free_float_value * config.free_float_participation_cap / inputs.portfolio_value
    else:
        reasons.append("FREE_FLOAT_UNKNOWN")
    required = {"FUNDAMENTAL": fundamental, "LIQUIDITY": liquidity}
    if any(value is None for value in required.values()):
        reasons.append("REQUIRED_CONSTRAINT_UNAVAILABLE")
        return SizingResult("POSITION_SIZE_INSUFFICIENT", fundamental, liquidity, risk, portfolio, free_float, D("0"), D("0"), "DATA_INSUFFICIENT", tuple(reasons))
    constraints = {"FUNDAMENTAL": fundamental, "LIQUIDITY": liquidity, "PORTFOLIO": portfolio}
    if risk is not None: constraints["RISK"] = risk
    if free_float is not None: constraints["FREE_FLOAT"] = free_float
    binding, final = min(constraints.items(), key=lambda item: (item[1], item[0]))
    return SizingResult("AVAILABLE", fundamental, liquidity, risk, portfolio, free_float, final, final * inputs.portfolio_value, binding, tuple(reasons))


def _latest_price(repo: Repository, security_id: str, as_of: date):
    row = repo.connection.execute("SELECT close,last,individual_trade_price FROM market_observations WHERE security_id=? AND trade_date<=? AND observation_status='TRADE_REPORTED' ORDER BY trade_date DESC LIMIT 1", (security_id, as_of.isoformat())).fetchone()
    if not row: return None
    value = next((v for v in row if v is not None), None)
    return D(value) if value is not None else None


def run_real_position_examples(database: Path, portfolio_values=(D("100000000"), D("1000000000"), D("10000000000")), as_of: date = date(2026, 9, 15)):
    tickers = ("AGMKP", "KASUP", "IPKY", "UZTL", "QZSM")
    output = []
    with Repository(database) as repo:
        repo.initialize()
        securities = repo.connection.execute("SELECT DISTINCT s.security_id,h.identifier_value ticker FROM securities s JOIN identifier_history h ON h.security_id=s.security_id AND h.identifier_type='TICKER' WHERE h.identifier_value IN (?,?,?,?,?) ORDER BY ticker", tickers).fetchall()
        for security in securities:
            sid, ticker = security
            valuation = repo.connection.execute("SELECT * FROM valuation_records WHERE security_id=? AND data_cutoff_date<=? ORDER BY created_at DESC LIMIT 1", (sid, as_of.isoformat())).fetchone()
            liquidity = repo.connection.execute("SELECT * FROM liquidity_assessments WHERE security_id=? AND as_of_date<=? AND position_shares='10000' AND participation_rate='0.10' ORDER BY created_at DESC LIMIT 1", (sid, as_of.isoformat())).fetchone()
            signal = repo.connection.execute("SELECT * FROM research_signals WHERE security_id=? ORDER BY generated_at DESC LIMIT 1", (sid,)).fetchone()
            price = _latest_price(repo, sid, as_of)
            if valuation and valuation["status"] == "AVAILABLE":
                zones = derive_entry_zones(D(valuation["bear_value"]), D(valuation["base_value"]), D(valuation["bull_value"]), D(valuation["confidence"]), price)
            else:
                zones = EntryZones("ENTRY_INSUFFICIENT", reasons=("VALUATION_INSUFFICIENT",))
            entry_id = str(uuid.uuid4())
            repo.connection.execute("INSERT INTO entry_zone_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (entry_id, sid, valuation["valuation_id"] if valuation else None, as_of.isoformat(), valuation["currency"] if valuation else None, valuation["bear_value"] if valuation else None, valuation["base_value"] if valuation else None, valuation["bull_value"] if valuation else None, str(zones.effective_margin_of_safety) if zones.effective_margin_of_safety is not None else None, str(zones.strong_buy_upper) if zones.strong_buy_upper is not None else None, str(zones.accumulate_upper) if zones.accumulate_upper is not None else None, str(zones.fair_value_upper) if zones.fair_value_upper is not None else None, str(zones.trim_upper) if zones.trim_upper is not None else None, str(price) if price is not None else None, zones.observed_zone, zones.status, json.dumps(zones.reasons), json.dumps(asdict(EntryConfig()), default=str, sort_keys=True), ENTRY_MODEL_VERSION, utc_now()))
            features = json.loads(liquidity["features_json"]) if liquidity else {}
            adv_shares = D(features["average_daily_share_volume"]) if features.get("average_daily_share_volume") is not None else None
            adv_value = adv_shares * price if adv_shares is not None and price is not None else None
            volatility = D(features["observed_daily_volatility"]) if features.get("observed_daily_volatility") is not None else None
            confidence = D(signal["confidence"]) if signal else None
            factors = json.loads(signal["factor_scores_json"]) if signal else {}
            data_quality = D(factors["Data Quality"]["score"]) if factors.get("Data Quality", {}).get("score") is not None else None
            governance = D(factors["Governance"]["score"]) if factors.get("Governance", {}).get("score") is not None else None
            for portfolio in portfolio_values:
                sizing_inputs = SizingInputs(portfolio, None, None, confidence, adv_value, volatility, liquidity["liquidity_state"] if liquidity else None, governance, data_quality)
                result = calculate_position_size(sizing_inputs)
                sizing_id = str(uuid.uuid4())
                repo.connection.execute("INSERT INTO position_sizing_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (sizing_id, sid, entry_id, liquidity["assessment_id"] if liquidity else None, signal["signal_id"] if signal else None, as_of.isoformat(), str(portfolio), "UZS", str(result.fundamental_maximum) if result.fundamental_maximum is not None else None, str(result.liquidity_maximum) if result.liquidity_maximum is not None else None, str(result.risk_maximum) if result.risk_maximum is not None else None, str(result.portfolio_maximum), str(result.free_float_maximum) if result.free_float_maximum is not None else None, str(result.final_maximum), str(result.final_position_value), result.binding_constraint, result.status, json.dumps(asdict(sizing_inputs), default=str, sort_keys=True), json.dumps(asdict(SizingConfig()), default=str, sort_keys=True), json.dumps({"reasons": result.reasons, "research_model_output_not_personal_advice": True}, sort_keys=True), SIZING_MODEL_VERSION, utc_now()))
                output.append({"ticker": ticker, "entry": zones, "portfolio_value": portfolio, "sizing": result, "adv_value": adv_value, "liquidity_state": liquidity["liquidity_state"] if liquidity else None, "confidence": confidence})
        repo.connection.commit()
    return output
