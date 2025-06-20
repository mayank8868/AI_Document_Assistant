import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pdfplumber
import fitz  # PyMuPDF

def load_pdf_text(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
    return text

def load_txt_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_and_split_document(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        text = load_pdf_text(file_path)
    elif ext == '.txt':
        text = load_txt_text(file_path)
    else:
        raise ValueError('Unsupported file type')
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=100,
        length_function=len
    )
    chunks = splitter.split_text(text)
    return chunks 