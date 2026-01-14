import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="SmartDoc AI", layout="wide")

USERS_FILE = "data/users.csv"

# =============================
# HELPERS
# =============================
def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "password", "role"])


def save_user(username, password, role):
    df = load_users()
    df.loc[len(df)] = [username, password, role]
    df.to_csv(USERS_FILE, index=False)


def authenticate(username, password):
    df = load_users()
    match = df[(df.username == username) & (df.password == password)]
    if not match.empty:
        return match.iloc[0]["role"]
    return None


# =============================
# SESSION STATE INIT
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None


# =============================
# LOGOUT HANDLER
# =============================
def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()


# =============================
# 🔐 AUTH PAGES (ONLY IF NOT LOGGED IN)
# =============================
if not st.session_state.logged_in:

    st.title("📄 SmartDoc AI")

    choice = st.radio("Choose Option", ["Login", "Sign Up"])

    # -------- SIGN UP --------
    if choice == "Sign Up":
        st.subheader("📝 Create Account")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            users = load_users()

            if username in users["username"].values:
                st.error("Username already exists")
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
# ✅ MAIN APP (ONLY IF LOGGED IN)
# =============================
else:
    st.sidebar.success(f"Role: {st.session_state.role}")
    st.sidebar.button("Logout", on_click=logout)

    st.title("📂 Welcome to SmartDoc AI")
    st.info("👉 Use the sidebar to navigate application pages")

