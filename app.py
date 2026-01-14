import streamlit as st
import pandas as pd
import os
import hashlib
from PyPDF2 import PdfReader
from groq import Groq
from datetime import datetime

# =============================
# APP CONFIG
# =============================
st.set_page_config(
    page_title="SmartDoc AI",
    page_icon="📄",
    layout="wide"
)

# =============================
# STORAGE & SETUP
# =============================
DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# Check for API Key
if "GROQ_API_KEY" not in st.secrets:
    st.error("🚨 GROQ_API_KEY not found in secrets. Please add it to .streamlit/secrets.toml")
    st.stop()

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# =============================
# SMART AI ENGINE
# =============================
def ai(prompt):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert analyst. You answer strictly based on the provided text. Do not hallucinate."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI Error: {str(e)}"

# =============================
# ROBUST HELPERS
# =============================
@st.cache_data
def extract_text(pdf_file):
    """Extracts text from PDF and caches the result for speed."""
    try:
        reader = PdfReader(pdf_file)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def smart_chunk_text(text, target_size=3000):
    """
    Splits text by preserving sentence boundaries instead of hard slicing.
    This prevents cutting words in half.
    """
    chunks = []
    current_chunk = ""
    sentences = text.replace('. ', '.\n').split('\n') # Simple sentence splitter

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < target_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "password", "role", "created_at"])

def save_user(username, password, role):
    df = load_users()
    if username in df['username'].values:
        return False
    
    new_user = pd.DataFrame({
        "username": [username],
        "password": [hash_pw(password)],
        "role": [role],
        "created_at": [datetime.now()]
    })
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USERS_FILE, index=False)
    return True

def authenticate(username, password):
    df = load_users()
    if df.empty: return None
    
    user = df[(df.username == username) & (df.password == hash_pw(password))]
    return user.iloc[0]["role"] if not user.empty else None

# =============================
# SESSION MANAGEMENT
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_doc_text" not in st.session_state:
    st.session_state.current_doc_text = None

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.current_doc_text = None # Clear data on logout
    st.rerun()

# =============================
# AUTH SCREEN
# =============================
if not st.session_state.logged_in:
    st.markdown("## 📄 SmartDoc AI")
    st.info("Log in to access your intelligent document assistant.")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            role = authenticate(u, p)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab2:
        nu = st.text_input("Pick a Username")
        np = st.text_input("Pick a Password", type="password")
        if st.button("Create Account"):
            users = load_users()
            role = "Admin" if users.empty else "User" # First user is always Admin
            if save_user(nu, np, role):
                st.success("Account created! You can now log in.")
            else:
                st.error("Username already taken.")
    
    st.stop() # Stop execution here if not logged in

# =============================
# MAIN APP INTERFACE
# =============================
# 

st.sidebar.title(f"👤 {st.session_state.role}")
st.sidebar.divider()

# --- PERSISTENT FILE UPLOADER ---
# We put this in sidebar so it doesn't disappear when changing pages
st.sidebar.markdown("### 📂 1. Upload Document")
uploaded_file = st.sidebar.file_uploader("Choose a PDF", type="pdf")

if uploaded_file:
    # Only re-process if it's a new file
    if st.session_state.current_doc_text is None or uploaded_file.name != getattr(st.session_state, 'last_file_name', ''):
        with st.spinner("Processing document..."):
            text = extract_text(uploaded_file)
            if text:
                st.session_state.current_doc_text = text
                st.session_state.last_file_name = uploaded_file.name
                st.sidebar.success("Document loaded!")
            else:
                st.sidebar.error("Could not read PDF text.")

# Navigation
page = st.sidebar.radio("Navigate", ["🏠 Home", "📘 Summary", "🔑 Insights", "❓ Chat"])
st.sidebar.divider()
st.sidebar.button("Logout", on_click=logout)

# =============================
# PAGES
# =============================
if page == "🏠 Home":
    st.title("Welcome to SmartDoc AI 🚀")
    st.write("Upload a document in the sidebar to get started.")
    
    if st.session_state.current_doc_text:
        st.info(f"✅ Currently analyzing: **{st.session_state.last_file_name}**")
        st.write(f"**Document Length:** {len(st.session_state.current_doc_text)} characters")
    else:
        st.warning("👈 Please upload a PDF in the sidebar to begin.")

elif page == "📘 Summary":
    st.header("Document Summary")
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        if st.button("Generate Summary"):
            with st.spinner("Analyzing..."):
                # Use first 15k chars to stay within rate limits for summary
                # For full doc summary, you'd need a map-reduce chain (more complex)
                doc_preview = st.session_state.current_doc_text[:15000] 
                summary = ai(f"Provide a comprehensive summary of this document:\n\n{doc_preview}")
                st.markdown(summary)

elif page == "🔑 Insights":
    st.header("Key Insights")
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        if st.button("Extract Insights"):
            with st.spinner("Extracting..."):
                doc_preview = st.session_state.current_doc_text[:15000]
                insights = ai(f"Extract the top 5 strategic insights and 5 key facts from this text:\n\n{doc_preview}")
                st.markdown(insights)

elif page == "❓ Chat":
    st.header("Chat with your Document")
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        # Chat Interface
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Ask a question about the PDF..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.spinner("Thinking..."):
                # RAG Context Injection
                # We simply grab the most relevant chunks or pass the context if small enough
                # For this simple version, we truncate context to fit model context window
                context = st.session_state.current_doc_text[:25000] 
                
                final_prompt = f"""
                Use the following document context to answer the user's question.
                If the answer is not in the text, say you don't know.
                
                DOCUMENT CONTEXT:
                {context}
                
                USER QUESTION:
                {prompt}
                """
                
                response = ai(final_prompt)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)
