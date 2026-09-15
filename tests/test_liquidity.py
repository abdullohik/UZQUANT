from datetime import date
from decimal import Decimal as D

import pytest

from uzquant.liquidity import (LiquidityFeatures, Thresholds, assess_capacity,
                               calculate_features, liquidation_horizon)


def features(**overrides):
    values = dict(observation_count=90, average_daily_share_volume=D("10000"),
        median_daily_share_volume=D("9000"), average_daily_trading_value=D("10000000"),
        median_daily_trading_value=D("9000000"), trading_frequency=D("1"),
        zero_trade_day_ratio=D("0"), average_trade_count=D("20"), median_trade_count=D("18"),
        bid_ask_spread=D(".01"), depth_shares=D("50000"), days_since_last_trade=1,
        free_float=D(".30"), free_float_turnover=D(".01"), ownership_concentration=D(".40"),
        observed_daily_volatility=D(".01"), calendar_basis="SUPPLIED_TRADING_CALENDAR",
        source_observation_ids=())
    values.update(overrides)
    return LiquidityFeatures(**values)


def test_liquid_stock_is_investable():
    result = assess_capacity(features(), D("1000"), D("100"), D(".10"))
    assert result.liquidity_state == "INVESTABLE"
    assert result.liquidation_horizon_days == D("1")
    assert result.estimated_realizable_value_low < result.mark_to_market_value


def test_zero_volume_and_stale_stock_is_liquidity_trap():
    result = assess_capacity(features(average_daily_share_volume=D("0"), median_daily_share_volume=D("0"),
        trading_frequency=D("0"), zero_trade_day_ratio=D("1"), days_since_last_trade=None), D("100"), D("10"), D(".10"))
    assert result.liquidity_state == "LIQUIDITY_TRAP"
    assert {"VERY_LOW_ADV","ZERO_VOLUME_DOMINANCE","EXTREME_STALENESS","UNRELIABLE_LAST_PRICE"} <= set(result.hard_flags)
    assert result.estimated_realizable_value_low is None


def test_large_position_exceeds_capacity():
    result = assess_capacity(features(), D("1000000"), D("100"), D(".10"))
    assert result.liquidation_horizon_days == D("1000")
    assert result.liquidity_state == "LIQUIDITY_TRAP"
    assert "POSITION_EXCEEDS_CAPACITY" in result.hard_flags


def test_tiny_adv_is_flagged():
    result = assess_capacity(features(average_daily_share_volume=D("500")), D("1000"), D("10"), D(".10"))
    assert "VERY_LOW_ADV" in result.hard_flags


def test_unknown_free_float_and_missing_order_book_reduce_confidence():
    result = assess_capacity(features(free_float=None, free_float_turnover=None, depth_shares=None,
        bid_ask_spread=None), D("1000"), D("100"), D(".10"))
    assert result.liquidity_confidence == "LOW"
    assert "FREE_FLOAT_UNAVAILABLE" in result.uncertainty
    assert "ORDER_BOOK_DEPTH_UNAVAILABLE" in result.uncertainty
    assert result.expected_slippage_high > result.expected_slippage_low


def test_extreme_concentration_and_wide_spread():
    result = assess_capacity(features(ownership_concentration=D(".95"), bid_ask_spread=D(".15")),
                             D("1000"), D("100"), D(".10"))
    assert "EXTREME_OWNERSHIP_CONCENTRATION" in result.hard_flags
    assert "VERY_WIDE_SPREAD" in result.hard_flags
    assert result.liquidity_state == "LIMITED_LIQUIDITY"


def test_feature_calculation_distinguishes_no_trade_days():
    rows = [
      {"observation_id":"a","trade_date":"2026-09-01","share_volume":"0","turnover_value":None,"trade_count":None,"close":"10","bid":None,"ask":None,"bid_size":None,"ask_size":None,"observation_status":"NO_TRADE_PLACEHOLDER"},
      {"observation_id":"b","trade_date":"2026-09-02","share_volume":"100","turnover_value":"1000","trade_count":2,"close":"10","bid":"9","ask":"11","bid_size":"5","ask_size":"5","observation_status":"TRADE_REPORTED"},
    ]
    result = calculate_features(rows,date(2026,9,3))
    assert result.average_daily_share_volume == D("50")
    assert result.trading_frequency == D(".5")
    assert result.zero_trade_day_ratio == D(".5")
    assert result.days_since_last_trade == 1


def test_horizons_at_configurable_participation_rates():
    assert liquidation_horizon(D("1000"),D("1000"),D(".05")) == D("20")
    assert liquidation_horizon(D("1000"),D("1000"),D(".10")) == D("10")
    assert liquidation_horizon(D("1000"),D("1000"),D(".20")) == D("5")
    with pytest.raises(ValueError): liquidation_horizon(D("1"),D("1"),D("0"))


def test_missing_mark_is_unassessable():
    result=assess_capacity(features(),D("100"),None,D(".10"))
    assert result.liquidity_state == "UNASSESSABLE"
