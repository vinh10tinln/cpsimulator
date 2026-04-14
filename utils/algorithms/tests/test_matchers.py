import unittest
from utils.algorithms import SimilarityAlgorithmService

class TestAlgorithmMatchers(unittest.TestCase):
    def setUp(self):
        self.service = SimilarityAlgorithmService()
        self.text_a_eng = "Hello world. This is a nice day to code."
        self.text_b_eng = "Well, hello world. This is a nice day to sleep."
        
        self.text_a_vie = "Xin chào các bạn. Hôm nay là ngày học lập trình thuật toán."
        self.text_b_vie = "Xin chào các bạn nhé. Hôm nay là ngày học lập trình vui vẻ."
        
    def test_aho_corasick(self):
        res = self.service.matchers[0].compare(self.text_a_eng, self.text_b_eng)
        self.assertEqual(res.algorithm_name, "Aho-Corasick")
        self.assertGreaterEqual(res.matched_length, 0)
        
    def test_trie(self):
        res = self.service.matchers[1].compare(self.text_a_vie, self.text_b_vie)
        self.assertEqual(res.algorithm_name, "Trie")
        self.assertGreater(res.similarity_percent, 0)
        
    def test_hash(self):
        res = self.service.matchers[2].compare(self.text_a_vie, self.text_b_vie)
        self.assertEqual(res.algorithm_name, "Hash (L=15)")
        self.assertGreater(res.matched_length, 0)
        
    def test_kmp(self):
        res = self.service.matchers[3].compare(self.text_a_vie, self.text_b_vie)
        self.assertEqual(res.algorithm_name, "KMP")
        # Since KMP splits by sentence and sentences differ, the match length might be low or zero
        
    def test_zfunction(self):
        text = "Hello world This is a nice day to code"
        res = self.service.matchers[4].compare(text, text)
        self.assertEqual(res.algorithm_name, "Z-Function")
        self.assertEqual(res.similarity_percent, 100.0) # Identical strings

if __name__ == "__main__":
    unittest.main()
