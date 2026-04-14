import os
from dataclasses import dataclass, field

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@dataclass
class AutoCorrectConfig:
    enabled: bool = True
    mode: str = "autocorrect" # 'autocorrect', 'suggest_only', 'spellcheck_only'
    confidence_threshold: float = 0.85
    enable_vie: bool = True
    enable_eng: bool = True
    
    eng_dict_path: str = os.path.join(BASE_DIR, "data", "dicts", "eng_words.txt")
    vie_dict_path: str = os.path.join(BASE_DIR, "data", "dicts", "vie_words.txt")
    teencode_path: str = os.path.join(BASE_DIR, "data", "dicts", "teencode.txt")
    custom_dicts_path: list = field(default_factory=lambda: [os.path.join(BASE_DIR, "data", "dicts", "hospital_whitelist.txt")])
    
    # Internal cache paths
    cache_dir: str = os.path.join(BASE_DIR, "data", "cache")

