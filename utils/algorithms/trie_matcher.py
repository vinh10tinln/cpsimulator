from typing import List, Tuple
import re
from .base_matcher import BaseMatcher, MatchResult, get_union_length

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class TrieMatcher(BaseMatcher):
    def __init__(self):
        self.root = TrieNode()
        
    def _insert(self, word: str):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        
    def _search(self, word: str) -> bool:
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def compare(self, text_a: str, text_b: str) -> MatchResult:
        self.root = TrieNode()
        
        # Lọc Keyword (từ >= 4 ký tự) của Văn bản A
        words_a = [m.group().lower() for m in re.finditer(r'\b\w{4,}\b', text_a)]
        unique_words_a = set(words_a)
        for w in unique_words_a:
            self._insert(w)
            
        matches = []
        match_count = 0
        matched_words = set()
        
        # Quét Văn bản B tìm các keyword đã xuất hiện ở A
        for m in re.finditer(r'\b\w{4,}\b', text_b):
            word = m.group().lower()
            if self._search(word):
                matches.append((m.start(), m.end()))
                match_count += 1
                matched_words.add(word)
                
        # Tỉ lệ dựa trên số lượng Keyword hiếm bị bám sát
        total_keywords = max(1, len(unique_words_a))
        sim = (len(matched_words) / total_keywords) * 100
        matched_length = get_union_length(matches)
        
        return MatchResult(
            algorithm_name="Trie (Keyword Analysis)",
            match_count=match_count,
            matched_length=matched_length,
            similarity_percent=min(100.0, sim),
            notes="Chỉ lọc và cài đặt các Từ Khóa Dài (chữ >= 4 ký tự) vào cây Trie. Chuyên dùng để vạch trần chiêu trò Paraphrasing (sửa cấu trúc câu nhưng xài lại 1 đống từ vựng học thuật hiếm).",
            matched_segments=matches
        )
