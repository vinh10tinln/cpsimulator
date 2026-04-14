import re

# Regex rules for ignoring spell check
IGNORE_RULES = [
    # Medical codes like HS123456
    r'\bHS\d{4,}\b',
    # ICD-10 like formats A00-B99, or A00.9
    r'\b[A-Z]\d{2}(?:\.\d{1,2})?\b',
    # Vital signs / Measurements like 120/80mmHg, 500mg
    r'\b\d{1,3}/\d{1,3}mmHg\b',
    r'\b\d+(?:\.\d+)?(?:mg|ml|mcg|kg|cm|mm)\b',
    # Emails
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    # Just numbers
    r'\b\d+\b'
]

compiled_rules = [re.compile(rule, re.IGNORECASE) for rule in IGNORE_RULES]

def is_ignored_by_regex(token: str) -> bool:
    for rule in compiled_rules:
        if rule.match(token):
            return True
    return False

# Noun detection (capitalized words not at start of sentence)
# But since we just process words stream or token stream loosely,
# a simple check for uppercase word can be here.
def is_proper_noun(token: str) -> bool:
    return len(token) > 0 and token[0].isupper() and token.isalpha()
