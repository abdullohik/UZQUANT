import sys
import inspect
import sqlite3
from decimal import Decimal
from types import SimpleNamespace

import pytest

from uzquant.targeted_valuation_unlock import _store_assumption, extract_ipky_2023_pdf
from uzquant.scoring import score_real_universe
from uzquant.valuation import MODEL_VERSION, _residual_income_source_lineage


def _install_pdf_reader(monkeypatch, text):
    page = SimpleNamespace(extract_text=lambda: text)
    reader = SimpleNamespace(pages=[page])
    monkeypatch.setitem(sys.modules, "pypdf", SimpleNamespace(PdfReader=lambda _: reader))


def test_ipky_parser_requires_explicit_perimeter_ifrs_and_unit(monkeypatch):
    text = """
    Ипак Йули
    Международными стандартами финансовой отчетности
    консолидированной финансовой отчетности
    (в миллионах узбекских сумов)
    ИТОГО АКТИВЫ 16 914 336 13 125 912
    ИТОГО ОБЯЗАТЕЛЬСТВА 14 096 641 10 992 891
    ИТОГО КАПИТАЛ 2 817 695 2 133 021
    Чистая прибыль за период 731 342 522 935
    Нематериальные активы 32 929 24 987
    Остаток на 31 декабря
    2021 года 534194 130 441 804 857 22 181 1 491 673
    """
    _install_pdf_reader(monkeypatch, text)
    parsed = extract_ipky_2023_pdf(b"fixture")
    assert parsed["perimeter"] == "CONSOLIDATED"
    assert parsed["values"]["Equity"][0] == 2_817_695_000_000
    assert parsed["values"]["Net Income"][1] == 522_935_000_000
    assert parsed["opening_equity_2021"][0] == 1_491_673_000_000


def test_ipky_parser_fails_closed_without_explicit_perimeter(monkeypatch):
    text = """
    Ипак Йули
    Международными стандартами финансовой отчетности
    (в миллионах узбекских сумов)
    """
    _install_pdf_reader(monkeypatch, text)
    with pytest.raises(ValueError, match="consolidated"):
        extract_ipky_2023_pdf(b"fixture")


def test_targeted_unlock_has_new_material_model_version():
    assert MODEL_VERSION == "sector-valuation/3.2.0"


def test_current_ranking_does_not_freeze_an_old_as_of_date():
    assert inspect.signature(score_real_universe).parameters["as_of"].default is None


def test_roe_assumption_and_valuation_preserve_opening_closing_and_income_lineage():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE valuation_assumption_inputs(assumption_id TEXT PRIMARY KEY,security_id TEXT,method TEXT,input_name TEXT,scenario TEXT,value TEXT,currency TEXT,as_of_date TEXT,provenance_class TEXT,source TEXT,created_at TEXT,UNIQUE(security_id,method,input_name,scenario,as_of_date))")
    connection.execute("CREATE TABLE valuation_assumption_details(assumption_id TEXT PRIMARY KEY,nominal_real_basis TEXT,source_date TEXT,source_url TEXT,methodology TEXT,derivation_json TEXT,confidence TEXT,assumption_version TEXT,created_at TEXT)")
    connection.execute("CREATE TABLE valuation_assumption_observation_lineage(assumption_id TEXT,observation_version_id TEXT,input_role TEXT,transformation TEXT,created_at TEXT,PRIMARY KEY(assumption_id,observation_version_id,input_role))")
    repo = SimpleNamespace(connection=connection)
    lineage = (
        ("OPENING_EQUITY_2022", "equity-2021", "AVERAGE_EQUITY=(OPENING_EQUITY+CLOSING_EQUITY)/2"),
        ("CLOSING_EQUITY_2022", "equity-2022", "AVERAGE_EQUITY=(OPENING_EQUITY+CLOSING_EQUITY)/2"),
        ("NET_INCOME_2022", "income-2022", "ROE=NET_INCOME/AVERAGE_EQUITY"),
    )
    assumption_id = _store_assumption(repo, "security", "ROE", "BEAR", Decimal("0.25"),
                                      "SOURCE_DERIVED", "audited report", "2024-12-11", "https://source",
                                      "verified two-period ROE", {}, "LOW", lineage)
    stored = connection.execute("SELECT input_role,observation_version_id FROM valuation_assumption_observation_lineage WHERE assumption_id=? ORDER BY input_role", (assumption_id,)).fetchall()
    assert stored == [("CLOSING_EQUITY_2022", "equity-2022"), ("NET_INCOME_2022", "income-2022"), ("OPENING_EQUITY_2022", "equity-2021")]

    assembled = {"latest_concepts": {
        "Equity": {"document_id": "doc", "observation_id": "equity-2023"},
        "Net Income": {"document_id": "doc", "observation_id": "income-2023"},
    }}
    detailed = [("ROE", "BEAR", "0.25", "SOURCE_DERIVED", "audited report", assumption_id)]
    documents, observations = _residual_income_source_lineage(repo, assembled, detailed)
    assert documents == ["doc"]
    assert observations == ["equity-2021", "equity-2022", "equity-2023", "income-2022", "income-2023"]
