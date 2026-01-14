import streamlit as st
from utils.pdf_utils import extract_text
from utils.ai_utils import summarize
import csv

st.title("📘 Document Summary")

uploaded = st.file_uploader("Upload PDF", type="pdf")

if uploaded:
    text = extract_text(uploaded)
    summary = summarize(text)
    st.markdown(summary)

    with open("data/document_logs.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([uploaded.name, st.session_state.role])
