from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
from utils.document_loader import load_and_split_document
from utils.vector_store import build_faiss_index, load_faiss_index
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline, AutoTokenizer
import traceback
import string

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../uploads'))

app = FastAPI()

@app.post('/embed')
def embed(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, 'wb') as f:
            f.write(file.file.read())
        chunks = load_and_split_document(file_path)
        print(f"Total chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i+1}: {chunk[:200]}")
        build_faiss_index(chunks)
        return {"status": "Document embedded and indexed.", "chunks": len(chunks)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post('/summarize')
def summarize(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, 'wb') as f:
            f.write(file.file.read())
        chunks = load_and_split_document(file_path)
        if not chunks or not any(chunks):
            return JSONResponse(status_code=400, content={"error": "No extractable text found in the document."})
        text = " ".join(chunks)
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
        # Truncate to 1024 tokens
        inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
        input_text = tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)
        summary = summarizer(input_text, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
        return {"summary": summary}
    except Exception as e:
        tb = traceback.format_exc()
        print("\n--- Exception in /summarize endpoint ---\n", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb})

@app.post('/ask')
def ask(question: str = Form(...)):
    try:
        db = load_faiss_index()
        results = db.similarity_search_with_score(question, k=3)
        threshold = 10.0  # Accept any match for debugging
        results = sorted(results, key=lambda x: x[1])
        print(f"\nQuestion: {question}")
        for idx, (doc, score) in enumerate(results):
            print(f"Result {idx+1}: Score={score}, Chunk={doc.page_content[:200]}")
        if not results or results[0][1] > threshold:
            print(f"No relevant chunk found. Top score: {results[0][1] if results else 'N/A'}")
            return {"answer": "No relevant information found in the document for your question.", "citation": "N/A", "snippet": ""}
        doc, score = results[0]
        print(f"Top score: {score}\nTop chunk: {doc.page_content[:120]}")
        # Use TinyLlama for text generation
        hf_pipeline = pipeline(
            "text-generation",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            max_new_tokens=256,
            device=-1
        )
        prompt = f"Context: {doc.page_content}\n\nQuestion: {question}\nAnswer (in 2-3 sentences, concise and to the point):"
        output = hf_pipeline(prompt)[0]
        answer = output.get('generated_text') or output.get('text')
        citation = getattr(doc, 'metadata', {}).get('source', 'chunk_1')
        snippet = doc.page_content
        return {"answer": answer.strip(), "citation": citation, "snippet": snippet}
    except Exception as e:
        tb = traceback.format_exc()
        print("\n--- Exception in /ask endpoint ---\n", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb})

@app.post('/generate_questions')
def generate_questions(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, 'wb') as f:
            f.write(file.file.read())
        chunks = load_and_split_document(file_path)
        if not chunks or not any(chunks):
            return JSONResponse(status_code=400, content={"error": "No extractable text found in the document."})
        # Sample from multiple chunks: start, middle, end
        num_chunks = len(chunks)
        selected_chunks = []
        if num_chunks >= 3:
            selected_chunks = [chunks[0], chunks[num_chunks//2], chunks[-1]]
        else:
            selected_chunks = chunks[:3]
        sampled_text = " ".join(selected_chunks)
        hf_pipeline = pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            max_new_tokens=256,
            device=-1
        )
        tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
        # Truncate to 512 tokens
        inputs = tokenizer(sampled_text, return_tensors="pt", max_length=512, truncation=True)
        input_text = tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)
        prompt = (
            "Generate 1 unique, logic-based question that requires reasoning and cannot be answered by simple lookup. "
            "The question must be about a non-trivial aspect of the content below.\nContent:\n" + input_text
        )
        output = hf_pipeline(prompt)[0].get('generated_text') or hf_pipeline(prompt)[0].get('text')
        # Extract the first question (if the model numbers it, remove the number)
        question = output.strip().lstrip('1234567890. ').strip()
        return {"questions": [question]}
    except Exception as e:
        tb = traceback.format_exc()
        print("\n--- Exception in /generate_questions endpoint ---\n", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb})

@app.post('/evaluate')
def evaluate(answer: str = Form(...)):
    try:
        db = load_faiss_index()
        retriever = db.as_retriever()
        docs = retriever.get_relevant_documents(answer)
        if docs:
            snippet = docs[0].page_content
            justification = f"Your answer is supported by: '{snippet[:120]}...'"
            score = 1
        else:
            justification = "No supporting evidence found in the document."
            score = 0
        return {"score": score, "justification": justification}
    except Exception as e:
        tb = traceback.format_exc()
        print("\n--- Exception in /evaluate endpoint ---\n", tb)
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb}) 