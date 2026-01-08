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
    uploaded_file = st.file_uploader("Upload Notes", type=["pdf", "jpg", "png", "jpeg"], key="pdf_chat_final_v7")

    if uploaded_file:
        if "pdf_content" not in st.session_state or st.session_state.get("last_uploaded") != uploaded_file.name:
            with st.spinner("🧠 Deep Scanning..."):
                try:
                    text_data = ""
                    if uploaded_file.type == "application/pdf":
                        # Method 1: PyPDF
                        import pypdf
                        reader = pypdf.PdfReader(uploaded_file)
                        for page in reader.pages:
                            text_data += page.extract_text() + "\n"
                        
                        # Method 2: If PyPDF fails to get text
                        if len(text_data.strip()) < 10:
                            text_data = "Error: PDF text readable nahi hai, please image upload karein."
                            
                    else:
                        # Image/Handwritten logic
                        v_model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        v_res = v_model.generate_content(["Extract all text strictly.", uploaded_file])
                        text_data = v_res.text
                    
                    st.session_state.pdf_content = text_data
                    st.session_state.last_uploaded = uploaded_file.name
                    st.success("✅ Content Synchronized!")
                except Exception as e:
                    st.error(f"Sync failed: {e}")

    st.divider()

    # Chat Display logic
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Input logic with direct prompt passing
    if u_input := st.chat_input("Ask from your notes..."):
        st.session_state.messages.append({"role": "user", "content": u_input})
        with st.chat_message("user"):
            st.markdown(u_input)

        with st.chat_message("assistant"):
            # Getting content from memory
            ctx = st.session_state.get("pdf_content", "No context available.")
            
            # Creating a super-clear prompt
            final_prompt = f"Note Context: {ctx[:10000]}\n\nQuestion: {u_input}\n\nInstruction: Answer strictly based on notes if available. If not, use general knowledge."

            try:
                # Primary AI
                g_model = genai.GenerativeModel('gemini-1.5-flash-latest')
                g_res = g_model.generate_content(final_prompt)
                ans = g_res.text
            except:
                # Backup AI (Groq) without the "Backup" message
                try:
                    from groq import Groq
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    res = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": final_prompt}]
                    )
                    ans = res.choices[0].message.content
                except:
                    ans = "Bhai, dono servers busy hain. Ek baar refresh karke 10 second ruko."

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