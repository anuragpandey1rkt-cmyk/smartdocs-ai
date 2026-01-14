import streamlit as st
import pandas as pd
import os
import hashlib

st.set_page_config(page_title="SmartDoc AI", layout="wide")

USERS_FILE = "data/users.csv"

# =============================
# 🔐 SECURITY HELPERS
# =============================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# =============================
# DATA HELPERS
# =============================
def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "password", "role"])


def save_user(username, password, role):
    df = load_users()
    hashed_pw = hash_password(password)
    df.loc[len(df)] = [username, hashed_pw, role]
    df.to_csv(USERS_FILE, index=False)


def authenticate(username, password):
    df = load_users()
    hashed_pw = hash_password(password)

    match = df[
        (df["username"] == username) &
        (df["password"] == hashed_pw)
    ]

    if not match.empty:
        return match.iloc[0]["role"]
    return None


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
# AUTH UI
# =============================
if not st.session_state.logged_in:

    st.title("📄 SmartDoc AI")

    option = st.radio("Choose Option", ["Login", "Sign Up"])

    # -------- SIGN UP --------
    if option == "Sign Up":
        st.subheader("📝 Create Account")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            users = load_users()

            if username in users["username"].values:
                st.error("Username already exists")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                role = "Admin" if users.empty else "User"
                save_user(username, password, role)
                st.success("Account created successfully")
                st.info("Please login now")

    # -------- LOGIN --------
    else:
        st.subheader("🔑 Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            role = authenticate(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid username or password")

# =============================
# MAIN APP
# =============================
else:
    # ---------- SIDEBAR ----------
    st.sidebar.success(f"Role: {st.session_state.role}")
    st.sidebar.markdown("### 📂 Navigation")

    if st.sidebar.button("📊 Dashboard"):
        st.switch_page("pages/1_Dashboard.py")

    if st.sidebar.button("📘 Document Summary"):
        st.switch_page("pages/2_Document_Summary.py")

    if st.sidebar.button("❓ Ask Questions"):
        st.switch_page("pages/3_Ask_Questions.py")

    if st.sidebar.button("🔑 Keyword Extraction"):
        st.switch_page("pages/4_Keyword_Extraction.py")

    if st.session_state.role == "Admin":
        if st.sidebar.button("🗂️ Document History"):
            st.switch_page("pages/5_Document_History.py")

    st.sidebar.divider()
    st.sidebar.button("🚪 Logout", on_click=logout)

    # ---------- MAIN ----------
    st.title("📂 Welcome to SmartDoc AI")
    st.info("👉 Select a feature from the sidebar")



