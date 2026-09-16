from datetime import date
from decimal import Decimal

from uzquant.financial_taxonomy import map_source_concept
from uzquant.repository import Repository
from uzquant.scoring import Evidence,data_quality_score,governance_factor
from uzquant.valuation import AssumptionInput,combine_valuations,execute_multiple_method,route_valuation


def test_exact_template_normalization_and_false_capex_rejection():
    assert map_source_concept("TOTAL FOR SECTION I (410+420+430+440+450+460+470)","480","BALANCE_SHEET")=="Equity"
    assert map_source_concept("Section I Total (500+510+520-530+540+550+560)","570","BALANCE_SHEET")=="Equity"
    assert map_source_concept("Net profit (loss) for the reporting period (290-300-310)","320","INCOME_STATEMENT")=="Net Income"
    assert map_source_concept("Capital Expenditures (0800)","100","BALANCE_SHEET") is None


def test_industrial_methods_are_independently_routed():
    methods=route_valuation("GENERAL")[1]
    assert {"INDUSTRIAL_DCF","EV/EBITDA","EV/EBIT","P/E","P/B","FCF_YIELD","DDM"}<=set(methods)


def test_multiple_valuation_requires_sourced_scenarios_and_uses_shares():
    assumptions={k:AssumptionInput(v,"SOURCE_DERIVED","versioned peer set") for k,v in {"bear":Decimal("4"),"base":Decimal("5"),"bull":Decimal("6")}.items()}
    result=execute_multiple_method("P/E",Decimal("1000"),Decimal("100"),assumptions,"UZS")
    assert (result.bear_value,result.base_value,result.bull_value)==(Decimal("40"),Decimal("50"),Decimal("60"))
    assert execute_multiple_method("P/E",Decimal("1000"),Decimal("100"),assumptions,"UZS",False).status=="VALUATION_INSUFFICIENT"


def test_consensus_is_confidence_weighted_and_currency_safe():
    a=execute_multiple_method("P/E",Decimal("1000"),Decimal("100"),{k:AssumptionInput(v,"OBSERVED","s") for k,v in {"bear":Decimal(4),"base":Decimal(5),"bull":Decimal(6)}.items()},"UZS")
    b=execute_multiple_method("P/B",Decimal("2000"),Decimal("100"),{k:AssumptionInput(v,"OBSERVED","s") for k,v in {"bear":Decimal(1),"base":Decimal(2),"bull":Decimal(3)}.items()},"UZS")
    assert combine_valuations([(a,Decimal(2)),(b,Decimal(1))]).base_value==Decimal("46.66666666666666666666666667")


def test_common_share_data_quality_has_no_preferred_right_penalty():
    common=data_quality_score(Evidence(financial_document_count=3,shares_outstanding_verified=True,market_observation_count=60,ownership_known=True,rights_confidence=None,valuation_available=True))
    preferred=data_quality_score(Evidence(financial_document_count=3,shares_outstanding_verified=True,market_observation_count=60,ownership_known=True,rights_confidence="MISSING",valuation_available=True))
    assert common.score-preferred.score==Decimal("10")


def test_governance_uses_only_directionally_supported_evidence():
    assert governance_factor([("e","MANAGEMENT_CHANGE","HIGH")]).score is None
    assert governance_factor([("e","DILUTION","HIGH")]).score==Decimal("25")


def test_unchecked_financial_document_is_not_eligible():
    with Repository() as repo:
        repo.initialize()
        tables={r[0] for r in repo.connection.execute("select name from sqlite_master where type='table'")}
        assert "financial_document_entity_checks" in tables
