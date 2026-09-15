import json
from decimal import Decimal

from uzquant.macro import MacroValue, classify_regimes, query_as_of, store_sector_mappings
from uzquant.repository import Repository, stable_id


def seeded_repo():
    repo = Repository(":memory:"); repo.initialize()
    repo.ensure_source("test", "Test source", "example.invalid", "PRIMARY", "VERIFIED_AUTOMATED", {})
    repo.connection.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES('run','test','2024-01-01T00:00:00Z','RUNNING','test')")
    for n in (1, 2):
        repo.connection.execute("INSERT INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)", (f"doc{n}", "test", "run", f"https://example.invalid/{n}", f"2024-0{n}-10T00:00:00Z", None, "application/json", str(n)*64, f"/tmp/{n}"))
    repo.connection.execute("INSERT INTO macro_series VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", ("series", "CPI_YOY", "CPI", "PRICES", "MONTHLY", "PERCENT", None, "test", "https://example.invalid", "SOURCE_RELEASE_DATE", "APPEND_ONLY_VINTAGES", "2024-01-01T00:00:00Z"))
    return repo


def insert_observation(repo, oid, value, vintage, document, revision=None):
    repo.connection.execute("INSERT INTO macro_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (oid, "series", "2023-12-01", "2023-12-31", "2024-01-10", revision, vintage, value, "PERCENT", None, "https://example.invalid", document, vintage, "test", "REVISED" if revision else "REPORTED"))


def test_as_of_returns_vintage_known_at_time_and_revision_later():
    repo = seeded_repo(); insert_observation(repo, "old", "10", "2024-01-10T00:00:00Z", "doc1"); insert_observation(repo, "new", "11", "2024-02-10T00:00:00Z", "doc2", "2024-02-10")
    assert query_as_of(repo.connection, "CPI_YOY", "2024-01-20T00:00:00Z")[0]["value"] == "10"
    assert query_as_of(repo.connection, "CPI_YOY", "2024-02-20T00:00:00Z")[0]["value"] == "11"
    assert query_as_of(repo.connection, "CPI_YOY", "2024-01-09T00:00:00Z") == []


def test_missing_macro_period_is_not_filled():
    repo = seeded_repo(); insert_observation(repo, "old", "10", "2024-01-10T00:00:00Z", "doc1")
    rows = query_as_of(repo.connection, "CPI_YOY", "2024-03-20T00:00:00Z")
    assert len(rows) == 1


def test_regime_transitions_are_deterministic_and_missing_is_unavailable():
    regimes = classify_regimes({"CBU_POLICY_RATE": [("2024-01-01", Decimal("14")), ("2024-02-01", Decimal("15"))], "USD_UZS": [("2023", Decimal("10000")), ("2024", Decimal("10700"))]})
    assert regimes["MONETARY_TIGHTENING"]["state"] == "ACTIVE"
    assert regimes["MONETARY_EASING"]["state"] == "INACTIVE"
    assert regimes["UZS_DEPRECIATION"]["state"] == "ACTIVE"
    assert regimes["HIGH_INFLATION"]["state"] == "UNAVAILABLE"


def test_sector_mappings_have_explicit_basis_and_no_signal_language():
    repo = Repository(":memory:"); repo.initialize(); count = store_sector_mappings(repo); repo.connection.commit()
    rows = repo.connection.execute("SELECT * FROM sector_macro_exposures").fetchall()
    assert count == len(rows) and all(row["basis_type"] == "ECONOMIC_ASSUMPTION" for row in rows)
    assert all("BUY" not in row["directional_effect"] and "SELL" not in row["directional_effect"] for row in rows)


def test_revision_uniqueness_and_release_fields_are_preserved():
    repo = seeded_repo(); insert_observation(repo, "old", "10", "2024-01-10T00:00:00Z", "doc1")
    row = repo.connection.execute("SELECT initial_release_date,revision_date,vintage_known_at FROM macro_observations").fetchone()
    assert tuple(row) == ("2024-01-10", None, "2024-01-10T00:00:00Z")
