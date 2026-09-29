from decimal import Decimal

import pytest

from uzquant.evidence import PROVENANCE_CLASSES
from uzquant.repository import Repository
from uzquant.valuation import AssumptionInput
from uzquant.perimeter_resolution import PRESENT


def test_structural_inference_is_a_distinct_provenance_class():
    assert "STRUCTURAL_INFERENCE_NO_SUBSIDIARIES" in PROVENANCE_CLASSES
    AssumptionInput(Decimal("1"), "STRUCTURAL_INFERENCE_NO_SUBSIDIARIES", "official charter evidence").validate()


def test_perimeter_evidence_schema_is_migrated(tmp_path):
    with Repository(tmp_path / "db.sqlite") as repo:
        repo.initialize()
        tables={r[0] for r in repo.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"perimeter_ownership_evidence","financial_document_perimeter_assessments","perimeter_source_search_log"} <= tables


def test_non_no_subsidiary_assessment_cannot_resolve_perimeter(tmp_path):
    with Repository(tmp_path / "db.sqlite") as repo:
        repo.initialize(); c=repo.connection
        with pytest.raises(Exception):
            c.execute("INSERT INTO financial_document_perimeter_assessments VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                      ("a","missing","SUBSIDIARIES_PRESENT","CONSOLIDATED","AUTHORITATIVE_SOURCE",None,"MATCHED",None,"bad","now","v"))


def test_period_matches_are_explicit_not_inferred_from_current_evidence():
    assert PRESENT["<O'zbektelekom> AK"][1] == {"2024"}
    assert "2025" not in PRESENT["<O'zbektelekom> AK"][1]
    assert PRESENT["<UzAuto Motors> AJ"][1] == {"2019"}
