import streamlit as st
from groq import Groq
import google.generativeai as genai
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TopperGPT Pro",
    page_icon="🎓",
    layout="wide"
)

# --- 2. SECURE CONFIGURATION ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    RZP_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] #
    
    # AI Setup
    genai.configure(api_key=GEMINI_API_KEY)
    client_groq = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("Secrets missing! Please check GROQ_API_KEY, RAZORPAY_KEY_ID, and GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = None

# --- 4. MAIN INTERFACE ---
st.title("🎓 TopperGPT: Your AI Study Studio")

# Saare Tabs wapas add kar diye hain
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Chat with PDF", 
    "🎥 YouTube Analyzer", 
    "🎧 AI Study Podcast", 
    "🧠 Mind Maps & Quizzes",
    "⚖️ Legal & Policies" # Razorpay fix
])

# --- TAB 1: PDF CHAT ---
with tab1:
    st.subheader("📚 Analyze your Notes")
    pdf_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_chat_uploader")
    if pdf_file:
        st.success(f"File '{pdf_file.name}' detected! Ready to chat.")
    st.info("Chat logic will be activated here tomorrow.")

# --- TAB 2: YOUTUBE ANALYZER ---
with tab2:
    st.subheader("🎥 YouTube Video to Notes")
    yt_url = st.text_input("Enter YouTube Video URL:", placeholder="https://youtube.com/watch?v=...")
    if st.button("Extract Knowledge"):
        st.warning("YouTube transcript feature is being configured.")

# --- TAB 3: AI STUDY PODCAST ---
with tab3:
    st.subheader("🎧 Convert Notes to Audio")
    st.write("Generate a professional AI podcast from your study material.")
    if st.button("Generate Podcast"):
        st.info("Audio generation (Gemini + gTTS) setup in progress.")

# --- TAB 4: MIND MAPS & QUIZZES ---
with tab4:
    st.subheader("🧠 Interactive Learning")
    col_a, col_b = st.columns(2)
    with col_a:
        st.button("Create Mind Map")
    with col_b:
        st.button("Generate Practice Quiz")

# --- TAB 5: LEGAL & POLICIES (Razorpay Verification) ---
with tab5:
    st.header("Legal Information & Policies")
    st.info("Required for Razorpay Payment Gateway Verification.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Privacy Policy")
        st.write("We do not store your PDFs permanently. Data is used only for real-time AI analysis.")
        st.subheader("2. Terms and Conditions")
        st.write("Service is for educational purposes. Users must not upload malicious content.")
    with col2:
        st.subheader("3. Refund & Cancellation")
        st.write("Subscription fees are non-refundable once the PRO features are accessed.")
        st.subheader("4. Contact Us")
        st.write("Email: support@toppergpt.com | Location: Neral, Maharashtra, India.")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 👤 Account Status")
    st.success("FREE Tier")
    st.markdown("---")
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()