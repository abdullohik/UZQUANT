import json
from pathlib import Path

from uzquant.research_api import grounded_report
from uzquant.web import ResearchApplication


class FakeService:
    def universe(self,filters=None): return {"status":"OK","count":1,"securities":[{"ticker":"TEST","market":{"price":"12.5"},"signal":"DATA_INSUFFICIENT"}]}
    def security(self,ticker): return {"api_version":"test","identity":{"ticker":ticker,"security_id":"s1"},"valuation_status":"VALUATION_INSUFFICIENT","signal":{"signal_state":"DATA_INSUFFICIENT","confidence":"22"},"warnings":["DATA_INSUFFICIENT"],"report":{"status":"GROUNDED"}}
    def issuer(self,issuer_id): return {"issuer":{"issuer_id":issuer_id}}
    def macro(self): return {"observations":[]}
    def portfolios(self): return {"runs":[]}
    def backtests(self): return {"status":"BACKTEST_INSUFFICIENT"}
    def validation(self): return {"validation":{"classification":"UNRELIABLE"}}
    def pipelines(self): return {"pipelines":[]}
    def operations(self): return {"status":"OK","health":[],"runs":[],"anomalies":[],"alerts":[],"signal_transitions":[]}
    def paper_trading(self): return {"status":"OK","portfolios":[],"snapshots":[],"security_states":[],"orders":[],"fills":[],"signal_outcomes":[],"drift":[]}


def request(app,path):
    captured={}
    def start(status,headers): captured.update(status=status,headers=dict(headers))
    body=b"".join(app({"PATH_INFO":path,"REQUEST_METHOD":"GET","QUERY_STRING":""},start))
    return captured,json.loads(body) if captured["headers"]["Content-Type"]=="application/json" else body.decode()


def test_api_security_value_matches_backend_service_exactly():
    status,payload=request(ResearchApplication(FakeService()),"/api/v1/securities/TEST")
    assert status["status"].startswith("200")
    assert payload["identity"]["ticker"]=="TEST"
    assert payload["signal"]["confidence"]=="22"
    assert payload["valuation_status"]=="VALUATION_INSUFFICIENT"


def test_missing_data_is_not_converted_to_zero():
    class Missing(FakeService):
        def universe(self,filters=None): return {"status":"OK","count":1,"securities":[{"ticker":"X","price":None}]}
    _,payload=request(ResearchApplication(Missing()),"/api/v1/universe")
    assert payload["securities"][0]["price"] is None


def test_warning_and_insufficient_states_are_visible_in_client():
    html=Path("uzquant/static/index.html").read_text(); js=Path("uzquant/static/app.js").read_text()
    assert "Missing evidence is never displayed as zero" in html
    assert "VALUATION_INSUFFICIENT" in html and "LIQUIDITY_TRAP" in html
    assert "/api/v1/securities/" in js and "/api/v1/validation" in js


def test_grounded_report_uses_backend_records_only():
    detail={"identity":{"ticker":"X","security_id":"s","security_class_code":"COMMON","legal_name":"Issuer","sector":"BANK"},"signal":{"signal_state":"HOLD","confidence":"31","triggered_gates_json":[]},"valuation":[],"valuation_status":"VALUATION_INSUFFICIENT","liquidity":None,"capacity":None,"financial_documents":[{"document_id":"d1"}],"fundamentals":[],"ownership":[],"rights_assessment":None,"governance":[],"events":[],"warnings":["VALUATION_INSUFFICIENT"],"source_record_ids":["d1"]}
    report=grounded_report(detail)
    assert "31" in report["sections"]["Executive Research Summary"]
    assert report["sections"]["Investment State"]=="HOLD"
    assert report["source_record_ids"]==["d1"]


def test_api_schema_and_static_assets():
    app=ResearchApplication(FakeService())
    assert request(app,"/api/v1/health")[1]["status"]=="OK"
    status,html=request(app,"/")
    assert status["status"].startswith("200") and "UZQUANT" in html


def test_phase17_operations_endpoint_is_read_only_and_available():
    status,payload=request(ResearchApplication(FakeService()),"/api/v1/operations")
    assert status["status"].startswith("200")
    assert payload["status"]=="OK" and payload["alerts"]==[]


def test_phase18_paper_trading_endpoint_is_read_only_and_available():
    status,payload=request(ResearchApplication(FakeService()),"/api/v1/paper-trading")
    assert status["status"].startswith("200")
    assert payload["status"]=="OK" and payload["fills"]==[]
