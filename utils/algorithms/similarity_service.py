from typing import List, Dict, Any
from .base_matcher import MatchResult
from .trie_matcher import TrieMatcher
from .hash_matcher import HashMatcher
from .aho_corasick_matcher import AhoCorasickMatcher
from .kmp_matcher import KMPMatcher
from .zfunction_matcher import ZFunctionMatcher

class SimilarityAlgorithmService:
    def __init__(self):
        self.matchers = [
            AhoCorasickMatcher(),
            TrieMatcher(),
            HashMatcher(window_size=15),
            KMPMatcher(),
            ZFunctionMatcher()
        ]

    def compare_all(self, text_a: str, text_b: str) -> List[MatchResult]:
        """Runs text_a and text_b through all matching algorithms and returns results."""
        results = []
        for matcher in self.matchers:
            try:
                res = matcher.compare(text_a, text_b)
                results.append(res)
            except Exception as e:
                # Add fallback result on error
                results.append(MatchResult(
                    algorithm_name=matcher.__class__.__name__,
                    match_count=0,
                    matched_length=0,
                    similarity_percent=0.0,
                    notes=f"Lỗi thực thi: {str(e)}",
                    matched_segments=[]
                ))
        return results
