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

# Firebase Setup
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except:
        st.error("Firebase Secrets missing in Streamlit Dashboard!")

# API Clients
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. LOGIN SYSTEM ---
def login_page():
    st.title("🔐 TopperGPT Login")
    st.write("Apne AI Study Partner ke sath padhai shuru karein.")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login / Sign Up"):
            try:
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
    # --- SIDEBAR (Razorpay & User Info) ---
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Logged in: {st.session_state.user}")
        st.divider()
        st.subheader("💎 PRO Version")
        st.write("Unlock Unlimited Features for ₹99")
        if st.button("🚀 Upgrade to PRO"):
            st.markdown(f"[Pay via Razorpay](https://rzp.io/l/your_link)") # Replace with real link
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # --- TABS 1 TO 5 (LINE WISE) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat with PDF/Image", 
        "🎥 YouTube Notes", 
        "🎙️ AI Podcast", 
        "🧠 Mind Map", 
        "📝 AI Quiz"
    ])

    # --- TAB 1: PDF/IMAGE CHAT ---
    with tab1:
        st.subheader("📚 Study with your Notes")
        uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
        
        if uploaded_file:
            if st.session_state.pdf_content == "" or st.session_state.get("last_file") != uploaded_file.name:
                with st.spinner("🧠 Scanning Content..."):
                    file_bytes = uploaded_file.read()
                    text = ""
                    if uploaded_file.type == "application/pdf":
                        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                            for page in pdf.pages[:25]:
                                t = page.extract_text()
                                if t: text += t + "\n"
                    if not text.strip():
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content(["Extract text strictly.", {"mime_type": uploaded_file.type, "data": file_bytes}])
                        text = res.text
                    st.session_state.pdf_content = text
                    st.session_state.last_file = uploaded_file.name
                    st.success("✅ Content Loaded!")

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if u_input := st.chat_input("Puchiye apne sawal..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            with st.chat_message("user"): st.markdown(u_input)
            
            with st.chat_message("assistant"):
                ctx = st.session_state.pdf_content
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Context: {ctx[:15000]}\n\nQuestion: {u_input}"}]
                )
                ans = res.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})

    # --- TAB 2: YOUTUBE NOTES ---
    with tab2:
        st.subheader("🎥 Video to Detailed Notes")
        yt_url = st.text_input("Paste YouTube URL for Summary:")
        if yt_url and st.button("Generate Summary"):
            with st.spinner("Watching Video..."):
                try:
                    v_id = yt_url.split("v=")[-1].split("&")[0] if "v=" in yt_url else yt_url.split("/")[-1]
                    transcript = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                    full_text = " ".join([t['text'] for t in transcript])
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f"Create detailed study notes from this transcript: {full_text[:12000]}"}]
                    )
                    st.markdown(res.choices[0].message.content)
                except:
                    st.warning("Transcript disabled! Video ka mindmap Tab 4 mein try karein.")

    # --- TAB 3: AI PODCAST ---
    with tab3:
        st.subheader("🎙️ Convert Notes to Audio")
        podcast_input = st.text_area("Notes for Podcast:", value=st.session_state.pdf_content[:2000])
        if st.button("Generate Podcast Audio"):
            if podcast_input:
                with st.spinner("Generating Voice..."):
                    tts = gTTS(text=podcast_input[:1500], lang='en')
                    tts.save("podcast.mp3")
                    st.audio("podcast.mp3")
            else:
                st.error("Pehle kuch text dalo ya PDF upload karo!")

    # --- TAB 4: MIND MAP (DEEP LOGIC) ---
    with tab4:
        st.subheader("🧠 Multi-Source Flowchart Mind Map")
        source_opt = st.radio("Choose Source:", ["YouTube", "PDF/Image", "Topic"], horizontal=True)
        
        m_source_text = ""
        if source_opt == "YouTube":
            yt_link = st.text_input("YouTube Link for MindMap:")
            if yt_link:
                with st.spinner("Searching Video Content..."):
                    try:
                        v_id = yt_link.split("v=")[-1].split("&")[0] if "v=" in yt_link else yt_link.split("/")[-1]
                        try:
                            t_data = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                            m_source_text = " ".join([t['text'] for t in t_data])
                        except:
                            m_source_text = f"Analyze topic of this video: {yt_link}"
                            st.info("ℹ️ Using AI Knowledge for this link.")
                    except: st.error("Link sahi nahi hai!")

        elif source_opt == "PDF/Image":
            m_source_text = st.session_state.pdf_content
            if not m_source_text: st.warning("⚠️ Tab 1 mein file upload karein.")

        elif source_opt == "Topic":
            m_source_text = st.text_input("Enter Topic Name (e.g. 'Photosynthesis'):")

        if st.button("Generate Mind Map & Summary"):
            if m_source_text:
                with st.spinner("Designing Flowchart..."):
                    prompt = f"""
                    Tasks: 1. Provide 4-line summary. 2. Create Mermaid.js flowchart (graph TD).
                    Context: {m_source_text[:12000]}
                    Format: ---SUMMARY--- [text] ---MERMAID--- [code]
                    """
                    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                    out = res.choices[0].message.content
                    if "---MERMAID---" in out:
                        st.info(out.split("---SUMMARY---")[1].split("---MERMAID---")[0])
                        clean_m = out.split("---MERMAID---")[1].replace("```mermaid", "").replace("```", "").strip()
                        st_mermaid(clean_m)
                    else: st.markdown(out)

    # --- TAB 5: AI QUIZ ---
    with tab5:
        st.subheader("📝 AI Practice Quiz")
        if st.button("Generate Quiz from My Notes"):
            if st.session_state.pdf_content:
                with st.spinner("Creating MCQs..."):
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f"Generate 5 MCQs from this: {st.session_state.pdf_content[:6000]}"}]
                    )
                    st.markdown(res.choices[0].message.content)
            else:
                st.warning("Pehle Tab 1 mein notes upload karein!")

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