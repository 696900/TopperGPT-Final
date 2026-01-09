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

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="TopperGPT Pro", layout="wide", page_icon="🎓")

if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Error: {e}")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. LOGIN PAGE ---
def login_page():
    st.title("🔐 TopperGPT Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login / Sign Up"):
        try:
            try: user = auth.get_user_by_email(email)
            except: user = auth.create_user(email=email, password=password)
            st.session_state.user = user.email
            st.rerun()
        except Exception as e: st.error(f"Auth Error: {e}")

# --- 4. MAIN APP ---
if st.session_state.user is None:
    login_page()
else:
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Hi, {st.session_state.user}")
        st.divider()
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.markdown("[Pay via Razorpay](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # Sequence of Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💬 Chat PDF", "🎥 YT Notes", "🎙️ Podcast", "🧠 Mind Map", "📝 Quiz", "⚖️ Legal"
    ])

    # --- TAB 1: PDF CHAT ---
    with tab1:
        st.subheader("📚 Analyze Notes")
        up_1 = st.file_uploader("Upload Notes", type=["pdf", "png", "jpg", "jpeg"], key="main_up")
        if up_1:
            if st.session_state.pdf_content == "" or st.session_state.get("last_file") != up_1.name:
                with st.spinner("🧠 Scanning..."):
                    try:
                        text = ""
                        if up_1.type == "application/pdf":
                            with pdfplumber.open(io.BytesIO(up_1.read())) as pdf:
                                text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                        if not text.strip():
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            res = model.generate_content([{"mime_type": up_1.type, "data": up_1.getvalue()}, "Extract all text."])
                            text = res.text
                        st.session_state.pdf_content = text
                        st.session_state.last_file = up_1.name
                        st.success("✅ Content Loaded!")
                    except Exception as e: st.error(f"Sync failed: {e}")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_input := st.chat_input("Ask doubts..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:12000]}\n\nQ: {u_input}"}])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # --- TAB 2: YT NOTES ---
    with tab2:
    st.subheader("🎥 Video to Smart Study Notes")
    yt_url = st.text_input("YouTube Video Link dalo:", placeholder="https://www.youtube.com/watch?v=...")
    
    if yt_url and st.button("Generate Smart Notes", key="yt_btn"):
        with st.spinner("📺 Video analyze ho rahi hai..."):
            try:
                # 1. Video ID Extract karna
                if "v=" in yt_url:
                    v_id = yt_url.split("v=")[1].split("&")[0]
                else:
                    v_id = yt_url.split("/")[-1].split("?")[0]
                
                # 2. Transcript fetch karne ki koshish (English + Hindi)
                transcript_text = ""
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                    transcript_text = " ".join([t['text'] for t in transcript_data])
                except:
                    transcript_text = "" # Transcript nahi mili

                # 3. AI ko bhej rahe hain (Summary ke liye)
                if transcript_text:
                    prompt = f"Summarize this YouTube lecture in detail with bullet points and key takeaways: {transcript_text[:15000]}"
                else:
                    # Agar transcript nahi hai, toh AI ko link aur topic fetch karne ko bolenge
                    prompt = f"Is YouTube video ke topic par detailed study notes banaiye: {yt_url}. Agar video access nahi ho rahi, toh link se topic identify karke us par notes dein."

                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("### 📝 Detailed Lecture Notes")
                st.write(res.choices[0].message.content)
                
                # Download Option
                st.download_button("📥 Download Notes", res.choices[0].message.content, file_name="yt_notes.txt")

            except Exception as e:
                st.error(f"⚠️ Error: Video link sahi nahi hai ya private hai. {e}")

    # --- TAB 3: PODCAST ---
    with tab3:
        st.subheader("🎙️ AI Podcast")
        p_txt = st.text_area("Script:", value=st.session_state.pdf_content[:1500])
        if st.button("Generate Audio"):
            tts = gTTS(text=p_txt[:1000], lang='en')
            tts.save("p.mp3"); st.audio("p.mp3")

    # --- TAB 4: MIND MAP (ISOLATED) ---
    with tab4:
        st.subheader("🧠 Visual Flowchart Mind Map")
        m_src = st.radio("Source:", ["Upload New File", "Use Tab 1 Content", "Topic"], horizontal=True)
        m_data = ""

        if m_src == "Upload New File":
            up_m = st.file_uploader("Mind Map file dalein:", type=["pdf", "png", "jpg", "jpeg"], key="m_up")
            if up_m:
                if up_m.type == "application/pdf":
                    with pdfplumber.open(io.BytesIO(up_m.read())) as pdf:
                        m_data = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([{"mime_type": up_m.type, "data": up_m.getvalue()}, "Extract text."])
                    m_data = res.text
        elif m_src == "Use Tab 1 Content":
            m_data = st.session_state.pdf_content
        else:
            m_data = st.text_input("Topic Name:")

        if st.button("Generate Mind Map"):
            if m_data:
                with st.spinner("Designing..."):
                    prompt = f"1. 4-line summary. 2. Mermaid code ONLY (graph TD). Context: {m_data[:10000]}. Format: ---SUMMARY--- [text] ---MERMAID--- [code]"
                    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                    out = res.choices[0].message.content
                    if "---MERMAID---" in out:
                        st.info(out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip())
                        mer_code = out.split("---MERMAID---")[1].replace("```mermaid", "").replace("```", "").strip()
                        st_mermaid(mer_code)
                        st.download_button("📥 Download Map Code", mer_code, "map.txt")

    # --- TAB 5: QUIZ ---
    with tab5:
        st.subheader("📝 AI Quiz")
        if st.button("Generate 5 MCQs"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"5 MCQs from: {st.session_state.pdf_content[:6000]}"}])
                st.markdown(res.choices[0].message.content)

    # --- TAB 6: LEGAL & POLICIES (ISOLATED) ---
    with tab6:
        st.subheader("⚖️ Legal & Policies")
        st.write("Last Updated: Jan 9, 2026")
        with st.expander("Privacy Policy"):
            st.write("Hum aapka data store nahi karte. Firebase login secure hai.")
        with st.expander("Contact Us"):
            st.write("Email: support@toppergpt.com | Maharashtra, India.")