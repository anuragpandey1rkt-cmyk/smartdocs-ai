import streamlit as st
import pandas as pd
import os
import hashlib
from PyPDF2 import PdfReader
from groq import Groq
from datetime import datetime
from gtts import gTTS
import io
import sqlalchemy
from sqlalchemy import create_engine, text

# =============================
# APP CONFIG
# =============================
st.set_page_config(
    page_title="SmartDoc AI",
    page_icon="📄",
    layout="wide"
)

# =============================
# STORAGE & SETUP (DATABASE)
# =============================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

if "GROQ_API_KEY" not in st.secrets:
    st.error("🚨 GROQ_API_KEY not found in secrets!")
    st.stop()

groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Database Connection
if "DATABASE_URL" in st.secrets:
    db_url = st.secrets["DATABASE_URL"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
else:
    st.error("🚨 DATABASE_URL missing in secrets!")
    st.stop()

# Create Engine
engine = create_engine(db_url)

# --- THE FIX IS HERE ---
@st.cache_resource
def init_db():
    """
    Creates users AND tickets tables.
    Cached to prevent 'Race Conditions' (multiple threads creating tables at once).
    """
    try:
        # Use engine.begin() to automatically commit transactions
        with engine.begin() as conn:
            # 1. Create Users Table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # 2. Create Tickets Table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id SERIAL PRIMARY KEY,
                    username TEXT,
                    issue_type TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'Open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
    except Exception as e:
        # If tables already exist or minor error, just log it and continue
        print(f"Database Init Note: {e}")

# Call the cached function
init_db()

# =============================
# SMART AI ENGINE
# =============================
def ai(prompt):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert corporate assistant. Answer strictly based on the context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000 
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI Error: {str(e)}"

# =============================
# HELPER FUNCTIONS
# =============================
@st.cache_data
def extract_text(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def save_user(username, password, role):
    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (username, password, role) VALUES (:u, :p, :r)"),
                {"u": username, "p": hash_pw(password), "r": role}
            )
            conn.commit()
        return True
    except sqlalchemy.exc.IntegrityError:
        return False
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def authenticate(username, password):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT role FROM users WHERE username = :u AND password = :p"),
            {"u": username, "p": hash_pw(password)}
        ).fetchone()
    return result[0] if result else None

# NEW: Function to submit tickets
def submit_ticket(username, issue_type, desc):
    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO tickets (username, issue_type, description) VALUES (:u, :t, :d)"),
                {"u": username, "t": issue_type, "d": desc}
            )
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Ticket Error: {e}")
        return False

def get_my_tickets(username):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, issue_type, description, status, created_at FROM tickets WHERE username = :u ORDER BY created_at DESC"),
            {"u": username}
        ).fetchall()
    return pd.DataFrame(result, columns=["Ticket ID", "Type", "Description", "Status", "Date"])

# =============================
# SESSION MANAGEMENT
# =============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
if "current_doc_text" not in st.session_state:
    st.session_state.current_doc_text = None

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.current_doc_text = None
    st.rerun()

# =============================
# AUTH SCREEN
# =============================
if not st.session_state.logged_in:
    st.markdown("## 📄 SmartDoc AI")
    st.info("Log in to access your Enterprise Assistant.")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            role = authenticate(u, p)
            if role:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Invalid credentials.")

    with tab2:
        nu = st.text_input("Pick a Username")
        np = st.text_input("Pick a Password", type="password")
        if st.button("Create Account"):
            # First user is Admin, others are Employees
            try:
                with engine.connect() as conn:
                    count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            except: count = 0
            
            role = "Admin" if count == 0 else "Employee"
            
            if save_user(nu, np, role):
                st.success("Account created! Please log in.")
            else:
                st.error("Username already taken.")
    st.stop()

# =============================
# MAIN APP INTERFACE
# =============================
st.sidebar.title(f"👤 {st.session_state.role}")
st.sidebar.caption(f"User: {st.session_state.username}")
st.sidebar.divider()

st.sidebar.markdown("### 📂 1. Upload Handbook")
uploaded_file = st.sidebar.file_uploader("Choose a PDF", type="pdf")

if uploaded_file:
    if st.session_state.current_doc_text is None or uploaded_file.name != getattr(st.session_state, 'last_file_name', ''):
        with st.spinner("Processing document..."):
            text = extract_text(uploaded_file)
            if text:
                st.session_state.current_doc_text = text
                st.session_state.last_file_name = uploaded_file.name
                st.sidebar.success("Document loaded!")
            else:
                st.sidebar.error("Could not read PDF text.")

# NAVIGATION
# Added "🛠️ Service Desk"
# UPDATE THIS LINE IN YOUR CODE:
page = st.sidebar.radio("Navigate", ["🏠 Home", "📘 Summary", "🔑 Insights", "❓ Chat", "🛠️ Service Desk", "📊 Admin Dashboard"])
st.sidebar.divider()
st.sidebar.button("Logout", on_click=logout)

