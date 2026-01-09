import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
from streamlit_mermaid import st_mermaid
from groq import Groq
from gtts import gTTS
from youtube_transcript_api import YouTubeTranscriptApi

# --- 1. CONFIGURATION & FIREBASE INITIALIZATION ---
st.set_page_config(page_title="TopperGPT Pro", layout="wide", page_icon="🎓")

if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            fb_dict = dict(st.secrets["firebase"])
            # Triple quotes TOML handle karne ke liye replace logic
            fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        else:
            st.error("❌ Firebase block missing in Secrets!")
    except Exception as e:
        st.error(f"⚠️ Firebase Setup Error: {e}")

# API Clients Initialization
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("❌ API Keys (Gemini/Groq) missing in Secrets!")

# --- 2. SESSION STATE (Keep data across tabs) ---
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. LOGIN PAGE LOGIC ---
def login_page():
    st.title("🔐 Welcome to TopperGPT")
    st.write("Login karein aur apni AI padhai shuru karein.")
    email = st.text_input("Email", placeholder="example@gmail.com")
    password = st.text_input("Password", type="password")
    
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

# --- 4. MAIN APP CONTENT ---
if st.session_state.user is None:
    login_page()
else:
    # SIDEBAR (Upgrade + Logout)
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Hi, {st.session_state.user}")
        st.divider()
        st.subheader("💎 Premium Plan")
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.markdown(f"[Pay via Razorpay](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # ALL 6 TABS IN SEQUENCE
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💬 Chat PDF/Image", 
        "🎥 YouTube Notes", 
        "🎙️ AI Podcast", 
        "🧠 Mind Map", 
        "📝 AI Quiz", 
        "⚖️ Legal & Policies"
    ])

    # --- TAB 1: CHAT WITH DOCUMENTS ---
    with tab1:
        st.subheader("📚 Analyze your Notes")
        uploaded_file = st.file_uploader("Upload PDF or Image", type=["pdf", "png", "jpg", "jpeg"])
        
        if uploaded_file:
            if st.session_state.pdf_content == "" or st.session_state.get("last_file") != uploaded_file.name:
                with st.spinner("🧠 Scanning document..."):
                    try:
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
                        st.success("✅ Document Synced!")
                    except Exception as e:
                        st.error(f"Sync failed: {e}")

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if u_input := st.chat_input("Puchiye apne doubts..."):
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
        st.subheader("🎥 Video Summarizer")
        yt_url = st.text_input("Paste YouTube Link for Summary:")
        if yt_url and st.button("Generate Summary"):
            with st.spinner("Analyzing Video..."):
                try:
                    v_id = yt_url.split("v=")[-1].split("&")[0] if "v=" in yt_url else yt_url.split("/")[-1]
                    transcript = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                    full_text = " ".join([t['text'] for t in transcript])
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f"Detailed study notes: {full_text[:12000]}"}]
                    )
                    st.markdown(res.choices[0].message.content)
                except:
                    st.warning("Transcript band hai! Please try another video.")

    # --- TAB 3: PODCAST ---
    with tab3:
        st.subheader("🎙️ AI Audio Podcast")
        p_text = st.text_area("Podcast Content:", value=st.session_state.pdf_content[:2000])
        if st.button("Create Audio"):
            if p_text:
                with st.spinner("Generating..."):
                    tts = gTTS(text=p_text[:1500], lang='en')
                    tts.save("p.mp3")
                    st.audio("p.mp3")
            else:
                st.error("Content empty hai!")

    # --- TAB 4: DEEP MIND MAP (FLOWCHART) ---
    with tab4:
        st.subheader("🧠 Visual Flowchart Mind Map")
        src = st.radio("Choose Source:", ["YouTube", "PDF/Image", "Topic"], horizontal=True)
        m_data = ""
        
        if src == "YouTube":
            yt_l = st.text_input("Link for MindMap:")
            if yt_l:
                try:
                    v_id = yt_l.split("v=")[-1].split("&")[0] if "v=" in yt_l else yt_l.split("/")[-1]
                    try:
                        t_data = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                        m_data = " ".join([t['text'] for t in t_data])
                    except: m_data = f"Topic reference: {yt_l}"
                except: st.error("Link issue!")
        elif src == "PDF/Image":
            m_data = st.session_state.pdf_content
        else:
            m_data = st.text_input("Enter Topic Name:")

        if st.button("Generate Mind Map"):
            if m_data:
                with st.spinner("Designing Flowchart..."):
                    # Strict prompt to prevent Mermaid syntax error
                    prompt = f"1. 4-line summary. 2. Mermaid.js flowchart (graph TD) strictly code only. Context: {m_data[:10000]}. Format: ---SUMMARY--- [text] ---MERMAID--- [code]"
                    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                    out = res.choices[0].message.content
                    if "---MERMAID---" in out:
                        st.info(out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip())
                        clean_m = out.split("---MERMAID---")[1].replace("```mermaid", "").replace("```", "").strip()
                        st_mermaid(clean_m)

    # --- TAB 5: AI QUIZ ---
    with tab5:
        st.subheader("📝 Practice Quiz")
        if st.button("Generate MCQs"):
            if st.session_state.pdf_content:
                with st.spinner("Creating Quiz..."):
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f"Generate 5 MCQs from: {st.session_state.pdf_content[:6000]}"}]
                    )
                    st.markdown(res.choices[0].message.content)
            else: st.warning("Upload notes first!")

    # --- TAB 6: LEGAL & POLICIES ---
    with tab6:
        st.subheader("⚖️ TopperGPT Legal Information")
        st.write("Last Updated: January 2026")
        
        col_p, col_t = st.columns(2)
        with col_p:
            st.markdown("#### 🔒 Privacy Policy")
            st.write("- User login data is secured via Firebase.")
            st.write("- Uploaded PDFs are processed in real-time and not stored permanently.")
            st.write("- We do not share your data with third parties.")
        
        with col_t:
            st.markdown("#### 📜 Terms of Service")
            st.write("- TopperGPT is an AI-powered educational tool.")
            st.write("- Users are responsible for the content they upload.")
            st.write("- PRO features are subject to successful payment verification.")
        
        st.divider()
        st.markdown("#### 📧 Contact & Refund")
        st.write("For support or refund queries, contact: **support@toppergpt.com**")
        st.write("Location: Neral, Maharashtra, India.")