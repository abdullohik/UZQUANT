import unittest
from uzquant.rse import parse_detail_classes,parse_universe
UNIVERSE=b'''<a href="/isu_infos/STK?isu_cd=UZ700055K015"> AGMKP (&lt;Olmaliq KMK&gt; AJ) </a><a href="/isu_infos/STK?isu_cd=UZ7028660007"> KASU (&lt;Kapital sug'urta&gt; AJ) </a><a href="/isu_infos/STK?isu_cd=UZ7028660007"> KASU (&lt;Kapital sug'urta&gt; AJ) </a>'''
DETAIL=b'''<tr><td>Common share</td><td><a href="/isu_infos/STK?isu_cd=UZ7000550002">UZ7000550002 <br> AGMK</a></td></tr><tr><td>Preferred share</td><td><a href="/isu_infos/STK?isu_cd=UZ700055K015">UZ700055K015 <br> AGMKP</a></td></tr>'''
class ParserTests(unittest.TestCase):
    def test_universe_shape_and_deduplication(self):
        rows=parse_universe(UNIVERSE); self.assertEqual(len(rows),2)
    def test_classes_are_explicit_not_inferred(self):
        result=parse_detail_classes(DETAIL); self.assertEqual(result[("UZ7000550002","AGMK")],"COMMON"); self.assertEqual(result[("UZ700055K015","AGMKP")],"PREFERRED")
if __name__=="__main__": unittest.main()
