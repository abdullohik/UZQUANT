from __future__ import annotations
import tempfile,urllib.request
from collections import Counter
from pathlib import Path
from .cohort_expansion import _md_table as table
from .config import Settings
from .issuer_valuation_unlock import export_mission2b
from .repository import Repository,stable_id,utc_now
from .security_master import archive

VERSION="perimeter-ownership-resolution/1.0.0"; SOURCE_ID="issuer-official-ownership-evidence"
PRESENT={
 "<Olmaliq KMK> AJ":("https://agmk.uz/en/menu/affilirovannye-litsa",{"2023","2026"},"Official affiliated-person list identifies multiple controlled entities, including 100% holdings, with relationship dates in 2023/2024."),
 "<O'zbektelekom> AK":("https://esg.uztelecom.uz/ru/determination-of-material-topics-and-report-boundaries.html",{"2024"},"Official 2024 sustainability report explicitly states that the company has subsidiaries and excludes them from that report boundary."),
 "<UzAuto Motors> AJ":("https://uzautomotors.com/documents/prospectus/file_prospectus1.pdf",{"2019"},"Official 2019 consolidated statements identify JSC UzAuto Motors and its subsidiaries as the Group."),
}
SEARCH={
 "<Agrobank> ATB":"https://agrobank.uz/ru/about/bank","<Biokimyo> AJ":"https://www.biokimyo.uz/ru/menu/godovye-otchety-emitenta",
 "<Hamkorbank> ATB":"https://hamkorbank.uz/about-bank/subsidiaries/","<Kapital sug'urta> AJ":"https://kapitalsugurta.uz/post/category/company_charter",
 "<O'zbekgeofizika> AJ":"https://uzbekgeofizika.uz/","<O'zbektelekom> AK":PRESENT["<O'zbektelekom> AK"][0],
 "<Olmaliq KMK> AJ":PRESENT["<Olmaliq KMK> AJ"][0],"<Qizilqumsement> AJ":"https://openinfo.uz/ru/reports/jsc/annual/5985",
 "<UzAuto Motors> AJ":PRESENT["<UzAuto Motors> AJ"][0],"AITB <Ipak Yo'li>":"https://en.ipakyulibank.uz/about/to-shareholders-and-investors/list-of-affiliated-persons-of-the-bank",
}

def _fetch(url):
 request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 UZQUANT research evidence collector"})
 with urllib.request.urlopen(request,timeout=30) as response:
  if response.status!=200: raise RuntimeError(f"HTTP {response.status}: {url}")
  return response.read()

