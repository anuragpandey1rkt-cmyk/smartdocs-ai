import streamlit as st
import re
from utils.pdf_utils import extract_text

st.title("🔑 Keyword Extraction")

uploaded = st.file_uploader("Upload PDF", type="pdf")

if uploaded:
    text = extract_text(uploaded)
    words = re.findall(r'\b[A-Za-z]{5,}\b', text)
    keywords = set(words[:15])
    for k in keywords:
        st.markdown(f"- **{k}**")

