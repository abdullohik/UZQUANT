import sys
import inspect
from types import SimpleNamespace

import pytest

from uzquant.targeted_valuation_unlock import extract_ipky_2023_pdf
from uzquant.scoring import score_real_universe
from uzquant.valuation import MODEL_VERSION


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
    """
    _install_pdf_reader(monkeypatch, text)
    parsed = extract_ipky_2023_pdf(b"fixture")
    assert parsed["perimeter"] == "CONSOLIDATED"
    assert parsed["values"]["Equity"][0] == 2_817_695_000_000
    assert parsed["values"]["Net Income"][1] == 522_935_000_000


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
