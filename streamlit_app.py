import streamlit as st
import requests
import os
import re

FASTAPI_URL = "http://localhost:8000"
UPLOADS_DIR = "uploads"

st.set_page_config(page_title="Document Assistant", layout="wide")

# --- Custom CSS for chat bubbles and avatars ---
st.markdown('''
    <style>
    .chat-bubble-user {
        background-color: #f5f5f5;
        color: #222;
        padding: 12px 18px;
        border-radius: 16px 16px 4px 16px;
        margin-bottom: 8px;
        max-width: 70%;
        align-self: flex-end;
        margin-left: auto;
        font-weight: bold;
    }
    .chat-bubble-assistant {
        background-color: #232f3e;
        color: #fff;
        padding: 14px 18px;
        border-radius: 16px 16px 16px 4px;
        margin-bottom: 8px;
        max-width: 70%;
        align-self: flex-start;
        margin-right: auto;
    }
    .chat-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: inline-block;
        vertical-align: middle;
        margin-right: 8px;
        background: #eee;
        text-align: center;
        line-height: 32px;
        font-size: 18px;
    }
    .chat-row {
        display: flex;
        align-items: flex-start;
        margin-bottom: 2px;
    }
    .sidebar-section {
        margin-bottom: 32px;
    }
    </style>
''', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2>📁 Upload Your PDF</h2>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drag and drop file here", type=["pdf", "txt"])
    st.markdown("<div class='sidebar-section'><b>📂 Select an existing PDF</b></div>", unsafe_allow_html=True)
    files = [f for f in os.listdir(UPLOADS_DIR) if f.lower().endswith((".pdf", ".txt"))] if os.path.exists(UPLOADS_DIR) else []
    select_options = ['-'] + files if files else ['-']
    selected_pdf = st.selectbox("", select_options)
    process_btn = st.button("🚀 Process PDF", disabled=not (uploaded_file or (selected_pdf and selected_pdf != '-' and selected_pdf != "No files found")))

# --- SESSION STATE ---
if 'doc_name' not in st.session_state:
    st.session_state['doc_name'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'summary' not in st.session_state:
    st.session_state['summary'] = None

# --- PDF Upload/Selection Logic ---
def process_pdf(uploaded_file, selected_pdf):
    if uploaded_file:
        file_path = os.path.join(UPLOADS_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        with st.spinner("Embedding document..."):
            with open(file_path, "rb") as f:
                files_data = {'file': (uploaded_file.name, f, uploaded_file.type)}
                r = requests.post(f"{FASTAPI_URL}/embed", files=files_data)
        if r.status_code == 200:
            st.session_state['doc_name'] = uploaded_file.name
            st.success("Document uploaded and embedded!")
        else:
            st.error(f"Embedding failed: {r.json().get('error', 'Unknown error')}")
    elif selected_pdf and selected_pdf != '-' and selected_pdf != "No files found":
        st.session_state['doc_name'] = selected_pdf
        st.success(f"Selected document: {selected_pdf}")

if process_btn:
    process_pdf(uploaded_file, selected_pdf)

# --- MAIN AREA ---
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 32px;'>🤖 Document Assistant</h1>
""", unsafe_allow_html=True)

if st.session_state['doc_name']:
    st.markdown(f"<div style='text-align:center; color:#888;'>Currently loaded: <b>{st.session_state['doc_name']}</b></div>", unsafe_allow_html=True)
    st.write("")
    tab1, tab2, tab3 = st.tabs(["📝 Create Summary", "💬 Ask Anything", "🧠 Challenge Me"])

    # --- Create Summary Tab ---
    with tab1:
        if st.button("Generate Summary") or st.session_state.get('summary'):
            if not st.session_state.get('summary'):
                file_path = os.path.join(UPLOADS_DIR, st.session_state['doc_name'])
                with open(file_path, "rb") as f:
                    files_data = {'file': (st.session_state['doc_name'], f, 'application/octet-stream')}
                    s = requests.post(f"{FASTAPI_URL}/summarize", files=files_data)
                if s.status_code == 200:
                    summary = s.json().get('summary', '')
                    st.session_state['summary'] = summary
                else:
                    st.error(f"Summarization failed: {s.json().get('error', 'Unknown error')}")
            if st.session_state.get('summary'):
                st.markdown(f"<div style='background:#232f3e;color:#fff;padding:18px;border-radius:12px;margin-top:16px;'><b>Summary:</b><br>{st.session_state['summary']}</div>", unsafe_allow_html=True)

    # --- Ask Anything Tab (Chat) ---
    with tab2:
        user_input = st.text_input("Type your question here...", key="chat_input")
        ask_btn = st.button("Send", key="send_btn")
        if ask_btn and user_input.strip():
            with st.spinner("Getting answer..."):
                r = requests.post(f"{FASTAPI_URL}/ask", data={'question': user_input})
            if r.status_code == 200:
                answer = r.json().get('answer', '')
                st.session_state['chat_history'].append({
                    "role": "user", "content": user_input
                })
                st.session_state['chat_history'].append({
                    "role": "assistant", "content": answer
                })
            else:
                st.error(f"Error: {r.json().get('error', 'Unknown error')}")
            st.experimental_rerun()
        for msg in st.session_state['chat_history']:
            if msg["role"] == "user":
                st.markdown(
                    f"<div class='chat-row' style='justify-content: flex-end;'><div class='chat-bubble-user'>{msg['content']}</div><div class='chat-avatar'>🧑</div></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='chat-row'><div class='chat-avatar'>🤖</div><div class='chat-bubble-assistant'>{msg['content']}</div></div>",
                    unsafe_allow_html=True,
                )

    # --- Challenge Me Tab ---
    with tab3:
        if 'challenge_questions' not in st.session_state:
            st.session_state['challenge_questions'] = None
        if 'challenge_answers' not in st.session_state:
            st.session_state['challenge_answers'] = []
        if st.button("Generate Challenge Questions") or st.session_state['challenge_questions']:
            if not st.session_state['challenge_questions']:
                file_path = os.path.join(UPLOADS_DIR, st.session_state['doc_name'])
                with open(file_path, "rb") as f:
                    files = {'file': (st.session_state['doc_name'], f, 'application/octet-stream')}
                    with st.spinner("Generating questions..."):
                        r = requests.post(f"{FASTAPI_URL}/generate_questions", files=files)
                    if r.status_code == 200:
                        st.session_state['challenge_questions'] = r.json().get('questions', [])
                        st.session_state['challenge_answers'] = [''] * len(st.session_state['challenge_questions'])
                    else:
                        st.error(f"Error: {r.json().get('error', 'Unknown error')}")
            if st.session_state['challenge_questions']:
                st.markdown("<b>Your Challenge Questions:</b>", unsafe_allow_html=True)
                for i, q in enumerate(st.session_state['challenge_questions'], 1):
                    st.markdown(f"**Q{i}:** {q}")
                    st.session_state['challenge_answers'][i-1] = st.text_input(f"Your answer to Q{i}", key=f"answer_{i}", value=st.session_state['challenge_answers'][i-1])
                if st.button("Submit Answers"):
                    st.subheader("Evaluation & Justification:")
                    for i, ans in enumerate(st.session_state['challenge_answers'], 1):
                        if ans.strip():
                            with st.spinner(f"Evaluating Q{i}..."):
                                r = requests.post(f"{FASTAPI_URL}/evaluate", data={'answer': ans})
                            if r.status_code == 200:
                                score = r.json().get('score', 0)
                                justification = r.json().get('justification', '')
                                icon = '✅' if score else '❌'
                                color = 'green' if score else 'red'
                                st.markdown(f"<span style='color:{color};font-size:1.2em'>{icon}</span> <b>Q{i} Score:</b> {score}", unsafe_allow_html=True)
                                st.markdown(f"Justification: {justification}")
                            else:
                                st.error(f"Error evaluating Q{i}: {r.json().get('error', 'Unknown error')}")
                        else:
                            st.warning(f"Please answer Q{i} before submitting.")
else:
    st.info("Please upload or select a PDF to start chatting.") 