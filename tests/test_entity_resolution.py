import unittest
from uzquant.security_master import normalize_name
class ResolutionTests(unittest.TestCase):
    def test_exact_normalization(self): self.assertEqual(normalize_name("<Kapital sug'urta> AJ"),normalize_name("Kapital sug'urta AJ"))
    def test_fuzzy_names_are_not_merged(self): self.assertNotEqual(normalize_name("Ipak Yoli Bank"),normalize_name("Ipak Yo'li"))
if __name__=="__main__": unittest.main()
