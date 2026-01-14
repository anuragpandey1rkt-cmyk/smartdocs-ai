import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="SmartDoc AI", layout="wide")

USERS_FILE = "data/users.csv"

# =============================
# HELPER FUNCTIONS
# =============================
def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "password", "role"])


def save_user(username, password, role):
    df = load_users()
    new_user = pd.DataFrame([[username, password, role]], columns=df.columns)
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USERS_FILE, index=False)


def authenticate(username, password):
    df = load_users()
    user = df[(df["username"] == username) & (df["password"] == password)]
    if not user.empty:
        return user.iloc[0]["role"]
    return None


# =============================
# SESSION STATE
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

# =============================
# MAIN UI
# =============================
st.title("📄 SmartDoc AI")

menu = st.radio("Choose Option", ["Login", "Sign Up"])

# =============================
# SIGNUP PAGE
# =============================
if menu == "Sign Up":
    st.subheader("📝 Create New Account")

    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")

    if st.button("Register"):
        users_df = load_users()

        if new_user in users_df["username"].values:
            st.error("Username already exists")
        else:
            # First user becomes Admin
            role = "Admin" if users_df.empty else "User"
            save_user(new_user, new_pass, role)
            st.success("Account created successfully!")
            st.info("You can now login")

# =============================
# LOGIN PAGE
# =============================
elif menu == "Login":
    st.subheader("🔑 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        role = authenticate(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.success(f"Logged in as {role}")
            st.rerun()
        else:
            st.error("Invalid username or password")

# =============================
# AFTER LOGIN
# =============================
if st.session_state.logged_in:
    st.sidebar.success(f"Role: {st.session_state.role}")
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())
    st.info("👉 Use the sidebar to navigate application pages")

