import re

def clean_text(text):
    """
    Basic text cleaning for Vietnamese text.
    Lowercases the text, replaces multiple spaces and newlines with a single space.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_sentences(text):
    """
    Splits text into a list of sentences based on common punctuation marks and newlines.
    Removes very short segments.
    """
    # Split by period, exclamation mark, question mark, or newline
    # Make sure we don't drop the empty strings and filter them out
    segments = re.split(r'[.!?\n]+', text)
    cleaned_segments = []
    
    for seg in segments:
        seg_cleaned = clean_text(seg)
        # Keep segment if it's reasonably long (e.g. at least 3 words)
        if len(seg_cleaned.split()) >= 3:
            cleaned_segments.append(seg_cleaned)
            
    return cleaned_segments
