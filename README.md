# 🧠 Smart Assistant for Research Summarization

## 🚀 Overview
This project is a GenAI-powered assistant that reads, understands, and reasons over user-uploaded research documents (PDF/TXT). It provides:
- **Summary** (≤150 words) on demand
- **Ask Anything**: Contextual, cited answers
- **Challenge Me**: Logic-based question generation, user answer evaluation, and justifications
- **All answers are grounded in the document, with snippet highlighting and citations**

## 🏗️ Architecture

| Layer      | Technology                | Purpose                                  |
|------------|---------------------------|-------------------------------------------|
| Frontend   | Streamlit                 | Interactive, beautiful web UI             |
| Backend    | FastAPI                   | Modular API endpoints for AI logic        |
| Reasoning  | LangChain + HuggingFace   | Chunking, retrieval, QA, QGen, Summarize  |
| Vector DB  | FAISS                     | Fast semantic search over document chunks |
| PDF Parse  | pdfplumber, PyMuPDF       | Robust PDF/TXT text extraction            |

### Reasoning Flow
1. **Upload**: User uploads PDF/TXT → backend extracts, chunks, and embeds content
2. **Summary**: On demand, summarization model generates ≤150 word summary
3. **Ask Anything**: User asks a question → RetrievalQA finds answer chunk → LLM answers with citation/snippet
4. **Challenge Me**: LLM generates a logic-based question → User answers → System evaluates and justifies with doc reference

## 📁 Project Structure
```
GenAI Assistant/
├── backend/                  # FastAPI app
│   ├── main.py               # API endpoints and reasoning logic
│   └── utils/                # Document loader, vector store, embeddings
├── uploads/                  # Uploaded files and FAISS index
├── streamlit_app.py          # Streamlit UI
├── requirements.txt
├── README.md
```

## ⚡ Setup Instructions
```bash
# 1. Clone the repo
# 2. Create a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start FastAPI backend
cd backend
uvicorn main:app --reload

# 5. In a new terminal, start Streamlit frontend
cd ..
streamlit run streamlit_app.py

# Open http://localhost:8501 in your browser
```

## 🧠 Key Features
- Upload PDF/TXT, generate summary on demand
- Ask Anything (contextual QA, with citation)
- Challenge Me (logic-based QGen, answer evaluation, justification)
- All answers grounded in document, with snippet highlighting
- Clean, modern Streamlit UI

## 🏆 Bonus Features
- Memory: Follow-up questions retain context
- Answer highlighting: Shows supporting snippet

## 📹 Click on image to watch the Demo

[![Watch the demo video](https://img.youtube.com/vi/jGRytU9dVSI/0.jpg)](https://youtu.be/jGRytU9dVSI)
