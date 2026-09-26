from datetime import date
from decimal import Decimal as D

import pytest

from uzquant.valuation import (DCFScenario, FXInput, INSUFFICIENT, convert_fx,
    AssumptionInput,
    dcf_sensitivity_grid, dcf_value, dividend_discount, implied_equity_multiple,
    industrial_dcf, mining_scenario, relative_metrics, residual_income,
    route_valuation, validate_consistency)


def test_authoritative_source_assumption_requires_citation():
    AssumptionInput(D("1.25"), "AUTHORITATIVE_SOURCE", "CBU series URL").validate()
    with pytest.raises(ValueError):
        AssumptionInput(D("1.25"), "AUTHORITATIVE_SOURCE", None).validate()


def scenario(**overrides):
    values = dict(revenue_growth=D("0"), ebit_margin=D("0.20"), tax_rate=D("0.25"),
                  da_pct_revenue=D("0.03"), capex_pct_revenue=D("0.04"),
                  working_capital_pct_revenue=D("0"), wacc=D("0.10"),
                  terminal_growth=D("0"))
    values.update(overrides)
    return DCFScenario(**values)


def test_dcf_math_terminal_value_share_count_and_net_debt():
    # FCF = 100*20%*(1-25%)+3-4 = 14; terminal = 140; EV = (14+140)/1.1 = 140.
    result = dcf_value(D("100"), scenario(), 1, D("40"), D("10"))
    assert result["last_fcf"] == D("14.00")
    assert result["terminal_value"] == D("140.00")
    assert result["enterprise_value"] == D("140.0")
    assert result["equity_value"] == D("100.0")
    assert result["fair_value_per_share"] == D("10.0")


def test_dcf_scenarios_and_sensitivity():
    cases = {"bear": scenario(ebit_margin=D(".10")), "base": scenario(),
             "bull": scenario(ebit_margin=D(".30"))}
    result = industrial_dcf(D("100"), cases, 1, D("0"), D("10"), "UZS",
                            "NOMINAL", "NOMINAL", "UZS", D(".05"))
    assert result.status == "AVAILABLE"
    assert result.bear_value < result.base_value < result.bull_value
    grid = dcf_sensitivity_grid(D("100"), scenario(), 1, D("0"), D("10"),
                               (D(".09"), D(".11")), (D("0"), D(".02")),
                               (D("0"),), (D(".2"),))
    assert len(grid) == 6 and all(r["fair_value_per_share"] is not None for r in grid)


def test_missing_cash_flow_inputs_return_insufficient():
    cases = {name: scenario() for name in ("bear", "base", "bull")}
    result = industrial_dcf(None, cases, 5, None, None, "UZS", "NOMINAL",
                            "NOMINAL", "UZS", None)
    assert result.status == INSUFFICIENT
    assert "MISSING_REVENUE" in result.reasons


def test_currency_basis_and_fx_conversion():
    fx = FXInput("USD", "UZS", D("12500"), date(2026, 9, 15), "Central bank")
    assert convert_fx(D("2"), fx) == D("25000")
    validate_consistency("USD", "UZS", "NOMINAL", "NOMINAL", fx)
    with pytest.raises(ValueError): validate_consistency("USD", "UZS", "REAL", "NOMINAL", fx)
    with pytest.raises(ValueError): validate_consistency("USD", "UZS", "NOMINAL", "NOMINAL")


def test_bank_and_insurer_routing_excludes_industrial_primary():
    assert route_valuation("BANK")[1][0] == "P/B"
    assert route_valuation("INSURANCE")[1][0] == "P/B"
    assert "INDUSTRIAL_DCF" not in route_valuation("BANK")[1]
    assert "INDUSTRIAL_DCF" not in route_valuation("INSURANCE")[1]


def test_negative_earnings_do_not_produce_pe_or_implied_pe_value():
    assert relative_metrics(price=D("10"), eps=D("-2"))["P/E"] is None
    assert implied_equity_multiple(D("-2"), D("8"), require_positive_metric=True) is None


def test_residual_income_and_dividend_models():
    assert residual_income(D("100"), D(".15"), D(".10"), D(".03"), D("10")) is not None
    assert dividend_discount(D("2"), D(".12"), D(".02")) == D("20.4")
    assert dividend_discount(D("2"), D(".02"), D(".02")) is None


def test_mining_scenario_and_missing_inputs():
    assert mining_scenario(D("10"), D("5"), D("2"), D("3"), D("4")) == D("66")
    assert mining_scenario(None, D("5"), D("2"), D("3"), D("4")) is None


def test_invalid_terminal_growth_and_share_count():
    with pytest.raises(ValueError): dcf_value(D("100"), scenario(wacc=D(".03"), terminal_growth=D(".03")), 5, D("0"), D("10"))
    with pytest.raises(ValueError): dcf_value(D("100"), scenario(), 5, D("0"), D("0"))
