import streamlit as st
import pandas as pd

st.title("📂 Document History")

df = pd.read_csv("data/document_logs.csv")

if st.session_state.role == "Admin":
    st.dataframe(df)
else:
    st.warning("Only Admin can view document history")