# =============================
# PAGES
# =============================
if page == "🏠 Home":
    st.title("Welcome to SmartDoc AI 🚀")
    st.write("Your All-in-One Enterprise Onboarding & Knowledge Assistant.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("📘 **Read:** Upload handbooks and get instant summaries.")
    with col2:
        st.success("🛠️ **Act:** Raise tickets for IT, HR, or Admin support.")

elif page == "📘 Summary":
    st.header("Executive Summary")
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        if st.button("Generate Summary"):
            with st.spinner("Analyzing..."):
                doc_preview = st.session_state.current_doc_text[:10000] 
                summary = ai(f"Provide a comprehensive summary of this document:\n\n{doc_preview}")
                st.markdown(summary)
                
                # Audio Feature
                try:
                    tts = gTTS(text=summary, lang='en')
                    audio_bytes = io.BytesIO()
                    tts.write_to_fp(audio_bytes)
                    st.audio(audio_bytes, format='audio/mp3')
                except:
                    st.caption("Audio requires 'gTTS'.")

elif page == "🔑 Insights":
    st.header("Key Insights")
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        if st.button("Extract Insights"):
            with st.spinner("Extracting..."):
                doc_preview = st.session_state.current_doc_text[:10000]
                insights = ai(f"Extract the top 5 strategic insights and 5 key facts from this text:\n\n{doc_preview}")
                st.markdown(insights)

elif page == "❓ Chat":
    st.header("Chat with the Handbook")
    if not st.session_state.current_doc_text:
        st.warning("Please upload a document first.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Ask about policies, wifi, insurance..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.spinner("Thinking..."):
                context = st.session_state.current_doc_text[:10000] 
                final_prompt = f"""
                Use the document context to answer the question.
                DOCUMENT CONTEXT: {context}
                USER QUESTION: {prompt}
                """
                response = ai(final_prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.chat_message("assistant").write(response)

elif page == "📊 Admin Dashboard":
    st.header("📊 Executive Dashboard")
    
    # SECURITY CHECK: Only Admins can see this page
    if st.session_state.role != "Admin":
        st.error("⛔ ACCESS DENIED. You do not have Admin permissions.")
        st.stop()

    st.write("Overview of system performance and ticket metrics.")
    
    # 1. Fetch Data from Database
    with engine.connect() as conn:
        tickets_df = pd.read_sql("SELECT * FROM tickets", conn)
        users_df = pd.read_sql("SELECT * FROM users", conn)
    
    # 2. Top Level Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Employees", len(users_df))
    with col2:
        st.metric("Total Tickets Raised", len(tickets_df))
    with col3:
        # Count 'Open' tickets if you had a status column, otherwise just count total
        open_tickets = len(tickets_df[tickets_df['status'] == 'Open']) if 'status' in tickets_df.columns else 0
        st.metric("Pending Issues", open_tickets)
    
    st.divider()

    # 3. Visualizations (The "Wow" Factor)
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🎫 Issues by Category")
        if not tickets_df.empty:
            # Bar chart of Issue Types
            chart_data = tickets_df['issue_type'].value_counts()
            st.bar_chart(chart_data)
        else:
            st.info("No data yet.")
            
    with c2:
        st.subheader("📅 Activity Timeline")
        if not tickets_df.empty:
            # Line chart of tickets over time
            tickets_df['created_at'] = pd.to_datetime(tickets_df['created_at'])
            time_data = tickets_df.set_index('created_at')['id'].resample('D').count()
            st.line_chart(time_data)
        else:
            st.info("No data yet.")

    st.divider()

    # 4. Master Data View
    st.subheader("🗂️ All Database Records")
    tab_users, tab_tickets = st.tabs(["Employees", "Support Tickets"])
    
    with tab_users:
        st.dataframe(users_df[['username', 'role', 'created_at']], use_container_width=True)
    
    with tab_tickets:
        st.dataframe(tickets_df, use_container_width=True)
        
elif page == "🛠️ Service Desk":
    st.header("🛠️ Employee Service Desk")
    st.write("Need help? Raise a ticket instantly.")
    
    with st.form("ticket_form"):
        issue_type = st.selectbox("Issue Type", ["IT Support (Laptop/Wifi)", "HR (Insurance/Leave)", "Facilities (Badge/Desk)", "Other"])
        desc = st.text_area("Description", placeholder="e.g., I lost my ID card")
        submitted = st.form_submit_button("Submit Ticket")
        
        if submitted:
            if submit_ticket(st.session_state.username, issue_type, desc):
                st.success("✅ Ticket created successfully! The team will contact you.")
            else:
                st.error("Failed to submit ticket.")
    
    st.divider()
    st.subheader("My Recent Tickets")
    tickets = get_my_tickets(st.session_state.username)
    if not tickets.empty:
        st.dataframe(tickets, use_container_width=True)
    else:
        st.info("No tickets raised yet.")
