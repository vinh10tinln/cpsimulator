from typing import List, Tuple
import re
from .base_matcher import BaseMatcher, MatchResult, get_union_length

class ZFunctionMatcher(BaseMatcher):
    def _z_function(self, s: str) -> List[int]:
        n = len(s)
        Z = [0] * n
        l, r = 0, 0
        for i in range(1, n):
            if i > r:
                l, r = i, i
                while r < n and s[r - l] == s[r]:
                    r += 1
                Z[i] = r - l
                r -= 1
            else:
                k = i - l
                if Z[k] < r - i + 1:
                    Z[i] = Z[k]
                else:
                    l = i
                    while r < n and s[r - l] == s[r]:
                        r += 1
                    Z[i] = r - l
                    r -= 1
        return Z

    def compare(self, text_a: str, text_b: str) -> MatchResult:
        # Tìm mọi điểm bắt đầu của các từ trong Text A (Word boundaries)
        boundaries = [m.start() for m in re.finditer(r'\b\w+\b', text_a)]
        
        # Phòng ngừa văn bản quá lớn làm treo Python (giới hạn 300 điểm neo)
        if len(boundaries) > 300:
            step = len(boundaries) // 300
            boundaries = boundaries[::step]
            
        max_z_len = 0
        best_match_segment = None
        match_count = 0
        matches = []
        
        for i in boundaries:
            # Thuật toán Z quét tiền tố Text_A[i:] ghép với Text_B
            pattern = text_a[i:]
            concat = pattern + "$" + text_b
            pat_len = len(pattern)
            
            Z = self._z_function(concat)
            
            for j in range(pat_len + 1, len(concat)):
                val = Z[j]
                if val > 15: # Chỉ ghi nhận các khối copy dài hơn 15 ký tự
                    start_in_b = j - pat_len - 1
                    matches.append((start_in_b, start_in_b + val))
                    match_count += 1
                    if val > max_z_len:
                        max_z_len = val
                        best_match_segment = (start_in_b, start_in_b + val)
                        
        matched_length = get_union_length(matches)
        
        # Tỉ lệ bằng: Chiều dài Block sao chép lớn nhất / Tổng dung lượng văn bản
        max_len = max(len(text_a), len(text_b))
        sim = (max_z_len / max_len) * 100 if max_len > 0 else 0.0
        
        return MatchResult(
            algorithm_name="Z-Function (Longest Block)",
            match_count=match_count,
            matched_length=max_z_len, # Report the longest block size for Z-func
            similarity_percent=min(100.0, sim),
            notes="Dùng mảng Z-array dò Longest Common Substring. Phát hiện chính xác khối liền mạch vĩ đại nhất (Longest Copy-Pasted Block) bị sao chép y nguyên.",
            matched_segments=[best_match_segment] if best_match_segment else []
        )
