from decimal import Decimal as D

from uzquant.position_sizing import SizingInputs, calculate_position_size, derive_entry_zones


def inputs(**changes):
    values = dict(portfolio_value=D("1000000"), expected_upside=D("0.50"), estimated_downside=D("0.20"), confidence=D("80"), adv_value=D("100000"), volatility=D("0.02"), liquidity_state="INVESTABLE", governance_score=D("90"), data_quality_score=D("90"))
    values.update(changes); return SizingInputs(**values)


def test_entry_zones_are_valuation_based_and_widen_with_uncertainty():
    tight = derive_entry_zones(D("90"), D("100"), D("110"), D("90"), D("70"))
    wide = derive_entry_zones(D("50"), D("100"), D("150"), D("40"), D("70"))
    assert tight.status == "AVAILABLE" and tight.observed_zone == "STRONG_BUY_ZONE"
    assert wide.effective_margin_of_safety > tight.effective_margin_of_safety


def test_high_conviction_shrinks_under_low_liquidity():
    liquid = calculate_position_size(inputs())
    illiquid = calculate_position_size(inputs(adv_value=D("1000"), liquidity_state="HIGH_LIQUIDITY_RISK"))
    assert illiquid.final_maximum < liquid.final_maximum
    assert illiquid.binding_constraint == "LIQUIDITY"


def test_high_confidence_shrinks_under_high_volatility():
    lower = calculate_position_size(inputs(volatility=D("0.01")))
    higher = calculate_position_size(inputs(volatility=D("0.20")))
    assert higher.risk_maximum < lower.risk_maximum
    assert higher.final_maximum < lower.final_maximum


def test_tiny_verified_free_float_binds():
    result = calculate_position_size(inputs(verified_free_float_value=D("50000")))
    assert result.binding_constraint == "FREE_FLOAT"
    assert result.free_float_maximum == D("0.0005")


def test_missing_liquidity_blocks_position_instead_of_assuming_capacity():
    result = calculate_position_size(inputs(adv_value=None, liquidity_state=None))
    assert result.status == "POSITION_SIZE_INSUFFICIENT"
    assert result.final_maximum == 0 and result.binding_constraint == "DATA_INSUFFICIENT"


def test_existing_portfolio_concentration_binds():
    result = calculate_position_size(inputs(existing_security_weight=D("0.039")))
    assert result.binding_constraint == "PORTFOLIO"
    assert result.final_maximum == D("0.001")


def test_lower_confidence_reduces_fundamental_and_risk_limits():
    high = calculate_position_size(inputs(confidence=D("90")))
    low = calculate_position_size(inputs(confidence=D("30")))
    assert low.fundamental_maximum < high.fundamental_maximum
    assert low.risk_maximum < high.risk_maximum
