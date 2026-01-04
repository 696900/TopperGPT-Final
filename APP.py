import streamlit as st
from groq import Groq
import io
import base64
from fpdf import FPDF
from gtts import gTTS
import pypdf

# --- 1. PRO UI CONFIG ---
st.set_page_config(page_title="Topper GPT Pro", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .stApp { background: #05070A; color: #E0E6ED; }
    .main-header {
        background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 3.5em; text-align: center;
    }
    .user-card { background: #111827; border: 1px solid #1F2937; padding: 20px; border-radius: 15px; margin-bottom: 15px; border-right: 5px solid #3B82F6; }
    .ai-card { background: #0F172A; border: 1px solid #1E293B; padding: 20px; border-radius: 15px; margin-bottom: 15px; border-left: 5px solid #00F2FE; }
    .pro-badge { background: #F2D50F; color: black; padding: 2px 10px; border-radius: 5px; font-weight: bold; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURATION (Apni Keys Yahan Dalein) ---
GROQ_API_KEY = "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" #
RZP_KEY_ID = "rzp_test_RzO8qWScgIjFEl" #
# Firebase placeholder (Google Auth link ke liye)
FIREBASE_API_KEY = "AIzaSyBO3mf0cn0WCAQUHtbEfuTAliFLVlt2vqM" #

# --- 3. SESSION & BUSINESS LOGIC ---
if "auth" not in st.session_state: st.session_state.auth = False
if "is_pro" not in st.session_state: st.session_state.is_pro = False
if "credits" not in st.session_state: st.session_state.credits = 3 # Free scans

def get_groq_ans(prompt, pdf_text=""):
    client = Groq(api_key=GROQ_API_KEY)
    full_prompt = f"Act as Topper GPT Engineering Senior. Explain in Hinglish. Context from PDF: {pdf_text}\n\nQuestion: {prompt}"
    try:
        # Using Llama 3.3 (Most Stable Text Model)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": full_prompt}],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. APP INTERFACE ---
if not st.session_state.auth:
    # --- LOGIN SCREEN ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><h1 class='main-header'>Topper GPT</h1>", unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Login with Google (Firebase)")
            st.info("Firebase Project: toppergpt-521e2 is active.") #
            if st.button("🚀 Sign In with Google", use_container_width=True):
                st.session_state.auth = True
                st.session_state.user = "Krishna"
                st.rerun()
else:
    # --- PRO DASHBOARD ---
    with st.sidebar:
        st.markdown(f"### 🧑‍🎓 {st.session_state.user}")
        status = "PRO Member 👑" if st.session_state.is_pro else "FREE Tier"
        st.markdown(f"Status: **{status}**")
        if not st.session_state.is_pro:
            st.write(f"Credits Left: {st.session_state.credits}")
            if st.button("👑 Upgrade to PRO (₹99)"):
                # Mock Payment Flow
                st.session_state.is_pro = True
                st.session_state.credits = 9999
                st.success("Payment Successful!")
                st.rerun()
        
        st.markdown("---")
        pdf_file = st.file_uploader("📂 Upload Notes (PDF)", type=["pdf"])
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.auth = False; st.rerun()

    st.markdown("<h2 style='color:#00F2FE;'>🌌 Solutions Hub</h2>", unsafe_allow_html=True)

    # Check for credits
    if st.session_state.credits <= 0 and not st.session_state.is_pro:
        st.error("🚨 Free Limit Reached! Please upgrade to continue.")
    else:
        query = st.chat_input("Ask your engineering doubt...")
        
        if query:
            st.markdown(f'<div class="user-card"><b>🧑‍🎓 You:</b> {query}</div>', unsafe_allow_html=True)
            
            with st.spinner("Analyzing with Groq LPU Engine..."):
                # PDF Reading
                pdf_context = ""
                if pdf_file:
                    reader = pypdf.PdfReader(pdf_file)
                    pdf_context = " ".join([page.extract_text() for page in reader.pages[:3]])
                
                ans = get_groq_ans(query, pdf_context)
                st.markdown(f'<div class="ai-card"><b>🤖 Topper GPT:</b> {ans}</div>', unsafe_allow_html=True)
                
                # Credits deduct karo
                if not st.session_state.is_pro: st.session_state.credits -= 1
                
                # Audio Autoplay
                tts = gTTS(text=ans[:300], lang='hi')
                fp = io.BytesIO(); tts.write_to_fp(fp); fp.seek(0)
                st.audio(fp, format="audio/mp3", autoplay=True)