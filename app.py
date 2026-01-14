import streamlit as st
import pandas as pd
import os
import hashlib
from PyPDF2 import PdfReader
from groq import Groq

# =============================
# CONFIG
# =============================
st.set_page_config(
    page_title="SmartDoc AI",
    page_icon="📄",
    layout="wide"
)

USERS_FILE = "data/users.csv"


groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def groq_generate(prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a professional document analysis assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content


def chunk_text(text, max_chars=2500):
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]



# =============================
# UTILITIES
# =============================
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "password", "role"])

def save_user(username, password, role):
    df = load_users()
    df.loc[len(df)] = [username, hash_password(password), role]
    df.to_csv(USERS_FILE, index=False)

def authenticate(username, password):
    df = load_users()
    pw = hash_password(password)
    user = df[(df.username == username) & (df.password == pw)]
    if not user.empty:
        return user.iloc[0]["role"]
    return None

def extract_text(pdf):
    reader = PdfReader(pdf)
    return "".join(page.extract_text() or "" for page in reader.pages)

# =============================
# SESSION STATE
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# =============================
# AUTH
# =============================
if not st.session_state.logged_in:
    st.markdown("## 📄 SmartDoc AI")
    st.markdown("### Enterprise Document Intelligence Platform")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            role = authenticate(u, p)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        u = st.text_input("New Username")
        p = st.text_input("New Password", type="password")
        if st.button("Register"):
            users = load_users()
            if u in users.username.values:
                st.error("User already exists")
            else:
                role = "Admin" if users.empty else "User"
                save_user(u, p, role)
                st.success("Account created. Please login.")

    st.stop()

# =============================
# SIDEBAR NAVIGATION (ALWAYS VISIBLE)
# =============================
st.sidebar.success(f"Role: {st.session_state.role}")
page = st.sidebar.radio(
    "📂 Navigation",
    [
        "🏠 Home",
        "📊 Dashboard",
        "📘 Document Summary",
        "❓ Ask Questions",
        "🔑 Keyword Extraction"
    ] + (["🗂️ Document History"] if st.session_state.role == "Admin" else [])
)
st.sidebar.button("🚪 Logout", on_click=logout)

# =============================
# PAGES
# =============================

if page == "🏠 Home":
    st.markdown("## 👋 Welcome to SmartDoc AI")
    st.info("AI-powered platform for document understanding, summarization and insights.")
    col1, col2, col3 = st.columns(3)
    col1.metric("AI Engine", "Gemini Pro")
    col2.metric("Security", "Hashed Passwords")
    col3.metric("Deployment", "Cloud Ready")

elif page == "📊 Dashboard":
    st.markdown("## 📊 Dashboard")
    st.metric("Documents Processed", 12)
    st.metric("AI Queries", 34)

elif page == "📘 Document Summary":
    st.markdown("## 📘 Document Summary")

    pdf = st.file_uploader("Upload PDF", type="pdf")

    if pdf:
        text = extract_text(pdf)

        if len(text.strip()) < 100:
            st.error("PDF has no readable text.")
            st.stop()

        def chunk_text(text, size=3000):
            return [text[i:i+size] for i in range(0, len(text), size)]

        chunks = chunk_text(text)[:4]  # safety limit
        summaries = []

        with st.spinner("Summarizing document with AI..."):
            try:
                for chunk in chunks:
                    summary = groq_generate(
                        f"Summarize the following document section in bullet points:\n{chunk}"
                    )
                    summaries.append(summary)

                final_summary = groq_generate(
                    "Combine the following summaries into a concise professional summary:\n"
                    + "\n".join(summaries)
                )

                st.success("Summary generated successfully")
                st.markdown(final_summary)

            except Exception as e:
                st.error("AI service failed. Please try again.")

elif page == "❓ Ask Questions":
    st.markdown("## ❓ Ask Questions")
    pdf = st.file_uploader("Upload PDF", type="pdf")
    q = st.text_input("Enter your question")
    if pdf and q:
        text = extract_text(pdf)
        ans = model.generate_content(
            f"Answer using this document only:\n{text}\nQuestion:{q}"
        ).text
        st.write(ans)

elif page == "🔑 Keyword Extraction":
    st.markdown("## 🔑 Keyword Extraction")
    pdf = st.file_uploader("Upload PDF", type="pdf")
    if pdf:
        text = extract_text(pdf)
        words = pd.Series(text.split()).value_counts().head(15)
        st.dataframe(words)

elif page == "🗂️ Document History":
    st.markdown("## 🗂️ Document History")
    st.info("Admin-only feature (future database integration)")



