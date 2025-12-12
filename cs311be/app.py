import os
import uuid
import requests
import streamlit as st
import json

# --- Settings ---
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3005")

# --- Custom CSS for ChatGPT-like interface ---
st.markdown("""
<style>
    /* Main container styling */
    .main-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        max-width: 100%;
    }
    
    /* Chat messages container */
    .chat-container {
        flex: 1;
        overflow-y: auto;
        padding: 20px;
        background-color: #f7f7f8;
        border-radius: 8px;
        margin-bottom: 20px;
        min-height: 400px;
        max-height: 600px;
    }
    
    /* Message styling */
    .message {
        margin-bottom: 20px;
        padding: 12px 16px;
        border-radius: 8px;
        max-width: 80%;
        word-wrap: break-word;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        text-align: right;
    }
    
    .bot-message {
        background-color: white;
        color: #333;
        border: 1px solid #e1e5e9;
        margin-right: auto;
    }
    
    /* Input area styling */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: white;
        padding: 20px;
        border-top: 1px solid #e1e5e9;
        z-index: 1000;
    }
    
    /* Hide Streamlit default elements */
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp > footer {
        visibility: hidden;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #0056b3;
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        border: 2px dashed #007bff;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        border: 1px solid #e1e5e9;
        border-radius: 6px;
        padding: 12px;
    }
    
    /* Success/Error message styling */
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #c3e6cb;
        margin: 10px 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #f5c6cb;
        margin: 10px 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .message {
            max-width: 95%;
        }
        
        .chat-container {
            padding: 10px;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Init session state ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_BACKEND_URL
if "room_id" not in st.session_state:
    st.session_state.room_id = str(uuid.uuid4())
if "resume_data" not in st.session_state:
    st.session_state.resume_data = None
if "job_data" not in st.session_state:
    st.session_state.job_data = None

# --- Header ---
st.markdown("""
<div style="text-align: center; padding: 20px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 20px;">
    <h1 style="margin: 0; font-size: 2.5em;">🧠 PrepAI Chatbot</h1>
    <p style="margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.9;">CV/JD Integration Assistant</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar for settings and file uploads ---
with st.sidebar:
    st.markdown("""
    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e1e5e9;">
        <h3 style="margin-top: 0; color: #333;">⚙️ Settings</h3>
    </div>
    """, unsafe_allow_html=True)
    
    backend_url = st.text_input(
        "Backend URL",
        value=st.session_state.backend_url,
        help="FastAPI base URL, e.g. http://localhost:3005",
    )
    if backend_url:
        st.session_state.backend_url = backend_url.rstrip("/")
    
    if st.button("🗑️ Clear Chat & Data", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.resume_data = None
        st.session_state.job_data = None
        st.rerun()

    st.markdown("---")
    st.markdown("**Session ID:**")
    st.code(st.session_state.room_id, language="text")
    
    st.markdown("---")
    st.markdown("""
    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e1e5e9;">
        <h3 style="margin-top: 0; color: #333;">📁 Upload Files</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # CV Upload
    uploaded_cv = st.file_uploader("📄 Upload CV (PDF/DOCX)", type=["pdf", "docx"])
    if uploaded_cv is not None:
        if st.button("🔍 Extract CV", use_container_width=True):
            with st.spinner("Đang trích xuất CV..."):
                try:
                    files = {"file": (uploaded_cv.name, uploaded_cv.getvalue(), uploaded_cv.type)}
                    data = {"session_id": st.session_state.room_id}
                    resp = requests.post(
                        f"{st.session_state.backend_url}/chat/extract-cv/", 
                        files=files, 
                        data=data,
                        timeout=120
                    )
                    resp.raise_for_status()
                    result = resp.json()
                    st.session_state.resume_data = result.get("resume_data")
                    st.markdown('<div class="success-message">✅ CV extracted and stored successfully!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="error-message">❌ Lỗi trích xuất CV: {e}</div>', unsafe_allow_html=True)

    # JD Input
    jd_text = st.text_area("📋 Paste Job Description (optional)", height=120, placeholder="Paste the job description here...")
    if st.button("🔍 Extract JD", use_container_width=True) and jd_text.strip():
        with st.spinner("Đang trích xuất JD..."):
            try:
                data = {
                    "job_description": jd_text,
                    "session_id": st.session_state.room_id
                }
                resp = requests.post(
                    f"{st.session_state.backend_url}/chat/extract-job/",
                    data=data,
                    timeout=120,
                )
                resp.raise_for_status()
                result = resp.json()
                st.session_state.job_data = result.get("job_data")
                st.markdown('<div class="success-message">✅ Job details extracted and stored successfully!</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="error-message">❌ Lỗi trích xuất JD: {e}</div>', unsafe_allow_html=True)

    # Show stored data status
    if st.session_state.resume_data:
        st.markdown("---")
        st.markdown("**📄 CV Data:** ✅ Loaded")
        with st.expander("View CV Data"):
            st.json(st.session_state.resume_data)
    
    if st.session_state.job_data:
        st.markdown("---")
        st.markdown("**📋 JD Data:** ✅ Loaded")
        with st.expander("View JD Data"):
            st.json(st.session_state.job_data)

    st.markdown("---")
    st.markdown("**📄 Báo cáo phỏng vấn (PDF)**")
    if st.button("Tạo & tải báo cáo PDF", use_container_width=True):
        try:
            resp = requests.get(
                f"{st.session_state.backend_url}/chat/final-report/{st.session_state.room_id}",
                timeout=120,
            )
            resp.raise_for_status()
            payload = resp.json()
            import base64
            pdf_bytes = base64.b64decode(payload.get("data_base64", ""))
            filename = payload.get("filename", f"interview_report_{st.session_state.room_id}.pdf")
            st.download_button(
                label="⬇️ Tải báo cáo PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"❌ Không thể tạo báo cáo: {e}")

# --- Main chat interface ---
st.markdown("""
<div style="display: flex; flex-direction: column; height: calc(100vh - 200px);">
    <div class="chat-container">
""", unsafe_allow_html=True)

# Display chat history
if not st.session_state.chat_history:
    st.markdown("""
    <div style="text-align: center; padding: 40px; color: #666;">
        <h3>👋 Welcome to PrepAI Chatbot!</h3>
        <p>Start a conversation by typing a message below.</p>
        <p><strong>Tip:</strong> Upload your CV and JD first for better responses.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="message user-message">
                <strong>You:</strong><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="message bot-message">
                <strong>PrepAI:</strong><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- Input area at bottom ---
st.markdown("""
<div class="input-container">
    <div style="max-width: 800px; margin: 0 auto;">
""", unsafe_allow_html=True)

# User input form
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "Type your message here...",
            placeholder="Ask me anything about your CV, JD, or interview preparation...",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("Send", use_container_width=True)

st.markdown("</div></div>", unsafe_allow_html=True)

# --- Handle user message ---
if submitted and query:
    st.session_state.chat_history.append({"role": "user", "content": query})
    with st.spinner("🤔 Thinking..."):
        try:
            url = f"{st.session_state.backend_url}/chat/chatDomain"
            payload = {
                "room_id": st.session_state.room_id,
                "query": query
            }
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("response", "")
        except Exception as e:
            answer = f"❌ Không thể kết nối API: {e}"

    if answer:
        st.session_state.chat_history.append({"role": "agent", "content": answer})
        st.rerun()

# --- Instructions in expander ---
with st.expander("ℹ️ How to use PrepAI"):
    st.markdown("""
    ### 📋 Usage Guide:
    
    1. **📄 Upload CV**: Upload your CV file (PDF/DOCX) and click "Extract CV"
    2. **📋 Add JD**: Paste the job description and click "Extract JD"  
    3. **💬 Chat**: Start chatting! PrepAI will use your CV/JD information to provide personalized responses
    
    ### 🎯 What you can ask:
    - "Create interview questions based on my CV and the job description"
    - "How well does my CV match this job?"
    - "Suggest improvements for my CV"
    - "What skills should I highlight for this position?"
    - "Generate a cover letter for this job"
    
    ### 🔧 API Endpoints:
    - `POST /chat/extract-cv/` - Extract and store CV data
    - `POST /chat/extract-job/` - Extract and store JD data
    - `POST /chat/chatDomain` - Chat with AI agent
    - `GET /chat/session-context/{session_id}` - Get session CV/JD data
    """)

# --- Footer ---
st.markdown("""
<div style="text-align: center; padding: 20px; color: #666; font-size: 0.9em;">
    <p>Powered by PrepAI • Built with Streamlit • CV/JD Integration</p>
</div>
""", unsafe_allow_html=True)