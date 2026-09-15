from datetime import date

import pytest

from uzquant.events import (EventCandidate, catalyst_for, classify_with_llm,
                            event_signal_effect, events_as_of, store_event)
from uzquant.repository import Repository, utc_now
from uzquant.scoring import catalyst_factor


def repo_with_sources():
    repo=Repository(); repo.initialize()
    repo.ensure_source("test","Test source","example.test","PRIMARY","VERIFIED_AUTOMATED",{})
    run=repo.start_run("test","test/1")
    repo.connection.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at) VALUES('issuer','Issuer','TEST',?)",(utc_now(),))
    repo.connection.execute("INSERT INTO securities VALUES('security','issuer','COMMON','EQUITY',NULL,'UZS',?)",(utc_now(),))
    for n in (1,2):
        repo.connection.execute("INSERT INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)",(f"doc{n}","test",run,f"https://example.test/{n}",f"2026-01-0{n}T00:00:00+00:00","2026-01-01","text/html",str(n)*64,f"/tmp/doc{n}"))
    repo.connection.commit(); return repo


def candidate(doc="doc1",record="r1",canonical="issuer:DIVIDEND:2026-01-01"):
    return EventCandidate("issuer",("security",),"2026-01-02","2026-01-03","DIVIDEND",
        "Dividend disclosed.","UNKNOWN","NEUTRAL","SHORT_TERM","HIGH",
        "DETERMINISTIC_TEST",doc,"test_record",record,f"https://example.test/{doc[-1]}",
        "Source states a dividend.",canonical)


def test_duplicate_disclosure_is_idempotent():
    repo=repo_with_sources(); store_event(repo,candidate()); store_event(repo,candidate()); repo.connection.commit()
    assert repo.connection.execute("SELECT count(*) FROM research_events").fetchone()[0]==1
    assert repo.connection.execute("SELECT count(*) FROM research_event_sources").fetchone()[0]==1


def test_same_event_from_multiple_sources_links_without_duplicate_merge():
    repo=repo_with_sources(); first=store_event(repo,candidate()); second=store_event(repo,candidate("doc2","r2")); repo.connection.commit()
    assert first==second
    assert repo.connection.execute("SELECT count(*) FROM research_events").fetchone()[0]==1
    assert repo.connection.execute("SELECT count(*) FROM research_event_sources").fetchone()[0]==2


def test_conflicting_source_is_logged_not_silently_overwritten():
    repo=repo_with_sources(); store_event(repo,candidate())
    conflicting=EventCandidate(**{**candidate("doc2","r2").__dict__,"direction":"POSITIVE"})
    store_event(repo,conflicting); repo.connection.commit()
    assert repo.connection.execute("SELECT direction FROM research_events").fetchone()[0]=="NEUTRAL"
    assert repo.connection.execute("SELECT count(*) FROM research_event_conflicts").fetchone()[0]==1


def test_llm_uncertainty_is_retained_and_neutralized():
    c=EventCandidate(**{**candidate().__dict__,"event_type":"ACQUISITION","direction":"POSITIVE","confidence":"MEDIUM","classification_method":"LLM_CLASSIFIER","model_version":"model-x","prompt_version":"prompt-1"})
    result=classify_with_llm(c,.60)
    assert result.event_type=="OTHER" and result.direction=="NEUTRAL" and result.confidence=="LOW"


def test_llm_lineage_is_required():
    c=EventCandidate(**{**candidate().__dict__,"classification_method":"LLM_CLASSIFIER"})
    repo=repo_with_sources()
    with pytest.raises(ValueError): store_event(repo,c)


def test_publication_date_controls_point_in_time_visibility():
    repo=repo_with_sources(); store_event(repo,candidate()); repo.connection.commit()
    assert len(events_as_of(repo,"issuer","2026-01-01"))==0
    assert len(events_as_of(repo,"issuer","2026-01-02"))==1


def test_positive_event_does_not_turn_overvalued_stock_into_buy():
    assert event_signal_effect("AVOID","STRONG_POSITIVE")=="AVOID"


def test_negative_event_does_not_turn_cheap_stock_into_sell_automatically():
    assert event_signal_effect("BUY","STRONG_NEGATIVE")=="BUY"


def test_catalyst_occurrence_materiality_and_relevance_are_separate():
    relevance,score,confidence,_=catalyst_for("PRIVATIZATION","POSITIVE","HIGH","HIGH")
    assert relevance=="DIRECT" and score=="80" and confidence=="HIGH"
    relevance,score,_,_=catalyst_for("DIVIDEND","NEUTRAL","UNKNOWN","HIGH")
    assert relevance=="POSSIBLE" and score=="40"


def test_phase8_catalyst_factor_preserves_event_evidence():
    rows=[{"event_id":"e1","event_type":"DIVIDEND","publication_at":"2026-01-01","event_materiality":"UNKNOWN","catalyst_relevance":"POSSIBLE","catalyst_confidence":"LOW","catalyst_score":"40"}]
    result=catalyst_factor(rows)
    assert result.score==40 and result.raw_metric["events"][0]["event_id"]=="e1"
