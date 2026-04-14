# Anti-Plagiarism & Multilingual Auto-Correct System

This is a comprehensive demonstration project for academic plagiarism detection and multilingual auto-correction. It features dual capabilities: finding similarities across multiple documents to detect plagiarism strings, and an advanced AI-powered engine for spelling correction.

## Features

1. **Plagiarism Detection (Batch Processing)**:
   - **TF-IDF Vectorization** and **Cosine Similarity** to compare uploaded documents.
   - **Batch Mode (1 vs Many)**: Compare a target document against multiple reference files simultaneously.
   - **Intelligent Coverage**: Analyzes similarities at the segment level to avoid double-counting text that appears in multiple reference files.
   - **Multiple String Matchers**: Includes Aho-Corasick, KMP, Trie, Hash, and Z-function matchers for versatile and robust string comparison logic.
   - **Final Risk Assessment**: Generates a unified plagiarism risk score (Low, Medium, High).

2. **Multilingual Auto-Correct Engine**:
   - Dedicated UI mode for spell checking and auto-correction.
   - Supported languages: English and Vietnamese (includes teencode normalization).
   - Domain-specific whitelist functionality.
   - **AI-Powered Context Engine**: Integrated with Google Gemini to handle complex language nuances and context-dependent spelling errors.

## Project Structure
- `app.py`: The Main Streamlit interface containing both modes.
- `utils/`: Core Logic modules.
   - `utils/algorithms/`: Specialized string matching algorithms.
   - `utils/autocorrect/`: Spell check validation, dictionaries, and AI integration via Gemini.
- `sample_data/`: Sample text files designed to test the application's capabilities.
- `requirements.txt`: Python dependencies.

## Installation & Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/emton6969/cp-simulator.git
   cd cp-simulator
   ```

2. Create and activate a python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

If you want to use the AI autocorrect feature, you will need a Google Gemini API key.
You can input your key directly into the app's sidebar during runtime, or set it securely in the environment.

## Running the App

To launch the Streamlit frontend, simply run:

```bash
streamlit run app.py
```

Open the local URL generated (usually `http://localhost:8501`) in your browser. You can navigate between the "Plagiarism Detection" (So sánh Batch) and "Auto-Correct" (Sửa lỗi chính tả) tabs in the sidebar.