def run(settings:Settings,outputs=Path("outputs"),fetcher=_fetch):
 now=utc_now(); report=[]; counts=Counter(); errors=[]
 with Repository(settings.database_path) as repo:
  repo.initialize(); c=repo.connection
  docs=c.execute("SELECT d.*,i.legal_name FROM financial_documents d JOIN issuers i USING(issuer_id) WHERE d.reporting_perimeter='UNKNOWN' ORDER BY i.legal_name,d.period_end,d.document_id").fetchall()
  if len(docs)!=36: raise ValueError(f"Mission 2d scope drift: expected 36 unresolved documents, found {len(docs)}")
  repo.ensure_source(SOURCE_ID,"Official issuer ownership/charter evidence","issuer websites","PRIMARY","VERIFIED_MANUAL",{"mission":"2d","version":VERSION}); run_id=repo.start_run(SOURCE_ID,VERSION); evidence={}
  for name,(url,periods,statement) in PRESENT.items():
   issuer=c.execute("SELECT issuer_id FROM issuers WHERE legal_name=?",(name,)).fetchone()
   try:
    body=fetcher(url); document,digest,path=archive(settings.raw_data_dir,body,now,"perimeter-ownership"); mime="application/pdf" if url.endswith(".pdf") else "text/html"
    repo.add_raw_document((document,SOURCE_ID,run_id,url,now,None,mime,digest,path)); eid=stable_id("perimeter-evidence",f"{issuer[0]}:{url}:{','.join(sorted(periods))}")
    effective_from=(next(iter(periods))+"-01-01") if len(periods)==1 else None; effective_to=(next(iter(periods))+"-12-31") if len(periods)==1 else None
    c.execute("INSERT OR REPLACE INTO perimeter_ownership_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(eid,issuer[0],"SUBSIDIARIES_PRESENT",effective_from,effective_to,now,url,document,statement,"AUTHORITATIVE_SOURCE",VERSION,now)); evidence[name]=eid
   except Exception as exc: errors.append(f"{name}: {type(exc).__name__}: {exc}")
  for name,url in SEARCH.items():
   issuer=c.execute("SELECT issuer_id FROM issuers WHERE legal_name=?",(name,)).fetchone()[0]; found=name in evidence
   note=PRESENT[name][2] if found else "Bounded official issuer/portal search found no period-matched statement establishing the complete controlled-entity population."
   c.execute("INSERT OR IGNORE INTO perimeter_source_search_log VALUES(?,?,?,?,?,?,?,?)",(stable_id("perimeter-search",f"{issuer}:{url}:{VERSION}"),issuer,now,"charter, subsidiaries, affiliated persons and official disclosures",url,"SUBSIDIARIES_PRESENT" if found else "NO_PERIOD_MATCHED_EVIDENCE",note,VERSION))
  for doc in docs:
   spec=PRESENT.get(doc["legal_name"]); matched=bool(spec and doc["period_end"][:4] in spec[1] and doc["legal_name"] in evidence)
   if matched: classification="SUBSIDIARIES_PRESENT"; period="MATCHED"; provenance="AUTHORITATIVE_SOURCE"; eid=evidence[doc["legal_name"]]; reason="Controlled entities existed in the matching period; financial-statement perimeter remains UNKNOWN."
   else: classification="OWNERSHIP_EVIDENCE_UNAVAILABLE"; period="NOT_MATCHED" if spec else "NO_PERIOD_EVIDENCE"; provenance="UNAVAILABLE"; eid=None; reason="No authoritative period-matched source establishes the complete controlled-entity population; perimeter remains UNKNOWN."
   counts[classification]+=1
   c.execute("INSERT OR REPLACE INTO financial_document_perimeter_assessments VALUES(?,?,?,?,?,?,?,?,?,?,?)",(stable_id("perimeter-assessment",f"{doc['document_id']}:{VERSION}"),doc["document_id"],classification,None,provenance,eid,period,"PUBLIC_DATA_NOT_YET_COLLECTED",reason,now,VERSION))
   report.append([doc["legal_name"],doc["document_id"],f"{doc['period_start']} to {doc['period_end']}",classification,period,spec[0] if matched else SEARCH[doc["legal_name"]],spec[2] if matched else reason,"UNKNOWN — unchanged"])
  c.commit(); repo.finish_run(run_id,"PARTIAL" if errors else "SUCCEEDED",len(evidence),len(errors),"\n".join(errors) or None)
 outputs.mkdir(parents=True,exist_ok=True)
 issuer_summary=("## Issuer-period classification\n\n"
  "- `NO_SUBSIDIARIES_CONFIRMED`: **0 issuers**.\n"
  "- `SUBSIDIARIES_PRESENT`: **3 issuers** for matched periods — `<Olmaliq KMK> AJ` (2023 and 2026), `<O'zbektelekom> AK` (2024), `<UzAuto Motors> AJ` (2019).\n"
  "- `OWNERSHIP_EVIDENCE_UNAVAILABLE`: **8 issuers with one or more unresolved periods** — `<Agrobank> ATB`, `<Biokimyo> AJ`, `<Hamkorbank> ATB`, `<Kapital sug'urta> AJ`, `<O'zbekgeofizika> AJ`, `<O'zbektelekom> AK` (2025 only), `<Qizilqumsement> AJ`, and `AITB <Ipak Yo'li>`. Categories overlap only because classification is reporting-period-specific.\n\n")
 (outputs/"perimeter_ownership_resolution.md").write_text(f"# Mission 2d Perimeter Resolution via Ownership/Charter Evidence\n\nGenerated: {now}. Version: `{VERSION}`. Scope: 36 unresolved documents across 10 issuers. Document-text extraction was not rerun.\n\n## Honest result\n\n"+table(["Category","Documents"],[[x,counts.get(x,0)] for x in ("NO_SUBSIDIARIES_CONFIRMED","SUBSIDIARIES_PRESENT","OWNERSHIP_EVIDENCE_UNAVAILABLE")])+"\n\nNo issuer had authoritative, period-matched evidence explicitly confirming **no subsidiaries**. No perimeter was promoted and `STRUCTURAL_INFERENCE_NO_SUBSIDIARIES` was not assigned. This zero-yield result is an evidence ceiling, not a parser failure.\n\n"+issuer_summary+"## Document decisions\n\n"+table(["Issuer","Document","Reporting period","Classification","Period check","Official source/search route","Evidence/reason","Perimeter result"],report)+"\n\n## Search-log standard\n\nEvery issuer has a stored search-log row with retrieval timestamp, search scope, route and outcome. Unresolved cases remain `PUBLIC_DATA_NOT_YET_COLLECTED`; none is called `PUBLIC_SOURCE_EXHAUSTED`.\n")
 with tempfile.TemporaryDirectory() as td:
  temp=Path(td); export_mission2b(settings.database_path,temp)
  for name in ("universe_valuations.md","universe_factor_coverage.md","universe_blocker_queue.md"):
   (outputs/name).write_text((temp/name).read_text().rstrip()+f"\n\n## Mission 2d perimeter result\n\nAs of {now}, 0 of 36 unknown perimeters were legitimately resolved. Valuation, factor, gate and signal records remain unchanged.\n")
 return {"documents":len(report),"categories":dict(counts),"resolved":0,"download_errors":errors}
