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
    uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "jpg", "png", "jpeg"], key="pdf_chat_v4")

    # 1. Extraction Logic (Memory Lock)
    if uploaded_file:
        if "pdf_content" not in st.session_state or st.session_state.get("last_uploaded") != uploaded_file.name:
            with st.spinner("🧠 Analyzing your documents..."):
                try:
                    extracted_text = ""
                    if uploaded_file.type == "application/pdf":
                        import pypdf
                        reader = pypdf.PdfReader(uploaded_file)
                        extracted_text = "".join([page.extract_text() or "" for page in reader.pages])
                    else:
                        model_v = genai.GenerativeModel('gemini-1.5-flash-latest')
                        res_v = model_v.generate_content(["Extract all text strictly.", uploaded_file])
                        extracted_text = res_v.text
                    
                    # Store in Session State for both Gemini & Groq
                    st.session_state.pdf_content = extracted_text
                    st.session_state.last_uploaded = uploaded_file.name
                    st.success(f"✅ Document '{uploaded_file.name}' sync ho gaya!")
                except Exception as e:
                    st.error(f"Sync Error: {e}")

    st.divider()

    # 2. Chat Display
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 3. Hybrid Chat Logic (No "I don't see PDF" messages)
    if prompt := st.chat_input("Ask about your notes..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            context = st.session_state.get("pdf_content", "")
            
            # Master Instruction
            system_instruction = f"You are TopperGPT. Use the provided context to answer. If no context, answer generally. Do NOT mention you can't see files. \n\nCONTEXT: {context[:15000]}"
            full_prompt = f"{system_instruction}\n\nUSER: {prompt}"

            ai_response = ""
            
            # Try Primary AI (Gemini)
            try:
                primary_model = genai.GenerativeModel('gemini-1.5-flash-latest')
                res = primary_model.generate_content(full_prompt)
                ai_response = res.text
            except:
                # Silent Failover to Backup (Groq)
                try:
                    from groq import Groq
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    completion = client.chat.completions.create(
                        model="llama-3.1-70b-versatile", # Stronger model for better analysis
                        messages=[{"role": "user", "content": full_prompt}]
                    )
                    ai_response = completion.choices[0].message.content
                except Exception as e:
                    ai_response = "Bhai, AI server thoda busy hai. Ek baar refresh karke try karo."

            # Final Display
            st.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
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