import re

def remove_duplicate_chars(word):
    """Xóa các ký tự lặp liên tiếp, ví dụ 'nhannh' -> 'nhanh'"""
    # Chỉ giữ lại tối đa 1 ký tự giống nhau liên tiếp nếu là nguyên âm bị gõ nhầm
    # Đây là mô phỏng regex đơn giản
    return re.sub(r'(.)\1+', r'\1', word)

def get_vie_suggestions(word, dict_set):
    """Generate suggestions for a Vietnamese word."""
    suggestions = []
    
    # Rule 1: Lặp phím gõ nhanh (nhannh -> nhanh)
    deduped = remove_duplicate_chars(word)
    if deduped != word and deduped in dict_set:
        suggestions.append({'word': deduped, 'score': 0.95, 'type': 'duplicate_chars'})
        
    # Lấy các biến thể gõ lỗi Telex đơn giản
    # Ví dụ: thuyr, truongf -> xóa ký tự cuối nếu là f, r, s, j, x
    if word[-1:] in ['f', 'r', 's', 'j', 'x']:
        stripped = word[:-1]
        # Ta cần một logic điền dấu tùy mức độ phức tạp, 
        # Tạm thời chỉ suggest nếu text không cố tình bỏ dấu
        # Thực tế logic này phức tạp hơn (cần symspell hoặc VNI unikey mapping).
        # Tạm giữ ở mức PoC
    
    # Gợi ý đơn giản từ Edit1 (chỉ xài alphabet cơ bản)
    letters = 'aáàảãạăắằẳẵặâấầẩẫậeéèẻẽẹêếềểễệiíìỉĩịoóòỏõọôốồổỗộơớờởỡợuúùủũụưứừửữựyýỳỷỹỵbcdđghklmnpqrstvx'
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    
    candidates = {w for w in (deletes + replaces) if w in dict_set}
    
    for c in candidates:
        if c not in [s['word'] for s in suggestions]:
            suggestions.append({'word': c, 'score': 0.85, 'type': 'edit_distance'})
            
    # Sort by score descending
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    return suggestions
