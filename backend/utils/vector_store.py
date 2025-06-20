import os
import shutil
from langchain_community.vectorstores import FAISS
from .embeddings import get_embedding_model

INDEX_PATH = os.path.join(os.path.dirname(__file__), '../../uploads/faiss_index')

def build_faiss_index(chunks):
    # Delete old index if it exists
    if os.path.exists(INDEX_PATH):
        shutil.rmtree(INDEX_PATH)
    embeddings = get_embedding_model()
    db = FAISS.from_texts(chunks, embeddings)
    db.save_local(INDEX_PATH)
    return INDEX_PATH

def load_faiss_index():
    embeddings = get_embedding_model()
    db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    return db 