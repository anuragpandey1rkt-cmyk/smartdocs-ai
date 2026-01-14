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
# STORAGE
# =============================
DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.csv"
os.makedirs(DATA_DIR, exist_ok=True)

# =============================
# GROQ CLIENT
# =============================
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def ai(prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You extract insights from documents clearly and professionally."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# =============================
# HELPERS
# =============================
def extract_text(pdf):
    reader = PdfReader(pdf)
    return "".join(page.extract_text() or "" for page in reader.pages)

def chunk_text(text, size=2500):
    return [text[i:i+size] for i in range(0, len(text), size)]

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "password", "role", "created_at"])

def save_user(username, password, role):
    df = load_users()
    df.loc[len(df)] = [username, hash_pw(password), role, datetime.now()]
    df.to_csv(USERS_FILE, index=False)

def authenticate(username, password):
    df = load_users()
    user = df[(df.username == username) & (df.password == hash_pw(password))]
    return user.iloc[0]["role"] if not user.empty else None

# =============================
# SESSION
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
# AUTH UI
# =============================
if not st.session_state.logged_in:
    st.markdown("## 📄 SmartDoc AI")
    st.markdown("### Turn documents into knowledge, instantly.")

    login, signup = st.tabs(["🔑 Login", "📝 Sign Up"])

    with login:
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

    with signup:
        u = st.text_input("New Username")
        p = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            users = load_users()
            if u in users.username.values:
                st.error("User already exists")
            else:
                role = "Admin" if users.empty else "User"
                save_user(u, p, role)
                st.success("Account created. Please login.")

    st.stop()

# =============================
# SIDEBAR
# =============================
st.sidebar.success(f"Role: {st.session_state.role}")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Home", "📘 Document Summary", "🔑 Key Insights", "❓ Ask Questions"]
)

st.sidebar.button("🚪 Logout", on_click=logout)

# =============================
# HOME
# =============================
if page == "🏠 Home":
    st.markdown("## 👋 Welcome to SmartDoc AI")

    st.write(
        """
        SmartDoc AI helps **students, professionals, and enterprises**
        understand large PDFs in minutes instead of hours.

        **What you can do:**
        - 📘 Get clear document summaries  
        - 🔑 Extract key insights & important points  
        - ❓ Ask questions directly from your documents  
        """
    )

    c1, c2, c3 = st.columns(3)
    c1.info("📘 Summarize complex documents")
    c2.info("🔑 Extract actionable insights")
    c3.info("❓ Ask questions & get precise answers")

# =============================
# DOCUMENT SUMMARY
# =============================
elif page == "📘 Document Summary":
    st.markdown("## 📘 Document Summary")

    pdf = st.file_uploader("Upload PDF", type="pdf")

    if pdf:
        text = extract_text(pdf)
        chunks = chunk_text(text)[:4]
        summaries = []

        with st.spinner("Generating summary..."):
            for c in chunks:
                summaries.append(ai(f"Summarize this section clearly:\n{c}"))

            final = ai(
                "Combine the following into a professional, easy-to-read summary:\n"
                + "\n".join(summaries)
            )

        st.success("Summary ready")
        st.markdown(final)

# =============================
# KEY INSIGHTS (REAL KEYWORDS)
# =============================
elif page == "🔑 Key Insights":
    st.markdown("## 🔑 Key Insights & Highlights")

    pdf = st.file_uploader("Upload PDF", type="pdf")

    if pdf:
        text = extract_text(pdf)[:6000]

        with st.spinner("Extracting key insights..."):
            insights = ai(
                f"""
                Extract the most important points, concepts, and takeaways
                from the following document. Present them as bullet points.

                DOCUMENT:
                {text}
                """
            )

        st.success("Key insights extracted")
        st.markdown(insights)

# =============================
# ASK QUESTIONS
# =============================
elif page == "❓ Ask Questions":
    st.markdown("## ❓ Ask Questions from Document")

    pdf = st.file_uploader("Upload PDF", type="pdf")
    question = st.text_input("Your question")

    if pdf and question:
        text = extract_text(pdf)[:6000]

        with st.spinner("Finding answer..."):
            answer = ai(
                f"""
                Answer the question using ONLY the document below.

                DOCUMENT:
                {text}

                QUESTION:
                {question}
                """
            )

        st.markdown("### ✅ Answer")
        st.write(answer)
