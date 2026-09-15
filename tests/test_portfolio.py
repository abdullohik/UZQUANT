from decimal import Decimal as D

from uzquant.portfolio import Candidate,PortfolioConfig,construct_portfolio


def candidate(name,**changes):
    values=dict(security_id=name,ticker=name,expected_upside=D(".5"),estimated_downside=D(".2"),confidence=D("80"),liquidity_capacity_value=D("1000000"),exit_horizon_days=D("3"),volatility=D(".2"),sector="INDUSTRIAL",governance_score=D("80"),data_quality_score=D("80"),free_float_maximum_value=None,government_exposure=D("0"),commodity_exposure=D("0"),fx_exposure=D("0"),factor_exposures={"VALUE":D("1")},thesis_reference="signal-1",validation_classification="ROBUST",signal_state="BUY")
    values.update(changes);return Candidate(**values)


def config(**changes):
    values=dict(single_name_cap=D(".3"),sector_cap=D(".5"),max_liquidation_horizon=D("10"),confidence_minimum=D("60"),government_exposure_cap=D(".5"),commodity_exposure_cap=D(".5"),fx_exposure_cap=D(".5"),factor_concentration_cap=D(".5"),correlated_group_cap=D(".4"))
    values.update(changes);return PortfolioConfig(**values)


def test_highly_correlated_portfolio_is_capped():
    result=construct_portfolio([candidate("A"),candidate("B")],D("1000000"),config=config(),correlations={("A","B"):D(".95")})
    assert sum(p.target_weight for p in result.positions)<=D(".4")


def test_sector_concentration_binds():
    result=construct_portfolio([candidate("A"),candidate("B")],D("1000000"),config=config(sector_cap=D(".2")))
    assert sum(p.target_weight for p in result.positions)==D(".2")
    assert any(p.binding_constraint in {"SECTOR","CORRELATED_GROUP"} for p in result.positions)


def test_one_illiquid_holding_gets_smaller_weight():
    result=construct_portfolio([candidate("LIQ"),candidate("ILLIQ",liquidity_capacity_value=D("10000"),sector="BANK")],D("1000000"),config=config())
    weights={p.candidate.ticker:p.target_weight for p in result.positions}
    assert weights["ILLIQ"]<weights["LIQ"]


def test_larger_portfolio_makes_capacity_binding():
    c=[candidate("A",liquidity_capacity_value=D("1000000"))]
    small=construct_portfolio(c,D("20000000"),config=config())
    large=construct_portfolio(c,D("20000000000"),config=config())
    assert large.positions[0].target_weight<small.positions[0].target_weight
    assert large.positions[0].binding_constraint=="LIQUIDITY"


def test_confidence_failure_excludes_candidate():
    result=construct_portfolio([candidate("A",confidence=D("40"))],D("1000000"),config=config())
    assert result.status=="DATA_INSUFFICIENT" and result.cash_weight==1


def test_liquidity_deterioration_reduces_allocation():
    good=construct_portfolio([candidate("A",liquidity_capacity_value=D("500000"))],D("1000000"),config=config())
    bad=construct_portfolio([candidate("A",liquidity_capacity_value=D("5000"))],D("1000000"),config=config())
    assert bad.positions[0].target_weight<good.positions[0].target_weight
