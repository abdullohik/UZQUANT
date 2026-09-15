from datetime import date
from decimal import Decimal
from pathlib import Path
import pytest

from uzquant.remediation import verified_shares_as_of
from uzquant.remediation_b import (parse_exchange_share_rows,preferred_rights_gate,
    scale_financial_value,validate_financial_metadata)
from uzquant.repository import Repository
from uzquant.valuation import route_valuation
from uzquant.scoring import apply_risk_gates


def test_exchange_share_parser_is_class_specific():
    html=b"<table><tr><td>Preferred share</td><td>UZ700055K015 AGMKP</td><td>8,998,232</td><td>3,914</td></tr></table>"
    row=parse_exchange_share_rows(html)[0]
    assert (row.ticker,row.security_class,row.quantity,row.nominal_value)==("AGMKP","PREFERRED",Decimal("8998232"),Decimal("3914"))


def test_effective_dated_share_selection_rejects_future_disclosure():
    with Repository() as repo:
        repo.initialize()
        repo.connection.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at) VALUES('i','I','TEST','2020-01-01')")
        repo.connection.execute("INSERT INTO securities VALUES('s','i','COMMON','EQUITY',NULL,'UZS','2020-01-01')")
        repo.connection.execute("INSERT INTO share_capital_observations VALUES('o','i','s','2025-01-01','2025-02-01',NULL,'10','1','UZS','VERIFIED',NULL,NULL,'u','p','v','2025-02-01')")
        assert verified_shares_as_of(repo,'s',date(2025,1,15)) is None
        assert verified_shares_as_of(repo,'s',date(2025,2,1))["class_shares_outstanding"]=='10'


def test_unit_scaling_and_unknown_unit_rejection():
    assert scale_financial_value(Decimal("12.5"),"THOUSAND_UZS")==Decimal("12500.0")
    assert scale_financial_value(Decimal("2"),"MILLION_UZS")==Decimal("2000000")
    with pytest.raises(ValueError): scale_financial_value(Decimal(1),"SOURCE_UNIT_UNSPECIFIED")


def test_currency_and_perimeter_are_mandatory():
    assert validate_financial_metadata("USD","THOUSAND_UZS","STANDALONE")==("UNVERIFIED_FINANCIAL_CURRENCY",)
    assert validate_financial_metadata("UZS","THOUSAND_UZS","UNKNOWN")==("UNVERIFIED_REPORTING_PERIMETER",)


def test_sector_routing_and_preferred_right_gate():
    assert route_valuation("BANK")[0]=="BANK"
    assert "INDUSTRIAL_DCF" not in route_valuation("INSURANCE")[1]
    assert preferred_rights_gate("PREFERRED","LOW")==("PREFERRED_SECURITY_RIGHTS_UNVERIFIED",)
    assert preferred_rights_gate("PREFERRED","HIGH")==()


def test_risk_gate_thresholds_are_preserved():
    result=apply_risk_gates(Decimal("90"),Decimal("90"),Decimal("49.99"),"INVESTABLE")
    assert result.state=="DATA_INSUFFICIENT"
