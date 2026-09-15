from decimal import Decimal as D

from uzquant.scoring import (Evidence, FactorScore, aggregate_attractiveness,
    apply_risk_gates, confidence_score, cross_sectional_scores, data_quality_score,
    sector_factor_metrics)


def factor(name,value): return FactorScore(name,{"raw":str(value)},"TEST_ABSOLUTE",D(value))


def test_high_valuation_failed_liquidity_is_overridden():
    result=apply_risk_gates(D("90"),D("90"),D("90"),"LIQUIDITY_TRAP")
    assert result.tentative_state == "STRONG_BUY"
    assert result.state == "LIQUIDITY_TRAP"


def test_great_fundamentals_bad_data_is_insufficient():
    result=apply_risk_gates(D("95"),D("20"),D("35"),"INVESTABLE")
    assert result.state == "DATA_INSUFFICIENT"
    assert "CRITICAL_DATA_QUALITY" in result.gates


def test_unknown_share_rights_reduce_high_signal():
    result=apply_risk_gates(D("75"),D("60"),D("80"),"INVESTABLE",rights_unknown=True)
    assert result.state == "WATCH"
    assert "MATERIALLY_UNKNOWN_SHARE_RIGHTS" in result.gates


def test_stale_price_suppresses_aggressive_state():
    result=apply_risk_gates(D("85"),D("80"),D("80"),"INVESTABLE",stale_price=True)
    assert result.state == "WATCH"
    assert any("STALE_PRICE" in gate for gate in result.gates)


def test_missing_factor_is_not_replaced_by_average_score():
    factors={"Valuation":factor("Valuation","90"),"Quality":factor("Quality","80"),
             "Growth":FactorScore("Growth",{},"NOT_TRANSFORMED",None,"MISSING")}
    score,reason=aggregate_attractiveness(factors,minimum_available_factors=3)
    assert score is None and reason == "INSUFFICIENT_FACTOR_COVERAGE"


def test_small_peer_group_is_unavailable():
    result=cross_sectional_scores({"a":D("1"),"b":D("2"),"c":D("3")},minimum_peers=5)
    assert all(item.score is None and item.reason=="SMALL_PEER_GROUP" for item in result.values())


def test_cross_sectional_ranking_preserves_raw_values():
    values={str(i):D(i) for i in range(5)}
    result=cross_sectional_scores(values)
    assert result["0"].score==0 and result["4"].score==100
    assert result["4"].raw_metric["value"] == "4"


def test_sector_routing_uses_specialist_metrics():
    assert "NIM" in sector_factor_metrics("BANK")["Quality"]
    assert "Combined Ratio" in sector_factor_metrics("INSURANCE")["Quality"]
    assert "Production" in sector_factor_metrics("MINING")["Growth"]
    assert "Gross Margin" in sector_factor_metrics("GENERAL")["Quality"]


def test_data_quality_evidence_penalties_are_explicit():
    result=data_quality_score(Evidence())
    reasons={p["reason"] for p in result.raw_metric["penalties"]}
    assert result.score < 50
    assert {"MISSING_STATEMENTS","UNCERTAIN_SHARES_OUTSTANDING","WEAK_MARKET_HISTORY"} <= reasons


def test_confidence_is_separate_and_bounded():
    assert confidence_score(D("100"),D("100"),D("100"),D("100"),D("100"),D("100"),D("100"))==100


def test_severe_governance_override():
    result=apply_risk_gates(D("90"),D("90"),D("90"),"INVESTABLE",severe_governance=True)
    assert result.state=="GOVERNANCE_RISK"


def test_existing_acceptance_thresholds_are_unchanged():
    factors={name:factor(name,"80") for name in ("Valuation","Quality","Liquidity")}
    score,reason=aggregate_attractiveness(factors)
    assert score is None and reason=="INSUFFICIENT_FACTOR_COVERAGE"
    assert apply_risk_gates(D("90"),D("90"),D("49.99"),"INVESTABLE").state=="DATA_INSUFFICIENT"
