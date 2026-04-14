from typing import List, Tuple
from .base_matcher import BaseMatcher, MatchResult, get_union_length

class HashMatcher(BaseMatcher):
    def __init__(self, window_size=15):
        self.window = window_size
        self.base = 256
        self.prime = 101

    def _get_hash(self, text: str, length: int) -> int:
        h = 0
        for i in range(length):
            h = (h * self.base + ord(text[i])) % self.prime
        return h

    def compare(self, text_a: str, text_b: str) -> MatchResult:
        if len(text_a) < self.window or len(text_b) < self.window:
            return MatchResult("Hash (Rolling)", 0, 0, 0.0, "Văn bản quá ngắn so với window hash.", [])
            
        # Hash all windows of length L in Text A and store positions
        hashes_a = {}
        h = self._get_hash(text_a, self.window)
        h_pow = pow(self.base, self.window - 1, self.prime)
        
        hashes_a[h] = [0]
        for i in range(1, len(text_a) - self.window + 1):
            h = (self.base * (h - ord(text_a[i - 1]) * h_pow) + ord(text_a[i + self.window - 1])) % self.prime
            hashes_a.setdefault(h, []).append(i)
            
        matches = []
        match_count = 0
        
        # Rolling hash on Text B
        hb = self._get_hash(text_b, self.window)
        
        def check_collision(idx_b, hb_val):
            nonlocal match_count
            if hb_val in hashes_a:
                str_b = text_b[idx_b:idx_b + self.window]
                for idx_a in hashes_a[hb_val]:
                    if text_a[idx_a:idx_a + self.window] == str_b:
                        matches.append((idx_b, idx_b + self.window))
                        match_count += 1
                        break
        
        check_collision(0, hb)
        for i in range(1, len(text_b) - self.window + 1):
            hb = (self.base * (hb - ord(text_b[i - 1]) * h_pow) + ord(text_b[i + self.window - 1])) % self.prime
            check_collision(i, hb)
            
        matched_length = get_union_length(matches)
        max_len = max(len(text_a), len(text_b))
        sim = (matched_length / max_len) * 100 if max_len > 0 else 0.0
        
        return MatchResult(
            algorithm_name=f"Hash (L={self.window})",
            match_count=match_count,
            matched_length=matched_length,
            similarity_percent=min(100.0, sim),
            notes=f"Dùng Rolling Hash cửa sổ {self.window} ký tự. Khắc phục được lỗi tráo đổi cụm từ, nhận diện mạnh ranh giới copy vụn vặt.",
            matched_segments=matches
        )
