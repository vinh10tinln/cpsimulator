# Anti-Plagiarism Demo

This is a simple student demonstration project for a 3-person, 3-week computing/informatics assignment focused on academic plagiarism detection in Vietnamese.

## Project Scope
This project uses **TF-IDF Vectorization** and **Cosine Similarity** to compare uploaded documents. 
It supports advanced batch processing to find plagiarism signatures across an entire dataset without double counting overlaps!

## Features
- **Upload target & reference documents** (`.txt` and `.docx` supported).
- **Two Flexible Modes**: 
  1. `1 vs 1`: Compare a target document against a single reference document.
  2. `Batch (1 vs Many)`: Upload one target document and multiple reference documents at once.
- Advanced metric calculations including **Top Match** and true **Coverage**.

## Batch Mode Scoring System
- **Overall Similarity (Per File)**: The direct mathematical similarity between the entire Target File and one Reference File.
- **Top Match**: The single Reference File that holds the highest Overall Similarity score with the Target File.
- **Coverage**: The true proportion of the Target File that contains suspicious (plagiarized) text. This algorithm scans the union of all matches, guaranteeing that if multiple reference files share the same plagiarized sentence, that sentence is still only counted *once* in the final coverage percentage.
- **Final Risk**: A synthesized conclusion grading the Target File as *High, Medium, Low, or Minimal* risk, heavily weighted by **Coverage** (scale) but also considering **Top Match** (intensity).

## Project Structure
- `app.py`: The Main Streamlit interface containing both modes.
- `utils/`: Core Logic modules (`preprocess.py`, `similarity.py`, `file_loader.py`).
- `sample_data/`: Includes robust sample files designed to test logic limits (e.g., completely unrelated text vs highly plagiarized vs medium rewritten text).
- `requirements.txt`: Python package requirements.

## How to Run & Demo in Class
1. Open a terminal and navigate to the project directory:
   ```bash
   cd anti_plagiarism_demo
   ```
2. Activate your virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

**Demoing the Logic**:
1. Select "So sánh nhiều tài liệu (Batch)" from the sidebar.
2. Upload `doc1_original.txt` as your Target Document.
3. Upload all four reference files (`batch_ref_1...` through `batch_ref_4...`) into the "References" slot simultaneously.
4. Explain the **Final Risk Assessment** dashboard. Point to the **Coverage** percentage and explain how it prevents double-counting overlaps. 
5. Under **"Chi tiết Độ Bao Phủ"**, unfold the accordion. It will show sentence-by-sentence what part of the Target was matched, and *which* reference file had the absolute highest similarity for that specific sentence!

## Limitations
1. **Sentence Fragmentation**: Splitting by standard delimiters might occasionally fragment acronyms if not heavily pre-processed.
2. **Advanced Paraphrasing**: Since TF-IDF correlates exact word frequencies, the application may fail to identify highly "spun" content where complex synonyms fully overwrite original words.
3. **No External Crawling**: This system strictly tests locally provided documents against each other. It does not scrape the internet for copied text.
