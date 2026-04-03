import io
import docx

def read_text_file(uploaded_file):
    """
    Reads a standard text file (.txt).
    """
    try:
        # Streamlit uploaded file is a file-like object
        return uploaded_file.getvalue().decode("utf-8")
    except Exception as e:
        return ""

def read_docx_file(uploaded_file):
    """
    Reads a Word document (.docx).
    """
    try:
        doc = docx.Document(uploaded_file)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                 full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        return ""

def load_file(uploaded_file):
    """
    Helper to process the uploaded file based on its extension.
    """
    if uploaded_file is None:
        return ""
        
    filename = uploaded_file.name
    if filename.endswith(".txt"):
        return read_text_file(uploaded_file)
    elif filename.endswith(".docx"):
        return read_docx_file(uploaded_file)
    else:
        # Unsupported format fallback
        return ""
