from typing import List, Tuple
from collections import deque
import re
from .base_matcher import BaseMatcher, MatchResult, get_union_length

class ACNode:
    def __init__(self):
        self.children = {}
        self.fail = None
        self.outputs = [] # Lengths of matched patterns

class AhoCorasickMatcher(BaseMatcher):
    def _build_automaton(self, patterns: List[str]):
        root = ACNode()
        # Insert
        for p in patterns:
            node = root
            for char in p:
                if char not in node.children:
                    node.children[char] = ACNode()
                node = node.children[char]
            node.outputs.append(len(p))
            
        # Failure links (BFS)
        queue = deque()
        for char, child in root.children.items():
            child.fail = root
            queue.append(child)
            
        while queue:
            current = queue.popleft()
            for char, child in current.children.items():
                queue.append(child)
                fail_node = current.fail
                while fail_node and char not in fail_node.children:
                    fail_node = fail_node.fail
                if fail_node:
                    child.fail = fail_node.children[char]
                    child.outputs.extend(child.fail.outputs)
                else:
                    child.fail = root
                    
        return root

    def compare(self, text_a: str, text_b: str) -> MatchResult:
        # Extract 3-word chunks (trigrams) from Text A
        words = [m.group() for m in re.finditer(r'\b\w+\b', text_a)]
        patterns = set()
        for i in range(len(words) - 2):
            patterns.add(" ".join(words[i:i+3]))
            
        if not patterns:
            # Fallback to single words if text is too short
            patterns = set(words)
            
        if not patterns:
            return MatchResult("Aho-Corasick", 0, 0, 0.0, "Văn bản rỗng.", [])

        root = self._build_automaton(list(patterns))
        
        matches = []
        match_count = 0
        node = root
        
        for i, char in enumerate(text_b):
            while node and char not in node.children:
                node = node.fail
            if node:
                node = node.children[char]
                if node.outputs:
                    for p_len in node.outputs:
                        start = i - p_len + 1
                        matches.append((start, i + 1))
                        match_count += 1
            else:
                node = root
                
        matched_length = get_union_length(matches)
        max_len = max(len(text_a), len(text_b))
        sim = (matched_length / max_len) * 100 if max_len > 0 else 0.0
        
        return MatchResult(
            algorithm_name="Aho-Corasick",
            match_count=match_count,
            matched_length=matched_length,
            similarity_percent=min(100.0, sim),
            notes="Dùng Automaton dò đồng thời nhiều cụm 3 từ (Trigram). Rất lý tưởng tìm đoạn văn sao chép mảng ráp, tối ưu tốc độ đỉnh cao.",
            matched_segments=matches
        )
