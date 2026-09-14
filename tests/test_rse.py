import unittest
from uzquant.rse import parse_daily_history,parse_detail_classes,parse_universe
UNIVERSE=b'''<a href="/isu_infos/STK?isu_cd=UZ700055K015"> AGMKP (&lt;Olmaliq KMK&gt; AJ) </a><a href="/isu_infos/STK?isu_cd=UZ7028660007"> KASU (&lt;Kapital sug'urta&gt; AJ) </a><a href="/isu_infos/STK?isu_cd=UZ7028660007"> KASU (&lt;Kapital sug'urta&gt; AJ) </a>'''
DETAIL=b'''<tr><td>Common share</td><td><a href="/isu_infos/STK?isu_cd=UZ7000550002">UZ7000550002 <br> AGMK</a></td></tr><tr><td>Preferred share</td><td><a href="/isu_infos/STK?isu_cd=UZ700055K015">UZ700055K015 <br> AGMKP</a></td></tr>'''
class ParserTests(unittest.TestCase):
    def test_universe_shape_and_deduplication(self):
        rows=parse_universe(UNIVERSE); self.assertEqual(len(rows),2)
    def test_classes_are_explicit_not_inferred(self):
        result=parse_detail_classes(DETAIL); self.assertEqual(result[("UZ7000550002","AGMK")],"COMMON"); self.assertEqual(result[("UZ700055K015","AGMKP")],"PREFERRED")
    def test_daily_history_and_impossible_price(self):
        good=b'data.push([moment("20260102", "YYYYMMDD")._d.valueOf(),1,2,1,2,10]);'
        self.assertEqual(parse_daily_history(good)[0]["share_volume"],"10")
        bad=b'data.push([moment("20260102", "YYYYMMDD")._d.valueOf(),0,2,1,2,10]);'
        with self.assertRaises(ValueError): parse_daily_history(bad)
if __name__=="__main__": unittest.main()
