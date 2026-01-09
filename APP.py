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
            fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        else:
            st.error("❌ Firebase Secrets missing in Dashboard!")
    except Exception as e:
        st.error(f"⚠️ Firebase Setup Error: {e}")

# API Clients
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. LOGIN PAGE ---
def login_page():
    st.title("🔐 Welcome to TopperGPT")
    st.write("Apne AI Study Partner ke sath padhai shuru karein.")
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

# --- 4. MAIN APP LOGIC ---
if st.session_state.user is None:
    login_page()
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Hi, {st.session_state.user}")
        st.divider()
        st.subheader("💎 Premium Plan")
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.markdown("[Proceed to Payment](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # --- TABS 1 TO 6 (COMPLETE LINE-WISE) ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💬 Chat PDF/Image", "🎥 YouTube Notes", "🎙️ AI Podcast", "🧠 Mind Map", "📝 AI Quiz", "⚖️ Legal & Policies"
    ])

    # --- TAB 1: CHAT PDF/IMAGE ---
    with tab1:
        st.subheader("📚 Analyze your Notes")
        up_1 = st.file_uploader("Chat ke liye file dalein:", type=["pdf", "png", "jpg", "jpeg"], key="main_up")
        if up_1:
            if st.session_state.pdf_content == "" or st.session_state.get("last_file") != up_1.name:
                with st.spinner("🧠 Scanning document..."):
                    try:
                        text = ""
                        if up_1.type == "application/pdf":
                            with pdfplumber.open(io.BytesIO(up_1.read())) as pdf:
                                text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                        if not text.strip():
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            res = model.generate_content([{"mime_type": up_1.type, "data": up_1.getvalue()}, "Extract all text strictly."])
                            text = res.text
                        st.session_state.pdf_content = text
                        st.session_state.last_file = up_1.name
                        st.success("✅ Document Loaded!")
                    except Exception as e: st.error(f"Sync failed: {e}")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_input := st.chat_input("Puchiye apne doubts..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            with st.chat_message("user"): st.markdown(u_input)
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:15000]}\n\nQ: {u_input}"}])
            ans = res.choices[0].message.content
            st.chat_message("assistant").markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

    # --- TAB 2: YOUTUBE NOTES (FIXED HYBRID LOGIC) ---
    with tab2:
        st.subheader("🎥 Video to Smart Study Notes")
        yt_url = st.text_input("YouTube Video Link dalo:", placeholder="https://www.youtube.com/watch?v=...", key="yt_tab2")
        if yt_url and st.button("Generate Smart Notes", key="yt_btn"):
            with st.spinner("📺 Video analyze ho rahi hai..."):
                try:
                    v_id = yt_url.split("v=")[1].split("&")[0] if "v=" in yt_url else yt_url.split("/")[-1].split("?")[0]
                    transcript_text = ""
                    try:
                        transcript_data = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                        transcript_text = " ".join([t['text'] for t in transcript_data])
                    except: transcript_text = ""

                    if transcript_text:
                        prompt = f"Summarize this YouTube lecture in detail with bullet points: {transcript_text[:15000]}"
                    else:
                        prompt = f"Is YouTube video ke topic par detailed study notes banaiye: {yt_url}"

                    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                    st.markdown("### 📝 Lecture Notes")
                    st.write(res.choices[0].message.content)
                    st.download_button("📥 Download Notes", res.choices[0].message.content, file_name="yt_notes.txt")
                except Exception as e: st.error(f"Error: {e}")

    # --- TAB 3: AI PODCAST ---
    with tab3:
        st.subheader("🎙️ AI Audio Podcast")
        p_txt = st.text_area("Podcast Script:", value=st.session_state.pdf_content[:2000], height=200)
        if st.button("Generate Audio"):
            if p_txt:
                with st.spinner("Vocals taiyar ho rahe hain..."):
                    tts = gTTS(text=p_txt[:1500], lang='en')
                    tts.save("p.mp3"); st.audio("p.mp3")

    # --- TAB 4: MIND MAP (FIXED WITH DIRECT UPLOAD) ---
    with tab4:
        st.subheader("🧠 Visual Flowchart Mind Map")
        m_src = st.radio("Choose Source:", ["PDF/Image Upload", "Use Tab 1 Content", "YouTube", "Topic"], horizontal=True)
        m_text = ""
        if m_src == "PDF/Image Upload":
            up_m = st.file_uploader("Upload for Mind Map:", type=["pdf", "png", "jpg", "jpeg"], key="m_up_tab4")
            if up_m:
                if up_m.type == "application/pdf":
                    with pdfplumber.open(io.BytesIO(up_m.read())) as pdf:
                        m_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([{"mime_type": up_m.type, "data": up_m.getvalue()}, "Extract text."])
                    m_text = res.text
        elif m_src == "Use Tab 1 Content": m_text = st.session_state.pdf_content
        elif m_src == "YouTube": 
            yt_m_url = st.text_input("Video Link for Map:")
            m_text = f"Analyze: {yt_m_url}" if yt_m_url else ""
        else: m_text = st.text_input("Enter Topic Name:")

        if st.button("🎨 Generate Mind Map"):
            if m_text:
                with st.spinner("Designing..."):
                    prompt = f"1. 4-line summary. 2. Mermaid code ONLY (graph TD). Context: {m_text[:10000]}. FORMAT: ---SUMMARY--- [text] ---MERMAID--- [code]"
                    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                    out = res.choices[0].message.content
                    if "---MERMAID---" in out:
                        sum_p = out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip()
                        mer_p = out.split("---MERMAID---")[1].replace("```mermaid", "").replace("```", "").strip()
                        st.info(sum_p)
                        st_mermaid(mer_p)
                        st.download_button("📥 Download Mind Map (Text)", mer_p, "mindmap.txt")
            else: st.error("Content dalo bhai!")

    # --- TAB 5: AI QUIZ ---
    with tab5:
        st.subheader("📝 Practice Quiz")
        if st.button("Generate 5 MCQs"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Generate 5 MCQs from: {st.session_state.pdf_content[:6000]}"}])
                st.markdown(res.choices[0].message.content)
            else: st.warning("Pehle notes upload karein (Tab 1).")

    # --- TAB 6: DETAILED LEGAL & POLICIES ---
    with tab6:
        st.header("⚖️ Legal, Policies & Contact")
        st.write("Last Updated: January 2026")
        with st.expander("🛡️ Privacy Policy", expanded=True):
            st.write("Hum sirf email collect karte hain. Uploaded documents scan ke baad discard ho jate hain.")
        with st.expander("📜 Terms of Service"):
            st.write("TopperGPT educational use ke liye hai. AI accuracy textbook se verify karein.")
        with st.expander("💰 Refund Policy"):
            st.write("Payments Razorpay se secure hain. Technical failure par refund 48h mein process hota hai.")
        st.subheader("📩 Contact Support")
        st.write("📧 Email: support@toppergpt.com | 📍 Neral, Maharashtra, India.")