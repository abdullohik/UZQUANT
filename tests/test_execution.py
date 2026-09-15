from decimal import Decimal as D

from uzquant.execution import CANNOT_ESTIMATE, ExecutionInputs, assess_execution, partial_fill_schedule
from uzquant.liquidity import LiquidityFeatures


def features(**changes):
    values=dict(observation_count=100,average_daily_share_volume=D("10000"),median_daily_share_volume=D("9000"),average_daily_trading_value=D("1000000"),median_daily_trading_value=D("900000"),trading_frequency=D("0.9"),zero_trade_day_ratio=D("0.1"),average_trade_count=D("5"),median_trade_count=D("4"),bid_ask_spread=None,depth_shares=None,days_since_last_trade=1,free_float=None,free_float_turnover=None,ownership_concentration=None,observed_daily_volatility=D("0.02"),calendar_basis="TEST")
    values.update(changes); return LiquidityFeatures(**values)


def case(**changes):
    values=dict(proposed_shares=D("1000"),side="ENTER",security_class="COMMON",liquidity_state="INVESTABLE",features=features(),mark_price=D("100"))
    values.update(changes); return ExecutionInputs(**values)


def test_no_order_book_exposes_unknown_child_and_intraday():
    result=assess_execution(case())
    assert result.status=="ESTIMATE_AVAILABLE" and result.maximum_suggested_child_order is None
    assert "ORDER_BOOK_AND_SPREAD_UNAVAILABLE" in result.uncertainty
    assert result.intraday_timing_status=="INTRADAY_TIMING_NOT_RELIABLE"


def test_wide_spread_uses_patient_limit_style_without_fill_guarantee():
    result=assess_execution(case(bid=D("90"),ask=D("110")))
    assert "VERY_WIDE_SPREAD" in result.flags
    assert result.preferred_execution_style=="PATIENT_LIMIT_ORDER_NO_FILL_ASSUMPTION"


def test_partial_fill_schedule_preserves_total_order():
    fills=partial_fill_schedule(D("250"),D("100"))
    assert fills==(D("100"),D("100"),D("50")) and sum(fills)==D("250")


def test_zero_trade_day_cannot_estimate():
    empty=features(observation_count=18,average_daily_share_volume=D("0"),trading_frequency=D("0"),zero_trade_day_ratio=D("1"))
    result=assess_execution(case(features=empty,liquidity_state="UNASSESSABLE",mark_price=None))
    assert result.status==CANNOT_ESTIMATE and result.expected_slippage_low is None


def test_illiquid_preferred_stock_has_small_participation_and_long_horizon():
    result=assess_execution(case(security_class="PREFERRED",liquidity_state="HIGH_LIQUIDITY_RISK",features=features(average_daily_share_volume=D("100"))))
    assert result.maximum_participation_rate==D("0.02") and result.estimated_execution_horizon_days==D("500")


def test_liquid_stock_gets_daily_participation_estimate():
    result=assess_execution(case())
    assert result.maximum_participation_rate==D("0.10") and result.estimated_execution_horizon_days==D("1")


def test_price_limit_does_not_assume_a_fill():
    result=assess_execution(case(price_limit_active=True))
    assert "PRICE_LIMIT_ACTIVE" in result.flags
    assert result.preferred_execution_style=="WAIT_OR_LIMIT_ORDER_AFTER_VENUE_RULE_VERIFICATION"
