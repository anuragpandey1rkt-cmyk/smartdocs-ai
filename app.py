import streamlit as st

st.set_page_config(page_title="SmartDoc AI", layout="wide")

# Hardcoded users (acceptable for internship demo)
USERS = {
    "admin": {"password": "admin123", "role": "Admin"},
    "user": {"password": "user123", "role": "User"}
}

st.title("📄 SmartDoc AI – Secure Login")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = USERS[username]["role"]
            st.success(f"Logged in as {st.session_state.role}")
            st.rerun()
        else:
            st.error("Invalid credentials")

else:
    st.sidebar.success(f"Role: {st.session_state.role}")
    st.sidebar.info("Use sidebar to navigate pages")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

