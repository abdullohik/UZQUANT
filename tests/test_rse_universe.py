from pathlib import Path
from uzquant.repository import Repository
from uzquant.rse_universe import Instrument,combine_current_equities,parse_detail_classes,parse_listing,parse_quotation

def test_listing_total_and_classification_are_source_driven():
    body=br'''<script>var DATA = [{"cat":"C","tic":"AAA","isin":"UZ1","name":"\u003cIssuer A\u003e AJ","date":"20260101","cur":"UZS","par":10,"shares":20},{"cat":"B","tic":"BBB","isin":"UZ2","name":"Issuer B","date":"20260102","cur":"UZS","par":0,"shares":0}];</script>'''
    rows,meta=parse_listing(body)
    assert meta=={"source_reported_total":2,"page_count":1,"page_row_counts":[2],"raw_rows":2,"unique_rows":2,"duplicates":0,"has_pagination_links":False}
    assert [row.instrument_class for row in rows]==["COMMON_EQUITY","BOND"]
    assert rows[0].issuer=="<Issuer A> AJ"

def test_listing_detects_pagination_and_duplicates():
    body=b'''<script>var DATA = [{"cat":"C","tic":"AAA","isin":"UZ1","name":"A","date":"20260101","cur":"UZS","par":1,"shares":2},{"cat":"C","tic":"AAA","isin":"UZ1","name":"A","date":"20260101","cur":"UZS","par":1,"shares":2}];</script><a href="?page=2">2</a>'''
    _,meta=parse_listing(body)
    assert meta["page_count"]==2 and meta["duplicates"]==1

def test_quotation_deduplicates_responsive_markup_without_inferring_class():
    anchor=b'<a href="/isu_infos/STK?isu_cd=UZ1"> AAAP (Issuer A) </a>'
    rows=parse_quotation(anchor+anchor)
    assert len(rows)==1 and rows[0].instrument_class=="UNKNOWN"

def test_detail_classification_requires_explicit_label():
    body=b'''<tr><td>Common share</td><td><a href="/isu_infos/STK?isu_cd=UZ1">UZ1<br>AAA</a></td></tr><tr><td>Preferred share</td><td><a href="/isu_infos/STK?isu_cd=UZ2">UZ2<br>AAAP</a></td></tr>'''
    assert parse_detail_classes(body)=={("UZ1","AAA"):"COMMON_EQUITY",("UZ2","AAAP"):"PREFERRED_EQUITY"}

def test_current_universe_is_isin_union_of_listing_and_quotation():
    listing=[Instrument("UZ1","AAA","Issuer","COMMON_EQUITY","listing"),Instrument("UZB","BOND","Issuer","BOND","bond")]
    quotes=[Instrument("UZ2","AAAP","Issuer","UNKNOWN","quote")]
    rows=combine_current_equities(listing,quotes,{("UZ1","AAA"):"COMMON_EQUITY",("UZ2","AAAP"):"PREFERRED_EQUITY"})
    assert [(r.isin,r.instrument_class) for r in rows]==[("UZ1","COMMON_EQUITY"),("UZ2","PREFERRED_EQUITY")]

def test_universe_schema_has_foreign_keys(tmp_path:Path):
    with Repository(tmp_path/"test.sqlite3") as repo:
        repo.initialize()
        assert not repo.connection.execute("PRAGMA foreign_key_check").fetchall()
        assert repo.connection.execute("SELECT 1 FROM sqlite_master WHERE name='rse_universe_captures'").fetchone()
