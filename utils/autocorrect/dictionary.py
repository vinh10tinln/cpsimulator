import os
import pickle
import json

class DictionaryManager:
    def __init__(self, config):
        self.config = config
        self.whitelist = set()
        self.eng_dict = set()
        self.vie_dict = set()
        self.teencode_dict = {}
        
        # Ensure cache dir exists
        os.makedirs(self.config.cache_dir, exist_ok=True)
        
        self._load_whitelist()
        if self.config.enable_eng:
            self._load_eng_dict()
        if self.config.enable_vie:
            self._load_vie_dict()
            
    def _load_whitelist(self):
        for path in self.config.custom_dicts_path:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip().lower()
                        if word:
                            self.whitelist.add(word)
                            
        # Load teencode mapping
        if hasattr(self.config, 'teencode_path') and os.path.exists(self.config.teencode_path):
            with open(self.config.teencode_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) == 2:
                        self.teencode_dict[parts[0].lower()] = parts[1].lower()
                            
    def _load_eng_dict(self):
        cache_file = os.path.join(self.config.cache_dir, 'eng_dict.pkl')
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                self.eng_dict = pickle.load(f)
        elif os.path.exists(self.config.eng_dict_path):
            with open(self.config.eng_dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    w = line.strip().lower()
                    if w and w.isalpha():
                        self.eng_dict.add(w)
            with open(cache_file, 'wb') as f:
                pickle.dump(self.eng_dict, f)
                
    def _load_vie_dict(self):
        cache_file = os.path.join(self.config.cache_dir, 'vie_dict.pkl')
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                self.vie_dict = pickle.load(f)
        elif os.path.exists(self.config.vie_dict_path):
            with open(self.config.vie_dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        w = data.get("text", "").strip().lower()
                    except json.JSONDecodeError:
                        w = line.lower()
                        
                    if w:
                        self.vie_dict.add(w)
            with open(cache_file, 'wb') as f:
                pickle.dump(self.vie_dict, f)

    def is_valid_word(self, token: str) -> bool:
        """Kiểm tra token có nằm trong bất kỳ dictionary/whitelist nào không"""
        t = token.lower()
        if t in self.whitelist:
            return True
        if self.config.enable_vie and t in self.vie_dict:
            return True
        if self.config.enable_eng and t in self.eng_dict:
            return True
        return False
