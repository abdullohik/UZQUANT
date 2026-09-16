from __future__ import annotations

import json
from importlib.resources import files
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from .research_api import ResearchService


class ResearchApplication:
    def __init__(self, service: ResearchService): self.service=service

    def __call__(self, environ, start_response):
        path=environ.get("PATH_INFO","/"); method=environ.get("REQUEST_METHOD","GET")
        try:
            if method!="GET": return self._json(start_response,405,{"status":"METHOD_NOT_ALLOWED"})
            if path=="/": return self._asset(start_response,"index.html","text/html; charset=utf-8")
            if path.startswith("/assets/"):
                name=path.rsplit("/",1)[-1]; mime="text/css" if name.endswith(".css") else "text/javascript; charset=utf-8"
                return self._asset(start_response,name,mime)
            if path=="/api/v1/health": return self._json(start_response,200,{"status":"OK","service":"UZQUANT Research API"})
            if path=="/api/v1/universe": return self._json(start_response,200,self.service.universe({k:v[0] for k,v in parse_qs(environ.get("QUERY_STRING","")).items()}))
            if path=="/api/v1/macro": return self._json(start_response,200,self.service.macro())
            if path=="/api/v1/portfolios": return self._json(start_response,200,self.service.portfolios())
            if path=="/api/v1/backtests": return self._json(start_response,200,self.service.backtests())
            if path=="/api/v1/validation": return self._json(start_response,200,self.service.validation())
            if path=="/api/v1/pipelines": return self._json(start_response,200,self.service.pipelines())
            if path=="/api/v1/operations": return self._json(start_response,200,self.service.operations())
            parts=[p for p in path.split("/") if p]
            if len(parts)>=4 and parts[:3]==["api","v1","securities"]:
                detail=self.service.security(parts[3]); section=parts[4] if len(parts)>4 else None
                sections={"market":"market_observations","financials":"financial_documents","valuation":"valuation","liquidity":"liquidity","corporate":"corporate_actions","signals":"signal_history","report":"report"}
                return self._json(start_response,200,detail if not section else {"api_version":detail["api_version"],"ticker":parts[3],section:detail.get(sections.get(section,section))})
            if len(parts)==4 and parts[:3]==["api","v1","issuers"]: return self._json(start_response,200,self.service.issuer(parts[3]))
            return self._json(start_response,404,{"status":"NOT_FOUND"})
        except KeyError as exc: return self._json(start_response,404,{"status":"NOT_FOUND","identifier":str(exc)})
        except Exception as exc: return self._json(start_response,500,{"status":"ERROR","error":type(exc).__name__})

    def _json(self,start_response,status,payload):
        body=json.dumps(payload,default=str,sort_keys=True).encode(); start_response(f"{status} {'OK' if status<400 else 'ERROR'}",[("Content-Type","application/json"),("Content-Length",str(len(body))),("Cache-Control","no-store")]); return [body]

    def _asset(self,start_response,name,mime):
        asset=files("uzquant.static").joinpath(name)
        if not asset.is_file(): return self._json(start_response,404,{"status":"NOT_FOUND"})
        body=asset.read_bytes(); start_response("200 OK",[("Content-Type",mime),("Content-Length",str(len(body))),("Cache-Control","no-store")]); return [body]


def serve(database,host="127.0.0.1",port=8765):
    app=ResearchApplication(ResearchService(database))
    with make_server(host,port,app) as server: server.serve_forever()
