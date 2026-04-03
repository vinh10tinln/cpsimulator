from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .preprocess import clean_text

def calculate_overall_similarity(text1, text2):
    """
    Calculates the overall similarity between text1 and text2.
    """
    cleaned1 = clean_text(text1)
    cleaned2 = clean_text(text2)
    
    if not cleaned1 or not cleaned2:
         return 0.0
         
    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([cleaned1, cleaned2])
        sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return float(sim_matrix[0][0])
    except ValueError:
        # Happens if texts only contain stop words or unvectorizable tokens
        return 0.0

def calculate_local_similarity(segments1, segments2):
    """
    Compares segments of document 1 against segments of document 2
    to find the localized regions of similarity (plagiarized regions).
    Returns a list of dictionaries with matching information.
    """
    if not segments1 or not segments2:
        return []
        
    vectorizer = TfidfVectorizer()
    all_segments = segments1 + segments2
    try:
         tfidf_matrix = vectorizer.fit_transform(all_segments)
    except ValueError:
         return []
         
    tfidf_doc1 = tfidf_matrix[:len(segments1)]
    tfidf_doc2 = tfidf_matrix[len(segments1):]
    
    similarity_matrix = cosine_similarity(tfidf_doc1, tfidf_doc2)
    
    results = []
    # For each segment in doc 2, find the best matching segment in doc 1
    for i, seg2 in enumerate(segments2):
        best_match_idx = np.argmax(similarity_matrix[:, i])
        best_sim_score = float(similarity_matrix[best_match_idx, i])
        
        results.append({
            'doc2_index': i,
            'doc2_text': seg2,
            'doc1_index': int(best_match_idx),
            'doc1_text': segments1[best_match_idx],
            'similarity_score': best_sim_score
        })
        
    return results

def classify_similarity(score, low_threshold=0.3, high_threshold=0.7):
    """
    Classifies a similarity score into Low, Medium, High.
    """
    if score >= high_threshold:
        return "High"
    elif score >= low_threshold:
        return "Medium"
    else:
         return "Low"

def calculate_target_coverage(target_segments, all_refs_segments_dict):
    """
    Computes the maximum similarity for each segment in the target document
    across a dictionary of multiple reference files to find overall Coverage.
    all_refs_segments_dict: dict of { "filename": [list_of_segments] }
    Returns:
       coverage_results: List of dicts mapping each target segment to its best matching file and score.
    """
    if not target_segments or not all_refs_segments_dict:
        return []
        
    vectorizer = TfidfVectorizer()
    
    # Flatten all text to fit the vectorizer
    all_text = target_segments.copy()
    ref_file_map = [] # To keep track of which mapped segment belongs to which file
    
    for filename, ref_segs in all_refs_segments_dict.items():
        all_text.extend(ref_segs)
        ref_file_map.extend([(filename, seg, i) for i, seg in enumerate(ref_segs)])
        
    try:
        tfidf_matrix = vectorizer.fit_transform(all_text)
    except ValueError:
        return []

    tfidf_target = tfidf_matrix[:len(target_segments)]
    tfidf_refs = tfidf_matrix[len(target_segments):]
    
    if tfidf_refs.shape[0] == 0:
        return []
        
    similarity_matrix = cosine_similarity(tfidf_target, tfidf_refs)
    
    coverage_results = []
    # For each segment in Target A, find the single highest score among ALL reference segments
    for i, target_seg in enumerate(target_segments):
        best_match_idx = np.argmax(similarity_matrix[i, :])
        best_sim_score = float(similarity_matrix[i, best_match_idx])
        
        best_file_name, best_ref_seg, _ = ref_file_map[best_match_idx]
        
        coverage_results.append({
            'target_index': i,
            'target_text': target_seg,
            'best_match_file': best_file_name,
            'best_ref_text': best_ref_seg,
            'similarity_score': best_sim_score
        })
        
    return coverage_results
