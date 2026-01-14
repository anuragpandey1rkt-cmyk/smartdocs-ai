import streamlit as st
from utils.pdf_utils import extract_text
from utils.ai_utils import answer_question

st.title("❓ Ask Questions")

uploaded = st.file_uploader("Upload PDF", type="pdf")
question = st.text_input("Ask a question")

if uploaded and question:
    text = extract_text(uploaded)
    answer = answer_question(text, question)
    st.write(answer)
