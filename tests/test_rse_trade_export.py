from datetime import date
import io
from zipfile import ZipFile

from uzquant.config import Settings
from uzquant.repository import Repository
from uzquant.rse_trade_export import ingest_trade_export, parse_trade_export
from uzquant.rse_history import import_inbox, next_job, parse_trade_results_html, plan_history, queue_status


def _html_trade(last_page=2):
    pagination = f'<a href="/trade_results?page={last_page}">Last &raquo;</a>' if last_page > 1 else ''
    return f'''<html><table><tbody><tr>
    <td>September 25, 2026 14:28</td><td></td>
    <td><a href="/isu_infos/STK?isu_cd=UZ700055K015">UZ700055K015<br>AGMKP</a></td>
    <td>&lt;Olmaliq KMK&gt; AJ</td><td>Pref. stocks</td><td>STK</td><td>G1</td>
    <td>33,333</td><td>3</td><td><span>UZS</span><br>99,999</td>
    </tr></tbody></table>{pagination}</html>'''.encode()


def test_trade_results_html_parser_and_pagination():
    rows, pages = parse_trade_results_html(_html_trade())
    assert pages == 2 and len(rows) == 1
    assert rows[0]["isin"] == "UZ700055K015"
    assert rows[0]["ticker"] == "AGMKP"
    assert rows[0]["exchange_timestamp"] == "2026-09-25T14:28:00"
    assert rows[0]["turnover_value"] == "99999"


def test_trade_results_html_rejects_turnover_mismatch():
    import pytest
    with pytest.raises(ValueError, match="turnover mismatch"):
        parse_trade_results_html(_html_trade().replace(b"99,999", b"99,998"))


def _workbook(path):
    strings = ["Время", "Код ЦБ", "Тикер", "Эмитент", "Тип ценной бумаги", "Рынок", "Площадка", "Торговая цена", "Кол-во ЦБ", "Объём торгов", "24.09.2026 11:41:37", "UZ700055K015", "AGMKP", "Issuer", "Прив. акции", "STK", "G1"]
    shared = '<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' + "".join(f"<si><t>{value}</t></si>" for value in strings) + "</sst>"
    header = "".join(f'<c r="{chr(65+i)}1" t="s"><v>{i}</v></c>' for i in range(10))
    values = list(range(10, 17))
    row = "".join(f'<c r="{chr(65+i)}2" t="s"><v>{value}</v></c>' for i, value in enumerate(values))
    row += '<c r="H2"><v>27000</v></c><c r="I2"><v>14</v></c><c r="J2"><v>378000</v></c>'
    sheet = f'<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1">{header}</row><row r="2">{row}</row></sheetData></worksheet>'
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def test_trade_export_parser_and_idempotent_ingestion(tmp_path):
    source = tmp_path / "trade.xlsx"
    _workbook(source)
    rows = parse_trade_export(source.read_bytes())
    assert len(rows) == 1
    assert all(row["market_code"] == "STK" for row in rows)
    settings = Settings(tmp_path / "db.sqlite3", tmp_path / "raw")
    with Repository(settings.database_path) as repo:
        repo.initialize()
        repo.ensure_source("uzse-public-web", "UZSE", "uzse.uz", "PRIMARY", "VERIFIED_MANUAL", {})
    first = ingest_trade_export(settings, source, date(2026, 9, 23), date(2026, 9, 24))
    second = ingest_trade_export(settings, source, date(2026, 9, 23), date(2026, 9, 24))
    assert first["records_inserted"] == 1
    assert second["records_inserted"] == 0 and second["idempotent"]
    with Repository(settings.database_path) as repo:
        assert repo.connection.execute("SELECT count(*) FROM rse_trade_records").fetchone()[0] == 1


def test_resumable_history_queue_and_validated_inbox(tmp_path):
    settings = Settings(tmp_path / "db.sqlite3", tmp_path / "raw")
    with Repository(settings.database_path) as repo:
        repo.initialize()
        repo.ensure_source("uzse-public-web", "UZSE", "uzse.uz", "PRIMARY", "VERIFIED_MANUAL", {})
        repo.connection.execute("INSERT INTO ingestion_runs(run_id,source_id,started_at,status,parser_version) VALUES('seed','uzse-public-web','2026-01-01','SUCCEEDED','seed')")
        repo.connection.execute("INSERT INTO raw_documents VALUES('doc','uzse-public-web','seed','https://uzse.uz','2026-01-01',NULL,'text/html',?,'seed')", ("a" * 64,))
        repo.connection.execute("INSERT INTO issuers(issuer_id,legal_name,resolution_method,created_at) VALUES('issuer','Issuer','TEST','2026-01-01')")
        repo.connection.execute("INSERT INTO securities VALUES('security','issuer','PREFERRED','EQUITY',NULL,'UZS','2026-01-01')")
        repo.connection.execute("INSERT INTO listings VALUES('listing','security','UZSE','STK','ACTIVE',NULL,NULL,'2026-01-01','doc')")
        repo.connection.execute("INSERT INTO identifier_history(identifier_id,entity_type,security_id,identifier_type,identifier_value,known_at,document_id) VALUES('isin','SECURITY','security','ISIN','UZ700055K015','2026-01-01','doc')")
        repo.connection.execute("INSERT INTO identifier_history(identifier_id,entity_type,security_id,identifier_type,identifier_value,known_at,document_id) VALUES('ticker','SECURITY','security','TICKER','AGMKP','2026-01-01','doc')")
        repo.connection.commit()
    planned = plan_history(settings.database_path, date(2026, 9, 1), date(2026, 10, 1))
    assert planned["jobs_created"] == 2
    job = next_job(settings.database_path)
    assert job["status"] == "READY" and job["isin"] == "UZ700055K015"
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    _workbook(inbox / job["expected_inbox_name"])
    result = import_inbox(settings, inbox)
    assert result["imported_files"] == 1 and result["failed_files"] == 0
    assert queue_status(settings.database_path)["by_status"] == {"IMPORTED": 1, "PENDING": 1}
