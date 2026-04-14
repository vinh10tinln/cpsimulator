from typing import List, Tuple

class MatchResult:
    def __init__(self, algorithm_name: str, match_count: int, matched_length: int, 
                 similarity_percent: float, notes: str, matched_segments: List[Tuple[int, int]]):
        self.algorithm_name = algorithm_name
        self.match_count = match_count
        self.matched_length = matched_length
        self.similarity_percent = similarity_percent
        self.notes = notes
        self.matched_segments = matched_segments
        
def get_union_length(intervals: List[Tuple[int, int]]) -> int:
    """Helper to calculate total unique length of overlapping intervals."""
    if not intervals:
        return 0
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    for current in intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return sum(end - start for start, end in merged)

class BaseMatcher:
    def compare(self, text_a: str, text_b: str) -> MatchResult:
        raise NotImplementedError()
