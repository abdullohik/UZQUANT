import json
import sqlite3
from pathlib import Path

import pytest

from uzquant.static_site import export_static_site, verify_static_site


PRODUCTION = Path("data/uzquant.sqlite3")


@pytest.mark.skipif(not PRODUCTION.exists(), reason="production validation database is not in a clean source checkout")
def test_static_export_preserves_market_wide_backend_contract(tmp_path):
    manifest = export_static_site(PRODUCTION, tmp_path / "site", "test-revision")
    verified = verify_static_site(tmp_path / "site")
    universe = json.loads((tmp_path / "site/data/universe.json").read_text())
    assert manifest == verified
    assert manifest["security_count"] == universe["count"] == 73
    assert manifest["policy"] == "READ_ONLY_BACKEND_DERIVED_SNAPSHOT"
    assert (tmp_path / "site/data/securities/IPKY.json").is_file()
    assert (tmp_path / "site/data/lineage/IPKY.json").is_file()
    assert 'name="uzquant-static-snapshot" content="true"' in (tmp_path / "site/index.html").read_text()


def test_static_verifier_rejects_inconsistent_manifest(tmp_path):
    site = tmp_path / "site"
    (site / "data").mkdir(parents=True)
    (site / "data/manifest.json").write_text(json.dumps({
        "format": "uzquant-static-snapshot/1.0.0",
        "security_count": 2,
        "tickers": ["IPKY"],
    }))
    with pytest.raises(ValueError, match="security manifest"):
        verify_static_site(site)


def test_export_does_not_modify_canonical_database(tmp_path):
    database = tmp_path / "test.sqlite3"
    sqlite3.connect(database).close()
    before = database.read_bytes()
    with pytest.raises(ValueError, match="no current research securities"):
        export_static_site(database, tmp_path / "site")
    assert database.read_bytes() == before


def test_export_refuses_to_replace_unmarked_directory(tmp_path):
    database = tmp_path / "test.sqlite3"
    sqlite3.connect(database).close()
    output = tmp_path / "unrelated"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve me", encoding="utf-8")

    with pytest.raises(ValueError, match="unmarked output directory"):
        export_static_site(database, output)

    assert sentinel.read_text(encoding="utf-8") == "preserve me"
