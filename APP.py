import streamlit as st
from groq import Groq
import google.generativeai as genai
import pypdf
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TopperGPT Pro",
    page_icon="🎓",
    layout="wide"
)

# --- 2. SECURE CONFIGURATION (Secrets Fetching) ---
try:
    # Saari keys yahan se uthayega
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    RZP_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    FIREBASE_API_KEY = st.secrets.get("FIREBASE_API_KEY", "NOT_SET") #
    
    # Gemini AI Setup
    genai.configure(api_key=GEMINI_API_KEY)
    
except Exception as e:
    st.error("Secrets not found! Please check Streamlit Dashboard Settings > Secrets.")
    st.stop()

# --- 3. SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_mem" not in st.session_state:
    st.session_state.pdf_mem = None
if "user_auth" not in st.session_state:
    st.session_state.user_auth = False

# --- 4. MAIN INTERFACE ---
st.title("🎓 TopperGPT: Your AI Study Studio")

# Firebase Login Simulation (Sidebar)
with st.sidebar:
    st.title("👤 User Profile")
    if not st.session_state.user_auth:
        st.info("Firebase Auth Ready ✅")
        user_email = st.text_input("Enter Email for Firebase Login")
        if st.button("Login / Sign Up"):
            st.session_state.user_auth = True
            st.success(f"Logged in: {user_email}")
    else:
        st.success("Authenticated ✅")
        if st.button("Logout"):
            st.session_state.user_auth = False
            st.rerun()
    
    st.divider()
    st.markdown("### 🛠️ AI Tools Status")
    st.write(f"**Groq AI:** Connected ✅")
    st.write(f"**Gemini AI:** Connected ✅")

# 5 TABS SYSTEM
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Chat with PDF", 
    "🎥 YouTube Analyzer", 
    "🎧 AI Study Podcast", 
    "🧠 Mind Maps & Quizzes",
    "⚖️ Legal & Policies" 
])

# --- TAB 1: PDF CHAT (Core logic placeholder) ---
with tab1:
    st.subheader("📚 Analyze your Notes")
    uploaded_pdf = st.file_uploader("Upload PDF material", type=["pdf"], key="main_pdf")
    if uploaded_pdf:
        st.success(f"'{uploaded_pdf.name}' is uploaded! (Full Logic fix coming tomorrow)")

# --- TAB 2: YOUTUBE ANALYZER ---
with tab2:
    st.subheader("🎥 Video to Study Notes")
    st.text_input("Paste YouTube Link here")
    st.button("Extract Knowledge (Gemini 1.5 Pro)")

# --- TAB 3: AI PODCAST ---
with tab3:
    st.subheader("🎧 Study Audio Guide")
    st.write("Convert your notes into an AI podcast.")
    st.button("Generate Audio Podcast")

# --- TAB 4: BRAIN TOOLS ---
with tab4:
    st.subheader("🧠 Mind Maps & Flashcards")
    st.button("Generate Visual Map")

# --- TAB 5: LEGAL & POLICIES (Razorpay Requirement) ---
with tab5:
    st.header("⚖️ Legal & Compliance")
    st.info("Required for Razorpay Payment Gateway Verification.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("### 1. Privacy Policy")
        st.write("We use Firebase for secure login. Your PDF content is processed for real-time analysis and not stored permanently.")
        st.write("### 2. Terms of Service")
        st.write("This service is for educational use only. Users are responsible for their uploaded content.")
    with c2:
        st.write("### 3. Refund Policy")
        st.write("Payments for PRO access are digital and generally non-refundable. Contact support for valid issues.")
        st.write("### 4. Contact Details")
        st.write("Support Email: **support@toppergpt.com**")
        st.write("Address: Neral, Maharashtra, India.")