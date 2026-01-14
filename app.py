import streamlit as st
import pandas as pd
import os
import hashlib
from PyPDF2 import PdfReader
from groq import Groq
from datetime import datetime

# =============================
# CONFIG
# =============================
st.set_page_config(
    page_title="SmartDoc AI",
    page_icon="📄",
    layout="wide"
)

USERS_FILE = "data/users.csv"
os.makedirs("data", exist_ok=True)

from supabase import create_client

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_ANON_KEY"]
)

# =============================
# GROQ CLIENT
# =============================
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def groq_generate(prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an enterprise document intelligence assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# =============================
# HELPERS
# =============================
def chunk_text(text, size=2500):
    return [text[i:i+size] for i in range(0, len(text), size)]

def extract_text(pdf):
    reader = PdfReader(pdf)
    return "".join(page.extract_text() or "" for page in reader.pages)

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "password", "role", "created_at"])

def save_user(username, password, role):
    df = load_users()
    df.loc[len(df)] = [
        username,
        hash_password(password),
        role,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ]
    df.to_csv(USERS_FILE, index=False)

def authenticate(username, password):
    df = load_users()
    pw = hash_password(password)
    user = df[(df.username == username) & (df.password == pw)]
    if not user.empty:
        return user.iloc[0]["role"]
    return None

# =============================
# SESSION STATE
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "stats" not in st.session_state:
    st.session_state.stats = {"docs": 0, "queries": 0}

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# =============================
# AUTH UI
# =============================
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.markdown("## 📄 SmartDoc AI")
    st.markdown("### Enterprise Document Intelligence Platform")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user = res.user
                st.rerun()
            except Exception:
                st.error("Invalid email or password")

    with tab2:
        email = st.text_input("New Email")
        password = st.text_input("New Password", type="password")

        if st.button("Register"):
            try:
                supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                st.success("Account created. Please login.")
            except Exception:
                st.error("User already exists or invalid email")

    st.stop()


# =============================
# SIDEBAR
# =============================
st.sidebar.markdown("## 📂 SmartDoc AI")
st.sidebar.success(f"Role: {st.session_state.role}")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "📊 Dashboard",
        "📘 Document Summary",
        "❓ Ask Questions",
        "🔑 Keyword Extraction",
    ] + (["🗂️ User Management"] if st.session_state.role == "Admin" else [])
)

st.sidebar.button("🚪 Logout", on_click=logout)

# =============================
# PAGES
# =============================
if page == "🏠 Home":
    st.markdown("## 👋 Welcome to SmartDoc AI")
    st.write(
        "SmartDoc AI helps enterprises, students, and professionals "
        "analyze large documents using fast AI models."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("AI Engine", "Groq LLaMA 3.1")
    c2.metric("Documents Processed", st.session_state.stats["docs"])
    c3.metric("AI Queries", st.session_state.stats["queries"])

elif page == "📊 Dashboard":
    st.markdown("## 📊 Usage Dashboard")

    st.metric("Total Documents", st.session_state.stats["docs"])
    st.metric("Total AI Queries", st.session_state.stats["queries"])

    st.info("Analytics can be extended with Supabase or Azure SQL.")

elif page == "📘 Document Summary":
    st.markdown("## 📘 Document Summary")

    pdf = st.file_uploader("Upload PDF", type="pdf")

    if pdf:
        text = extract_text(pdf)

        if len(text.strip()) < 100:
            st.error("PDF contains no readable text.")
            st.stop()

        chunks = chunk_text(text)[:4]
        summaries = []

        with st.spinner("Analyzing document with AI..."):
            for chunk in chunks:
                summaries.append(
                    groq_generate(
                        f"Summarize this document section in bullet points:\n{chunk}"
                    )
                )

            final_summary = groq_generate(
                "Combine the following summaries into a concise professional summary:\n"
                + "\n".join(summaries)
            )

        st.success("Summary generated")
        st.markdown(final_summary)

        st.session_state.stats["docs"] += 1
        st.session_state.stats["queries"] += len(chunks) + 1

elif page == "❓ Ask Questions":
    st.markdown("## ❓ Ask Questions from Document")

    pdf = st.file_uploader("Upload PDF", type="pdf")
    question = st.text_input("Enter your question")

    if pdf and question:
        text = extract_text(pdf)[:6000]

        with st.spinner("Thinking..."):
            answer = groq_generate(
                f"Answer ONLY from the document below:\n\n{text}\n\nQuestion:\n{question}"
            )

        st.markdown("### ✅ Answer")
        st.write(answer)

        st.session_state.stats["queries"] += 1

elif page == "🔑 Keyword Extraction":
    st.markdown("## 🔑 Keyword Extraction")

    pdf = st.file_uploader("Upload PDF", type="pdf")

    if pdf:
        text = extract_text(pdf)
        words = pd.Series(text.lower().split()).value_counts().head(15)
        st.dataframe(words)

elif page == "🗂️ User Management":
    st.markdown("## 🗂️ User Management (Admin)")
    st.dataframe(load_users())

