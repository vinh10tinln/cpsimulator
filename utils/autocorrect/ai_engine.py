import difflib
import google.generativeai as genai
import re

def configure_ai(api_key: str):
    genai.configure(api_key=api_key)

def process_text_with_ai(text: str) -> dict:
    """
    Sử dụng Gemini AI để sửa lỗi chính tả theo ngữ cảnh, sau đó dùng difflib
    để so sánh và sinh ra logs lỗi.
    """
    prompt = f"""You are an expert bilingual (Vietnamese/English) copy editor. 
Your task is to fix all spelling errors, missing accents, teencode, and typos in the given text.
IMPORTANT RULES:
1. Preserve all medical terminologies, IDs (like HS123456), and proper nouns exactly as they are.
2. Ensure perfect grammatical context.
3. Replace popular GenZ slangs (thíc, cx, hăm, etc) into standard Vietnamese perfectly according to context.
4. Output ONLY the fully corrected text. Do not add any conversational filler.

Original text:
{text}
"""
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        response = model.generate_content(prompt)
        corrected_text = response.text.strip()
    except Exception as e:
        return {'original': text, 'corrected': text, 'logs': [{'word': 'API_ERROR', 'suggested': str(e), 'applied': False}]}

    # Use difflib to find differences and construct logs
    logs = []
    
    # Simple whitespace split tokenization
    orig_tokens = re.findall(r'\S+|\s+', text)
    corr_tokens = re.findall(r'\S+|\s+', corrected_text)
    
    sm = difflib.SequenceMatcher(None, orig_tokens, corr_tokens)
    
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'replace':
            # It might be multiple tokens replaced by multiple tokens
            orig_str = "".join(orig_tokens[i1:i2]).strip()
            corr_str = "".join(corr_tokens[j1:j2]).strip()
            if orig_str and corr_str and orig_str != corr_str:
                logs.append({
                    'word': orig_str,
                    'suggested': corr_str,
                    'applied': True,
                    'score': 1.0,
                    'note': 'AI Corrected'
                })
        elif tag == 'delete':
            orig_str = "".join(orig_tokens[i1:i2]).strip()
            if orig_str:
                logs.append({
                    'word': orig_str,
                    'suggested': '[Xóa]',
                    'applied': True,
                    'score': 1.0,
                    'note': 'AI Removed'
                })
        elif tag == 'insert':
            corr_str = "".join(corr_tokens[j1:j2]).strip()
            if corr_str:
                logs.append({
                    'word': '[Thêm mới]',
                    'suggested': corr_str,
                    'applied': True,
                    'score': 1.0,
                    'note': 'AI Inserted'
                })

    return {'original': text, 'corrected': corrected_text, 'logs': logs}
