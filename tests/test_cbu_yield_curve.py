import json

from uzquant.cbu_yield_curve import parse_curve_payloads, store_curve_payloads, curve_as_of
from uzquant.repository import Repository


def payloads(rate="16.96"):
    results = [{"id": 7, "date": "2026-09-23", "codeRevisionNumber": "revision-1"}]
    points = [{"id": 70, "yieldCurveResultsId": 7, "date": "2036-09-23", "str": "10 years",
               "deltaPeriods": 3652, "discount": 0.21, "zeroRate": rate, "forwardRate": 17.1}]
    return json.dumps(results).encode(), json.dumps(points).encode()


def seeded():
    repo = Repository(":memory:"); repo.initialize()
    repo.ensure_source("cbu-government-yield-curve", "CBU curve", "uz-yield-curve.cbu.uz",
                       "PRIMARY", "VERIFIED_AUTOMATED", {})
    repo.connection.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES('r','cbu-government-yield-curve','2026-09-27','RUNNING','test')")
    for doc, url in (("results", "https://official/results"), ("points", "https://official/points")):
        repo.connection.execute("INSERT INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)",
                                (doc, "cbu-government-yield-curve", "r", url, "2026-09-27T00:00:00Z", None,
                                 "application/json", ("1" if doc == "results" else "2")*64, f"/tmp/{doc}"))
    return repo


def test_full_curve_parser_preserves_tenor_and_official_fields():
    results, points = parse_curve_payloads(*payloads())
    assert results[7]["date"] == "2026-09-23"
    assert points[0].tenor_days == 3652 and str(points[0].zero_rate_percent) == "16.96"


def test_curve_storage_is_point_in_time_and_nominal_uzs_continuous():
    repo = seeded()
    summary = store_curve_payloads(repo, *payloads(), "2026-09-27T00:00:00Z", "results", "points")
    repo.connection.commit()
    assert summary["curve_vintages"] == 1 and summary["curve_points"] == 1
    assert curve_as_of(repo.connection, "2026-09-26T23:59:59Z") == []
    row = curve_as_of(repo.connection, "2026-09-28T00:00:00Z")[0]
    assert (row["currency"], row["rate_basis"], row["compounding"]) == ("UZS", "NOMINAL", "CONTINUOUS")
    assert row["provenance_class"] == "AUTHORITATIVE_SOURCE" and row["observation_class"] == "OBSERVED"


def test_curve_rerun_preserves_distinct_retrieval_vintage():
    repo = seeded()
    first = payloads("16.96")
    store_curve_payloads(repo, *first, "2026-09-27T00:00:00Z", "results", "points")
    # Re-use immutable raw evidence in this unit fixture while proving retrieval-time vintage behavior.
    store_curve_payloads(repo, *payloads("17.00"), "2026-09-28T00:00:00Z", "results", "points")
    repo.connection.commit()
    assert repo.connection.execute("SELECT count(*) FROM government_yield_curve_vintages").fetchone()[0] == 2
    assert curve_as_of(repo.connection, "2026-09-27T12:00:00Z")[0]["zero_rate_percent"] == "16.96"
    assert curve_as_of(repo.connection, "2026-09-29T00:00:00Z")[0]["zero_rate_percent"] == "17.00"
