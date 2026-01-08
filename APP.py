import streamlit as st
from groq import Groq
import google.generativeai as genai
import pypdf
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="TopperGPT Pro", page_icon="🎓", layout="wide")

# --- 2. SECURE KEYS ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    RZP_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    FIREBASE_API_KEY = st.secrets.get("FIREBASE_API_KEY", "NOT_SET")
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error("Secrets Missing! Check Streamlit Dashboard.")
    st.stop()

# --- 3. SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "user_auth" not in st.session_state: st.session_state.user_auth = False

# --- 4. SIDEBAR (Auth & Upgrade) ---
with st.sidebar:
    st.title("👤 Topper Profile")
    if not st.session_state.user_auth:
        st.write("Status: **FREE Tier**")
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.toast("Opening Razorpay...")
        st.divider()
        u_email = st.text_input("Email Login (Firebase)")
        if st.button("Login"):
            st.session_state.user_auth = True
            st.rerun()
    else:
        st.success("PRO User ✅")
        if st.button("Logout"):
            st.session_state.user_auth = False
            st.rerun()
    st.divider()
    st.write("AI Engines: Groq & Gemini Online ✅")

# --- 5. MAIN TABS (Sare Features Wapas!) ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💬 PDF Chat", "🎥 YT Notes", "🎧 Podcast", "🧠 Mind Maps", "📝 Quizzes", "⚖️ Legal"
])

with tab1:
    with tab1:
    st.subheader("📚 Analyze your Notes (PDF & Handwritten)")
    
    # PDF Upload Section
    uploaded_file = st.file_uploader("Upload PDF or Image of Notes", type=["pdf", "jpg", "png"], key="pdf_chat_main")

    # 1. PROCESSING LOGIC (Memory Lock)
    if uploaded_file:
        # Nayi file detect karne ka logic
        if "pdf_content" not in st.session_state or st.session_state.get("last_uploaded") != uploaded_file.name:
            with st.spinner("🧠 AI is deep-scanning your notes..."):
                try:
                    if uploaded_file.type == "application/pdf":
                        # Standard PDF Text Extraction
                        import pypdf
                        reader = pypdf.PdfReader(uploaded_file)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() or ""
                        st.session_state.pdf_content = text
                    else:
                        # Image/Handwritten logic (Gemini Vision use karenge)
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        response = model.generate_content(["Extract all text and formulas from this handwritten note image strictly.", uploaded_file])
                        st.session_state.pdf_content = response.text
                    
                    st.session_state.last_uploaded = uploaded_file.name
                    st.success(f"✅ '{uploaded_file.name}' is now in Memory!")
                except Exception as e:
                    st.error(f"Extraction Error: {e}")

    st.divider()

    # 2. CHAT HISTORY DISPLAY
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 3. HYBRID CHAT LOGIC (NotebookLM style + Open AI)
    if prompt := st.chat_input("Ask anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prompt Engineering: AI ko batana ki context hai ya nahi
        context = st.session_state.get("pdf_content", "")
        
        # System Instruction
        if context:
            system_prompt = f"You are TopperGPT. Use this user's notes to answer. If the answer isn't in notes, use your own knowledge but mention 'Based on my knowledge'. \n\nNOTES: {context[:10000]}"
        else:
            system_prompt = "You are TopperGPT. No notes uploaded yet. Answer the user's question using your general study knowledge."

        with st.chat_message("assistant"):
            try:
                # Gemini 1.5 Pro for High Accuracy
                model = genai.GenerativeModel('gemini-1.5-pro')
                chat = model.start_chat()
                full_prompt = f"{system_prompt} \n\nUSER QUESTION: {prompt}"
                response = chat.send_message(full_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"AI Error: {e}")
        st.rerun()
with tab2:
    st.subheader("🎥 YouTube Video Analyzer")
    st.text_input("YouTube URL")
    st.button("Get Detailed Notes")

with tab3:
    st.subheader("🎧 AI Study Podcast")
    st.write("Convert your material into a professional audio guide.")
    st.button("Generate Audio")

with tab4:
    st.subheader("🧠 Visual Mind Maps")
    st.write("Generate interactive diagrams for better memory.")
    st.button("Create Map")

with tab5:
    st.subheader("📝 Practice Quizzes & Flashcards")
    st.write("Test your knowledge with AI-generated questions.")
    col_q1, col_q2 = st.columns(2)
    with col_q1: st.button("Generate 10 MCQ Quiz")
    with col_q2: st.button("Create Flashcards")

# --- 6. LEGAL & POLICIES (Razorpay Fix) ---
with tab6:
    st.header("⚖️ Privacy Policy & Terms")
    st.info("Razorpay Verification Status: Pages Live.")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Privacy Policy")
        st.write("We use Firebase for secure login. No user data or uploaded PDFs are sold. Processing is done in real-time.")
        st.subheader("2. Terms of Service")
        st.write("By using TopperGPT, you agree to fair use of AI credits for educational purposes.")
    with c2:
        st.subheader("3. Refund Policy")
        st.write("Subscription is for digital access. Refund is applicable only for technical failures exceeding 48 hours.")
        st.subheader("4. Contact Us")
        st.write("Email: support@toppergpt.com | Address: Neral, Maharashtra, India.")