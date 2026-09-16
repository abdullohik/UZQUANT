from __future__ import annotations
import hashlib,html,json,re,zipfile
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
from .financial_documents import parse_decimal
from .financial_taxonomy import map_source_concept
from .repository import Repository,stable_id,utc_now
from .rse import fetch
PARSER_VERSION="remediation-c-attachments/1.0.0"

def _xlsx_rows(content:bytes):
 with zipfile.ZipFile(BytesIO(content)) as z:
  shared=[]
  if "xl/sharedStrings.xml" in z.namelist():
   shared=["".join(x.itertext()) for x in ET.fromstring(z.read("xl/sharedStrings.xml"))]
  for name in sorted(n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml",n)):
   for row in ET.fromstring(z.read(name)).iter():
    if not row.tag.endswith('}row'): continue
    cells=[]
    for cell in row:
     if not cell.tag.endswith('}c'): continue
     kind=cell.attrib.get('t'); value=next((x.text for x in cell if x.tag.endswith('}v')),None)
     if value is None: cells.append(next(("".join(x.itertext()) for x in cell if x.tag.endswith('}is')),""))
     else: cells.append(shared[int(value)] if kind=='s' else value)
    if any(cells): yield name,row.attrib.get('r','?'),cells

def ingest_financial_attachments(settings):
 with Repository(settings.database_path) as repo:
  repo.initialize(); repo.ensure_source("openinfo-attachment","Openinfo official report attachments","new-api.openinfo.uz","PRIMARY","VERIFIED_AUTOMATED",{"formats":["XLSX","PDF"]})
  repo.connection.execute(
   "UPDATE ingestion_runs SET finished_at=?,status='FAILED',errors=1,error_details='INTERRUPTED_PRIOR_RUN' "
   "WHERE source_id='openinfo-attachment' AND status='RUNNING'",
   (utc_now(),),
  )
  repo.connection.commit()
  run=repo.start_run("openinfo-attachment",PARSER_VERSION); stored=scaled=bank_values=errors=0
  docs=repo.connection.execute("SELECT f.*,r.storage_path FROM financial_documents f JOIN raw_documents r ON r.document_id=f.raw_document_id JOIN financial_document_entity_checks c ON c.document_id=f.document_id AND c.validation_status='MATCHED' JOIN financial_document_identity_assignments a ON a.document_id=f.document_id AND a.assignment_status='VERIFIED'").fetchall()
  for doc in docs:
   text=Path(doc['storage_path']).read_text(errors='ignore'); match=re.search(r'https://new-api\.openinfo\.uz/api/v2/reports/export-excel/[^"\\]+',text)
   if not match: continue
   url=html.unescape(match.group(0))
   try: content=fetch(url,timeout=settings.request_timeout_seconds,attempts=settings.retry_attempts,backoff=settings.retry_backoff_seconds)
   except Exception: errors+=1; continue
   digest=hashlib.sha256(content).hexdigest(); raw_id=stable_id('raw-financial-attachment',f'{url}:{digest}'); target=settings.raw_data_dir/'openinfo'/'attachments'/f'{raw_id}.xlsx'; target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists(): target.write_bytes(content)
   repo.connection.execute("INSERT OR IGNORE INTO raw_documents VALUES(?,?,?,?,?,?,?,?,?)",(raw_id,"openinfo-attachment",run,url,utc_now(),doc['publication_date'],"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",digest,str(target))); stored+=1
   rows=list(_xlsx_rows(content)); workbook_text=' '.join(' '.join(r[2]) for r in rows).casefold(); unit='THOUSAND_UZS' if ('thousand soums' in workbook_text or 'thousand uzs' in workbook_text) else None
   if unit:
    eid=stable_id('metadata-evidence',f"{doc['document_id']}:unit:{raw_id}")
    repo.connection.execute("INSERT OR REPLACE INTO financial_document_metadata_evidence VALUES(?,?,?,?,?,?,?,?,?,?)",(eid,doc['document_id'],'SOURCE_UNIT',unit,'HIGH',raw_id,url,'workbook header',PARSER_VERSION,utc_now()))
    for obs in repo.connection.execute("SELECT observation_id,raw_value FROM financial_observations WHERE document_id=?",(doc['document_id'],)).fetchall():
     number=parse_decimal(obs[1])
     if number is not None: repo.connection.execute("UPDATE financial_observations SET normalized_value=?,unit='UZS' WHERE observation_id=?",(str(number*Decimal(1000)),obs[0])); scaled+=1
   if '/bank/' in doc['source_url']:
    for sheet,rownum,cells in rows:
     label=next((c for c in cells if c and not re.fullmatch(r'[-+]?\d+(?:\.\d+)?',c)),None); nums=[parse_decimal(c) for c in cells if parse_decimal(c) is not None]
     if not label or not nums: continue
     concept=map_source_concept(label,None,'UNKNOWN','BANK')
     if not concept: continue
     raw=str(nums[-1]); location=f"xlsx:{sheet}/row[{rownum}]"; rid=stable_id('financial-raw',f"{doc['document_id']}:{location}")
     repo.connection.execute("INSERT OR IGNORE INTO financial_raw_values VALUES(?,?,?,?,?,?,?,?,?)",(rid,doc['document_id'],'UNKNOWN',label,None,raw,'CURRENT_OR_PERIOD_END',location,'STRUCTURED_XLSX'))
     oid=stable_id('financial-observation',f"{doc['document_id']}:{concept}:{location}"); value=nums[-1]*Decimal(1000) if unit else nums[-1]
     repo.connection.execute("INSERT OR REPLACE INTO financial_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(oid,doc['document_id'],doc['issuer_id'],'UNKNOWN',concept,doc['period_start'],doc['period_end'],raw,str(value),doc['currency'],'UZS' if unit else 'SOURCE_UNIT_UNSPECIFIED','AS_REPORTED',location,'STRUCTURED_XLSX','HIGH','REPORTED')); bank_values+=1
   repo.connection.commit()
  repo.finish_run(run,'SUCCEEDED' if not errors else 'PARTIAL',stored,errors)
  return {'attachments':stored,'scaled_observations':scaled,'bank_observations':bank_values,'errors':errors}
