import streamlit as st
import pandas as pd
import os
import hashlib
from PyPDF2 import PdfReader
from groq import Groq
from datetime import datetime
from gtts import gTTS
import io
import sqlalchemy
from sqlalchemy import create_engine, text
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
# Database Setup
if "DATABASE_URL" in st.secrets:
    db_url = st.secrets["DATABASE_URL"]
    # Fix for some dialect issues if url starts with 'postgres://'
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
else:
    st.error("🚨 DATABASE_URL missing in secrets!")
    st.stop()

engine = create_engine(db_url)

def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

init_db()


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
                {"role": "system", "content": "You are an expert analyst. Answer strictly based on the provided text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000 
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI Error: {str(e)}"

# =============================
# ROBUST HELPERS
# =============================
@st.cache_data
def extract_text(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    """Fetches all users (For debugging/admin)."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT username, role FROM users"))
        return pd.DataFrame(result.fetchall(), columns=["username", "role"])

def save_user(username, password, role):
    """Saves a new user to the Cloud Database."""
    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (username, password, role) VALUES (:u, :p, :r)"),
                {"u": username, "p": hash_pw(password), "r": role}
            )
            conn.commit()
        return True
    except sqlalchemy.exc.IntegrityError:
        return False # Username already exists
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def authenticate(username, password):
    """Checks credentials against the Cloud Database."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT role FROM users WHERE username = :u AND password = :p"),
            {"u": username, "p": hash_pw(password)}
        ).fetchone()
        
    return result[0] if result else None
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
    st.session_state.current_doc_text = None

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
            role = "Admin" if users.empty else "User"
            if save_user(nu, np, role):
                st.success("Account created! You can now log in.")
            else:
                st.error("Username already taken.")
    st.stop()

# =============================
# MAIN APP INTERFACE
# =============================
st.sidebar.title(f"👤 {st.session_state.role}")
st.sidebar.divider()

st.sidebar.markdown("### 📂 1. Upload Document")
uploaded_file = st.sidebar.file_uploader("Choose a PDF", type="pdf")

if uploaded_file:
    if st.session_state.current_doc_text is None or uploaded_file.name != getattr(st.session_state, 'last_file_name', ''):
        with st.spinner("Processing document..."):
            text = extract_text(uploaded_file)
            if text:
                st.session_state.current_doc_text = text
                st.session_state.last_file_name = uploaded_file.name
                st.sidebar.success("Document loaded!")
            else:
                st.sidebar.error("Could not read PDF text.")

page = st.sidebar.radio("Navigate", ["🏠 Home", "📘 Summary", "🔑 Insights", "❓ Chat", "🎓 Take a Quiz", "🕸️ Knowledge Map"])
st.sidebar.divider()
if st.sidebar.button("Logout"):
    logout()
    st.rerun()

# =============================
# PAGES
# =============================
if page == "🏠 Home":
    st.title("Welcome to SmartDoc AI 🚀")
    st.write("Upload a document in the sidebar to get started.")
    if st.session_state.current_doc_text:
        st.info(f"✅ Currently analyzing: **{st.session_state.last_file_name}**")
        st.write(f"**Document Length:** {len(st.session_state.current_doc_text)} characters")

elif page == "📘 Summary":
    st.header("Document Summary")
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        if st.button("Generate Summary"):
            with st.spinner("Analyzing..."):
                # REDUCED LIMIT to 10,000 chars to avoid Error 413
                doc_preview = st.session_state.current_doc_text[:10000] 
                summary = ai(f"Provide a comprehensive summary of this document:\n\n{doc_preview}")
                st.markdown(summary) # This line already exists

                # ADD THIS LINE BELOW:
                # It uses Google's text-to-speech API (gTTS)
                # You might need to pip install gTTS first
                try:
                    # Create audio in memory
                    tts = gTTS(text=summary, lang='en')
                    audio_bytes = io.BytesIO()
                    tts.write_to_fp(audio_bytes)
    
                    st.audio(audio_bytes, format='audio/mp3')
                except:
                    st.caption("Audio generation requires 'gTTS' library. (pip install gTTS)")

elif page == "🔑 Insights":
    st.header("Key Insights")
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        if st.button("Extract Insights"):
            with st.spinner("Extracting..."):
                # REDUCED LIMIT to 10,000 chars
                doc_preview = st.session_state.current_doc_text[:10000]
                insights = ai(f"Extract the top 5 strategic insights and 5 key facts from this text:\n\n{doc_preview}")
                st.markdown(insights)

elif page == "❓ Chat":
    st.header("Chat with your Document")
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Ask a question about the PDF..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.spinner("Thinking..."):
                # REDUCED LIMIT to 10,000 chars (approx 2,500 tokens)
                # This leaves enough room in the 6,000 token limit for the answer
                context = st.session_state.current_doc_text[:10000] 
                
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

elif page == "🎓 Take a Quiz":
    st.header("🎓 Test Your Knowledge")
    
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        # Button to generate a NEW quiz
        if st.button("Generate New Quiz"):
            with st.spinner("Creating questions..."):
                doc_preview = st.session_state.current_doc_text[:10000]
                
                # Strict prompt to get clean format
                quiz_prompt = f"""
                Generate 3 multiple-choice questions based on this text.
                Format exactly like this:
                
                Q1: [Question text]
                A) [Option]
                B) [Option]
                C) [Option]
                Answer: [Correct Option Letter]
                
                Q2: ...
                
                TEXT:
                {doc_preview}
                """
                
                quiz_content = ai(quiz_prompt)
                st.session_state.quiz_data = quiz_content # Save to session so it doesn't vanish

        # Display the Quiz if it exists
        if "quiz_data" in st.session_state:
            st.markdown("---")
            st.subheader("Quiz")
            
            # Simple parsing to hide answers initially
            # We display the raw AI output but you can use an 'Expander' to hide answers
            
            questions = st.session_state.quiz_data.split("Q")
            
            for q in questions:
                if q.strip():
                    # Clean up formatting a bit
                    full_q = "Q" + q 
                    
                    # Split question from answer to make it interactive
                    if "Answer:" in full_q:
                        q_text, ans_text = full_q.split("Answer:")
                        
                        st.info(q_text) # Show Question
                        with st.expander("👀 Reveal Answer"):
                            st.success(f"Correct Answer: {ans_text}")
                    else:
                        st.write(full_q)
elif page == "🕸️ Knowledge Map":
    st.header("🕸️ Knowledge Graph")
    
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        if st.button("Generate Knowledge Map"):
            with st.spinner("Mapping connections..."):
                doc_preview = st.session_state.current_doc_text[:10000]
                
                # Ask AI to generate Mermaid.js syntax
                graph_prompt = f"""
                Create a Mermaid.js flowchart syntax to visualize the key concepts in this text.
                Use 'graph TD;' format.
                Keep it simple (max 10 nodes).
                Do not use special characters or brackets in node names.
                Example Output:
                graph TD;
                    A[Concept 1] --> B[Concept 2];
                    A --> C[Concept 3];
                    B --> D[Result];
                
                TEXT:
                {doc_preview}
                """
                
                graph_code = ai(graph_prompt)
                
                # Clean up code (sometimes AI adds markdown blocks)
                graph_code = graph_code.replace("```mermaid", "").replace("```", "").strip()
                
                st.markdown(f"```mermaid\n{graph_code}\n```")
                st.info("💡 This graph visualizes how concepts in your document are connected.")
                
