from typing import List, Tuple
import re
from .base_matcher import BaseMatcher, MatchResult, get_union_length

class KMPMatcher(BaseMatcher):
    def _compute_lps(self, pattern: str) -> List[int]:
        m = len(pattern)
        lps = [0] * m
        length = 0
        i = 1
        while i < m:
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1
        return lps

    def _kmp_search(self, text: str, pattern: str) -> List[Tuple[int, int]]:
        if not pattern:
            return []
            
        m = len(pattern)
        n = len(text)
        lps = self._compute_lps(pattern)
        matches = []
        i = 0
        j = 0
        
        while i < n:
            if pattern[j] == text[i]:
                i += 1
                j += 1
            if j == m:
                matches.append((i - j, i))
                j = lps[j - 1]
            elif i < n and pattern[j] != text[i]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1
        return matches

    def compare(self, text_a: str, text_b: str) -> MatchResult:
        # Tách Text A thành các câu (sentences)
        sentences = [s.strip() for s in re.split(r'[.?!]+', text_a) if len(s.strip()) > 10]
        if not sentences:
            sentences = [text_a.strip()] if text_a.strip() else []
            
        matches = []
        match_count = 0
        
        for sentence in sentences:
            found = self._kmp_search(text_b, sentence)
            if found:
                matches.extend(found)
                match_count += len(found)
                
        matched_length = get_union_length(matches)
        max_len = max(len(text_a), len(text_b))
        sim = (matched_length / max_len) * 100 if max_len > 0 else 0.0
        
        return MatchResult(
            algorithm_name="KMP",
            match_count=match_count,
            matched_length=matched_length,
            similarity_percent=min(100.0, sim),
            notes="Chỉ tìm khớp nguyên văn từng câu (Sentence) bằng KMP. Tỉ lệ thường thấp và khắt khe nhất nếu có sửa đổi nhỏ (Dấu câu, khoảng trắng...).",
            matched_segments=matches
        )
