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
    st.subheader("📚 Analyze your Notes (PDF & Handwritten)")
    uploaded_file = st.file_uploader("Upload Notes", type=["pdf", "jpg", "png", "jpeg"], key="pdf_chat_final_v9")

    if uploaded_file:
        if "pdf_content" not in st.session_state or st.session_state.get("last_uploaded") != uploaded_file.name:
            with st.spinner("🧠 AI is reading your 12MB file... please wait."):
                try:
                    # GEMINI VISION/PDF DIRECT SCAN (Strongest Method)
                    model_v = genai.GenerativeModel('gemini-1.5-flash-latest')
                    
                    # File ko bytes mein convert karke direct Gemini ko dena
                    file_bytes = uploaded_file.read()
                    
                    # Agar PDF hai toh usse analyze karwana
                    if uploaded_file.type == "application/pdf":
                        # Gemini can take PDF bytes directly in some regions, 
                        # but for stability, we ask it to describe the content
                        response = model_v.generate_content([
                            "Analyze this document and extract all study content, questions, and important topics into text.",
                            {"mime_type": "application/pdf", "data": file_bytes}
                        ])
                    else:
                        response = model_v.generate_content([
                            "Extract all text from this image.",
                            {"mime_type": uploaded_file.type, "data": file_bytes}
                        ])
                    
                    st.session_state.pdf_content = response.text
                    st.session_state.last_uploaded = uploaded_file.name
                    st.success("✅ PDF Content Captured!")
                except Exception as e:
                    st.error("Gemini busy hai, hum normal PDF reader try kar rahe hain...")
                    # Fallback to pypdf if API fails
                    import pypdf, io
                    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                    st.session_state.pdf_content = "".join([p.extract_text() for p in reader.pages])

    st.divider()

    # Chat logic (Same as before but with STRONGER prompt)
    if prompt := st.chat_input("Ask from your notes..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            ctx = st.session_state.get("pdf_content", "")
            # Direct Injection: AI cannot deny this data
            final_p = f"IGNORE PREVIOUS KNOWLEDGE. USE ONLY THIS TEXT TO ANSWER:\n\n{ctx[:20000]}\n\nQUESTION: {prompt}"
            
            try:
                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                res = model.generate_content(final_p)
                ans = res.text
            except:
                from groq import Groq
                client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": final_p}]
                )
                ans = res.choices[0].message.content
            
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
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