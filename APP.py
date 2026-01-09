import streamlit as st
import google.generativeai as genai
import os
import firebase_admin
from firebase_admin import credentials, auth
import razorpay
from youtube_transcript_api import YouTubeTranscriptApi
import pdfplumber
import io
from gtts import gTTS
from streamlit_mermaid import st_mermaid
from groq import Groq

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="TopperGPT", layout="wide", page_icon="🎓")

# Firebase Initialization
if not firebase_admin._apps:
    try:
        # Dashboard secrets se firebase credentials lena
        cred_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Secrets missing or invalid: {e}")

# API Clients Setup
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. LOGIN PAGE ---
def login_page():
    st.title("🔐 TopperGPT Login")
    st.write("Apne AI Study Partner ke sath padhai shuru karein.")
    
    email = st.text_input("Email", placeholder="example@gmail.com")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login / Sign Up"):
            try:
                # Basic Auth Flow
                try:
                    user = auth.get_user_by_email(email)
                except:
                    user = auth.create_user(email=email, password=password)
                st.session_state.user = user.email
                st.rerun()
            except Exception as e:
                st.error(f"Auth Error: {e}")
    with col2:
        st.write("Google One-Tap: Coming Soon 🚀")

# --- 4. MAIN APP LOGIC ---
if st.session_state.user is None:
    login_page()
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Hi, {st.session_state.user}!")
        st.divider()
        st.subheader("💎 PRO Version")
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.markdown(f"[Proceed to Payment](https://rzp.io/l/your_link)") 
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # --- TABS (LINE WISE 1-5) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat with PDF/Image", 
        "🎥 YouTube Notes", 
        "🎙️ AI Podcast", 
        "🧠 Mind Map", 
        "📝 AI Quiz"
    ])

    # --- TAB 1: PDF/IMAGE CHAT ---
    with tab1:
        st.subheader("📚 Analyze your Notes")
        uploaded_file = st.file_uploader("Upload Notes (PDF/JPG/PNG)", type=["pdf", "png", "jpg", "jpeg"])
        
        if uploaded_file:
            if st.session_state.pdf_content == "" or st.session_state.get("last_file") != uploaded_file.name:
                with st.spinner("🧠 AI scanning your notes..."):
                    file_bytes = uploaded_file.read()
                    text = ""
                    # PDF Extraction
                    if uploaded_file.type == "application/pdf":
                        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                            for page in pdf.pages[:25]:
                                t = page.extract_text()
                                if t: text += t + "\n"
                    # Vision OCR Backup
                    if not text.strip():
                        # Stable version fix for 404
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(["Extract all text strictly.", {"mime_type": uploaded_file.type, "data": file_bytes}])
                        text = res.text
                    
                    st.session_state.pdf_content = text
                    st.session_state.last_file = uploaded_file.name
                    st.success("✅ Content Synced!")

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if u_input := st.chat_input("Ask from your notes..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            with st.chat_message("user"): st.markdown(u_input)
            
            with st.chat_message("assistant"):
                # Using Groq for fast response
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:12000]}\n\nQ: {u_input}"}]
                )
                ans = res.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})

    # --- TAB 2: YOUTUBE NOTES ---
    with tab2:
        st.subheader("🎥 Video to Detailed Notes")
        yt_url = st.text_input("Paste YouTube Link:")
        if yt_url and st.button("Generate Summary"):
            with st.spinner("Watching video..."):
                try:
                    v_id = yt_url.split("v=")[-1].split("&")[0] if "v=" in yt_url else yt_url.split("/")[-1]
                    transcript = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                    full_text = " ".join([t['text'] for t in transcript])
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f"Create detailed bullet-point notes: {full_text[:12000]}"}]
                    )
                    st.markdown(res.choices[0].message.content)
                except:
                    st.warning("Transcript band hai! Please try another video or use Mind Map.")

    # --- TAB 3: PODCAST ---
    with tab3:
        st.subheader("🎙️ AI Podcast")
        p_input = st.text_area("Notes to Audio:", value=st.session_state.pdf_content[:1500])
        if st.button("Create Podcast"):
            if p_input:
                tts = gTTS(text=p_input[:1000], lang='en')
                tts.save("p.mp3")
                st.audio("p.mp3")

    # --- TAB 4: DEEP MIND MAP LOGIC ---
    with tab4:
        st.subheader("🧠 Professional AI Mind Map")
        src = st.radio("Source:", ["YouTube", "PDF/Image", "Topic"], horizontal=True)
        m_text = ""
        
        if src == "YouTube":
            yt_l = st.text_input("Video URL for Map:")
            if yt_l:
                try:
                    v_id = yt_l.split("v=")[-1].split("&")[0] if "v=" in yt_l else yt_l.split("/")[-1]
                    try:
                        t_data = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                        m_text = " ".join([t['text'] for t in t_data])
                    except:
                        m_text = f"Topic from video link: {yt_l}"
                except: st.error("Link issue!")

        elif src == "PDF/Image":
            m_text = st.session_state.pdf_content
            if not m_text: st.warning("Pehle Tab 1 mein file upload karein.")

        elif src == "Topic":
            m_text = st.text_input("Enter Topic (e.g. 'Photosynthesis'):")

        if st.button("Generate Mind Map"):
            if m_text:
                with st.spinner("Designing Flowchart..."):
                    prompt = f"1. 4-line Summary. 2. Mermaid.js flowchart (graph TD) for: {m_text[:10000]}. Format: ---SUMMARY--- [text] ---MERMAID--- [code]"
                    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                    out = res.choices[0].message.content
                    if "---MERMAID---" in out:
                        st.info(out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip())
                        clean_m = out.split("---MERMAID---")[1].replace("```mermaid", "").replace("```", "").strip()
                        st_mermaid(clean_m)

    # --- TAB 5: AI QUIZ ---
    with tab5:
        st.subheader("📝 Practice Quiz")
        if st.button("Generate 5 MCQs"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Generate 5 MCQs from: {st.session_state.pdf_content[:6000]}"}]
                )
                st.markdown(res.choices[0].message.content)
            else: st.warning("Tab 1 mein notes upload karein.")
            
    # --- 6. LEGAL & POLICIES (Razorpay Fix) --- #
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