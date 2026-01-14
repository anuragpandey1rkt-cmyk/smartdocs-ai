import google.generativeai as genai
import streamlit as st

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-pro")

def summarize(text):
    prompt = f"Summarize this document in bullet points:\n{text}"
    return model.generate_content(prompt).text

def answer_question(text, question):
    prompt = f"Answer based only on this document:\n{text}\nQuestion:{question}"
    return model.generate_content(prompt).text
