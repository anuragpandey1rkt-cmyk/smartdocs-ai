import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai
import pandas as pd
import re
import time

# ==============================
# CONFIGURATION
# ==============================
st.set_page_config(
    page_title="SmartDoc AI",
    page_icon="📄",
    layout="wide"
)

# ==============================
# API KEY (USE YOUR OWN)
# ==============================
genai.configure(api_key="YOUR_GEMINI_API_KEY")

model = genai.GenerativeModel("gemini-pro")

# ==============================
# CUSTOM UI STYLING
# ==============================
st.markdown("""
<style>
.metric-card {
    background-color: #f9fafb;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.05);
}
.title-text {
    font-size: 40px;
    font-weight: 700;
}
.subtitle-text {
    font-size: 18px;
    color: gray;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# HELPER FUNCTIONS
# ==============================
def extract_text_from_pdf(pdf):
    text = ""
    reader = PdfReader(pdf)
    for page in reader.pages:
        text += page.extract_text()
    return text


def ai_answer(context, question):
    prompt = f"""
    You are an intelligent document assistant.
    Answer strictly based on the document below.

    DOCUMENT:
    {context}

    QUESTION:
    {question}
    """
    response = model.generate_content(prompt)
    return response.text


def ai_summary(context):
    prompt = f"""
    Summarize the following document clearly in bullet points:

    {context}
    """
    response = model.generate_content(prompt)
    return response.text


def extract_keywords(text):
    words = re.findall(r'\b[A-Za-z]{5,}\b', text)
    keywords = pd.Series(words).value_counts().head(10)
    return keywords

# ==============================
# HEADER
# ==============================
st.markdown('<div class="title-text">📄 SmartDoc AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">AI-powered Document Understanding & Knowledge Extraction</div>', unsafe_allow_html=True)
st.divider()

# ==============================
# SIDEBAR
# ==============================
st.sidebar.header("📂 Upload Document")
uploaded_file = st.sidebar.file_uploader("Upload PDF", type=["pdf"])

feature = st.sidebar.radio(
    "Choose Feature",
    ["📘 Document Summary", "❓ Ask Questions", "🔑 Keyword Extraction"]
)

# ==============================
# MAIN LOGIC
# ==============================
if uploaded_file:
    with st.spinner("Reading document..."):
        document_text = extract_text_from_pdf(uploaded_file)
        time.sleep(1)

    st.success("Document processed successfully!")

    # ==============================
    # SUMMARY FEATURE
    # ==============================
    if feature == "📘 Document Summary":
        st.subheader("📘 AI Generated Summary")
        summary = ai_summary(document_text)
        st.markdown(summary)

    # ==============================
    # QUESTION ANSWERING
    # ==============================
    elif feature == "❓ Ask Questions":
        st.subheader("❓ Ask a Question from Document")
        user_question = st.text_input("Enter your question")

        if st.button("Get Answer"):
            with st.spinner("Thinking..."):
                answer = ai_answer(document_text, user_question)
            st.markdown("### ✅ Answer")
            st.write(answer)

    # ==============================
    # KEYWORD EXTRACTION
    # ==============================
    elif feature == "🔑 Keyword Extraction":
        st.subheader("🔑 Important Keywords")
        keywords = extract_keywords(document_text)

        for word, count in keywords.items():
            st.markdown(f"**{word}** — {count} times")

else:
    st.info("👈 Upload a PDF document to get started")

# ==============================
# FOOTER
# ==============================
st.divider()
st.caption("SmartDoc AI | Internship Project | Cloud & AI Ready")
