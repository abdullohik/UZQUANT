from pathlib import Path

import pytest

from uzquant.research_api import FACTOR_NAMES, ResearchService
from uzquant.web import ResearchApplication


PRODUCTION = Path("data/uzquant.sqlite3")


@pytest.mark.skipif(not PRODUCTION.exists(), reason="production validation database is not in a clean source checkout")
def test_current_equity_api_matches_verified_rse_universe():
    service = ResearchService(PRODUCTION)
    universe = service.universe()
    coverage = service.coverage()
    assert universe["count"] == 73
    assert coverage["count"] == 73
    assert len(coverage["historical_excluded"]) == 7
    assert len(coverage["issuer_groups"]) == 52
    assert {row["security_class_code"] for row in universe["securities"]} == {"COMMON", "PREFERRED"}
    assert all(set(row["factors"]) == set(FACTOR_NAMES) for row in universe["securities"])
    assert all(row["top_blocker"] is None or {"code", "taxonomy", "evidence"} <= set(row["top_blocker"]) for row in universe["securities"])


@pytest.mark.skipif(not PRODUCTION.exists(), reason="production validation database is not in a clean source checkout")
def test_frozen_market_wide_results_are_unchanged():
    rows = {row["ticker"]: row for row in ResearchService(PRODUCTION).universe()["securities"]}
    assert rows["IPKY"]["signal"] == "REDUCE"
    assert rows["UZTL"]["signal"] == "HOLD"
    assert rows["AGMK"]["signal"] == rows["AGMKP"]["signal"] == "LIQUIDITY_TRAP"
    assert [row["ticker"] for row in rows.values() if row["valuation_status"] == "AVAILABLE"] == ["IPKY"]


def test_terminal_contract_is_read_only_and_has_all_required_views():
    html = Path("uzquant/static/index.html").read_text()
    js = Path("uzquant/static/app.js").read_text()
    css = Path("uzquant/static/styles.css").read_text()
    for label in ("MARKET", "SCREENER", "RESEARCH", "VALUATION", "FACTORS", "EVIDENCE", "COVERAGE", "SYSTEM"):
        assert f">{label}<" in html
    for label in FACTOR_NAMES:
        assert label in js
    for view in ("Most undervalued", "Best data coverage", "Valuation insufficient"):
        assert view in js
    assert '<span class="na">n/a</span>' in js
    assert "method:'POST'" not in js and 'method:"POST"' not in js
    assert "#0B1220" in css and "#111827" in css and "#162033" in css and "#C6A15B" in css


def test_coverage_route_is_exposed():
    class Service:
        def coverage(self): return {"status": "OK", "count": 73}
    app = ResearchApplication(Service())
    status = {}
    body = app({"PATH_INFO": "/api/v1/coverage", "REQUEST_METHOD": "GET"}, lambda s, h: status.update(value=s))
    assert status["value"].startswith("200")
    assert b'"count": 73' in b"".join(body)
