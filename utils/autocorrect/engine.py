import re
from .config import AutoCorrectConfig
from .dictionary import DictionaryManager
from .regex_filters import is_ignored_by_regex, is_proper_noun
from .eng_validator import get_eng_suggestions
from .vie_validator import get_vie_suggestions

class CorrectionEngine:
    def __init__(self, config: AutoCorrectConfig = None):
        self.config = config or AutoCorrectConfig()
        self.dict_manager = DictionaryManager(self.config)
        
    def _tokenize_with_positions(self, text: str):
        # Find all words (alphanumeric + some special chars handling) and their spans
        # This keeps punctuation intact for replacement
        tokens = []
        for match in re.finditer(r'\b[\w-]+\b', text, re.UNICODE):
            tokens.append({
                'word': match.group(),
                'start': match.start(),
                'end': match.end()
            })
        return tokens

    def process_text(self, text: str) -> dict:
        if not self.config.enabled:
            return {'original': text, 'corrected': text, 'logs': []}
            
        tokens = self._tokenize_with_positions(text)
        corrected_text = text
        logs = []
        
        # We process from end to start so replacement doesn't mess up spans!
        # We process from end to start so replacement doesn't mess up spans!
        for index in range(len(tokens) - 1, -1, -1):
            token_info = tokens[index]
            token = token_info['word']
            start = token_info['start']
            end = token_info['end']
            
            # Context
            prev_token = tokens[index - 1]['word'].lower() if index > 0 else ""
            next_token = tokens[index + 1]['word'].lower() if index < len(tokens) - 1 else ""
            
            # Step 1: Filters
            if is_ignored_by_regex(token):
                logs.append({'word': token, 'status': 'ignored_by_regex'})
                continue
                
            if is_proper_noun(token):
                logs.append({'word': token, 'status': 'ignored_proper_noun'})
                continue

            # Teencode override (MUST BE BEFORE is_valid_word because some teencode maps to valid english letters like 'j', 'cx', etc)
            if token.lower() in self.dict_manager.teencode_dict:
                suggested_word = self.dict_manager.teencode_dict[token.lower()]
                if token.istitle():
                    suggested_word = suggested_word.capitalize()
                elif token.isupper():
                    suggested_word = suggested_word.upper()
                
                corrected_text = corrected_text[:start] + suggested_word + corrected_text[end:]
                logs.append({
                    'word': token, 
                    'suggested': suggested_word, 
                    'applied': True,
                    'score': 1.0,
                    'note': 'teencode'
                })
                continue
                
            if self.dict_manager.is_valid_word(token):
                continue
                
            # Step 2: Generate Suggestions
            candidates = []
            if self.config.enable_vie:
                candidates.extend(get_vie_suggestions(token.lower(), self.dict_manager.vie_dict))
            if self.config.enable_eng and not candidates:
                # If no vie suggestions and eng is enabled
                eng_cands = get_eng_suggestions(token.lower(), self.dict_manager.eng_dict)
                candidates.extend(eng_cands)
                
            # Step 2.5: Context-Aware Boosting based on surrounding dictionary phrases
            for cand in candidates:
                cand_word = cand['word']
                boosted = False
                if prev_token:
                    bigram1 = f"{prev_token} {cand_word}"
                    if bigram1 in self.dict_manager.vie_dict:
                        cand['score'] = min(0.99, cand['score'] + 0.15)
                        boosted = True
                if next_token and not boosted:
                    bigram2 = f"{cand_word} {next_token}"
                    if bigram2 in self.dict_manager.vie_dict:
                        cand['score'] = min(0.99, cand['score'] + 0.15)
                        
            # Sort overall candidates by score
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            if not candidates:
                logs.append({'word': token, 'status': 'no_suggestions'})
                continue
                
            best_cand = candidates[0]
            
            # Match case if original was capitalized
            suggested_word = best_cand['word']
            if token.istitle():
                suggested_word = suggested_word.capitalize()
            elif token.isupper():
                suggested_word = suggested_word.upper()
                
            if self.config.mode == "autocorrect" and best_cand['score'] >= self.config.confidence_threshold:
                # Replace in text
                corrected_text = corrected_text[:start] + suggested_word + corrected_text[end:]
                logs.append({
                    'word': token, 
                    'suggested': suggested_word, 
                    'applied': True,
                    'score': best_cand['score']
                })
            elif self.config.mode in ["suggest_only", "autocorrect"]: # If autocorrect but score < threshold, treat as suggest
                logs.append({
                    'word': token, 
                    'suggestions': candidates, 
                    'applied': False
                })

        # Reverse logs back to original reading order
        logs.reverse()
        return {'original': text, 'corrected': corrected_text, 'logs': logs}
