from datetime import date

from uzquant.cohort_expansion import ReadinessInputs, classify_blocker, readiness_score, select_cohort
from uzquant.repository import Repository
from uzquant.valuation import _method_blockers


def test_readiness_score_rewards_evidence_not_attractiveness():
    sparse=ReadinessInputs(True,False,2,0,0,False,0,False,0,0,0,0)
    complete=ReadinessInputs(True,True,60,3,4,True,2,True,4,2,1,2)
    assert readiness_score(sparse)==13
    assert readiness_score(complete)>readiness_score(sparse)
    assert 0<=readiness_score(complete)<=100


def test_cohort_selection_is_rank_order_only():
    rows=[{"ticker":"A","readiness_score":80},{"ticker":"B","readiness_score":70},{"ticker":"C","readiness_score":60}]
    selected=select_cohort(rows,2)
    assert [row["ticker"] for row in selected if row["selected"]]==["A","B"]
    assert "DATA_READINESS" in selected[0]["selection_reason"]


def test_every_blocker_is_classified_without_conflating_missing_with_zero():
    row={"financial_documents":2,"rights_records":0}
    assert classify_blocker(row,"MISSING_EBIT")=="DATA_ALREADY_PRESENT_NOT_NORMALIZED"
    assert classify_blocker(row,"UNVERIFIED_REPORTING_PERIMETER")=="METADATA_GAP"
    assert classify_blocker(row,"PREFERRED_SECURITY_RIGHTS_UNVERIFIED")=="PUBLIC_DATA_NOT_YET_COLLECTED"


def test_preferred_rights_gate_is_class_based_not_ticker_based():
    with Repository() as repo:
        repo.initialize()
        repo.connection.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at) VALUES('i','Issuer','TEST','2020-01-01')")
        repo.connection.execute("INSERT INTO securities VALUES('preferred','i','PREFERRED','EQUITY',NULL,'UZS','2020-01-01')")
        repo.connection.execute("INSERT INTO securities VALUES('common','i','COMMON','EQUITY',NULL,'UZS','2020-01-01')")
        preferred=_method_blockers(repo,"ARBITRARYP","DDM",[],{"security_id":"preferred","latest_concepts":{}},None,date(2026,9,28))
        common=_method_blockers(repo,"ARBITRARY","DDM",[],{"security_id":"common","latest_concepts":{}},None,date(2026,9,28))
        assert "PREFERRED_SECURITY_RIGHTS_UNVERIFIED" in preferred
        assert "PREFERRED_SECURITY_RIGHTS_UNVERIFIED" not in common
