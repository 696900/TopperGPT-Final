import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import razorpay
from youtube_transcript_api import YouTubeTranscriptApi
import pdfplumber
import io
from gtts import gTTS
from streamlit_mermaid import st_mermaid
from groq import Groq

# --- 1. CONFIGURATION & FIREBASE INIT ---
st.set_page_config(page_title="TopperGPT", layout="wide", page_icon="🎓")

if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            # Converting secrets to dict and fixing the private_key format
            fb_dict = dict(st.secrets["firebase"])
            fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        else:
            st.error("❌ Firebase block missing in Secrets!")
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
    st.title("🔐 TopperGPT Login")
    st.write("Apne AI Study Partner ke sath padhai shuru karein.")
    email = st.text_input("Email", placeholder="example@gmail.com")
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

# --- 4. MAIN APP ---
if st.session_state.user is None:
    login_page()
else:
    # SIDEBAR
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"User: {st.session_state.user}")
        st.divider()
        st.subheader("💎 PRO Version")
        if st.button("🚀 Upgrade to PRO"):
            st.markdown(f"[Payment Link](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # TABS (Sequence 1-5)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat PDF", "🎥 YT Notes", "🎙️ Podcast", "🧠 Mind Map", "📝 Quiz"
    ])

    # TAB 1: PDF CHAT (Fixed for 404 Error)
    with tab1:
        st.subheader("📚 Analyze Notes")
        uploaded_file = st.file_uploader("Upload Notes", type=["pdf", "png", "jpg", "jpeg"])
        if uploaded_file:
            if st.session_state.pdf_content == "" or st.session_state.get("last_file") != uploaded_file.name:
                with st.spinner("🧠 Scanning..."):
                    try:
                        file_bytes = uploaded_file.read()
                        text = ""
                        if uploaded_file.type == "application/pdf":
                            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                                for page in pdf.pages[:25]:
                                    t = page.extract_text(); text += (t + "\n") if t else ""
                        if not text.strip():
                            # Stable Gemini Call
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            res = model.generate_content(["Extract text strictly.", {"mime_type": uploaded_file.type, "data": file_bytes}])
                            text = res.text
                        st.session_state.pdf_content = text
                        st.session_state.last_file = uploaded_file.name
                        st.success("✅ Synced!")
                    except Exception as e:
                        st.error(f"Sync failed: {e}")

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_input := st.chat_input("Ask doubts..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            with st.chat_message("user"): st.markdown(u_input)
            res = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:12000]}\n\nQ: {u_input}"}]
            )
            ans = res.choices[0].message.content
            st.chat_message("assistant").markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

    # TAB 2: YT NOTES
    with tab2:
        st.subheader("🎥 Video Summary")
        yt_url = st.text_input("YouTube URL:")
        if yt_url and st.button("Generate Summary"):
            try:
                v_id = yt_url.split("v=")[-1].split("&")[0] if "v=" in yt_url else yt_url.split("/")[-1]
                t_data = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                full_t = " ".join([t['text'] for t in t_data])
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Summarize: {full_t[:12000]}"}])
                st.markdown(res.choices[0].message.content)
            except: st.warning("Transcript band hai!")

    # TAB 3: PODCAST
    with tab3:
        st.subheader("🎙️ AI Podcast")
        p_in = st.text_area("Notes:", value=st.session_state.pdf_content[:1500])
        if st.button("Generate Audio"):
            if p_in:
                tts = gTTS(text=p_in[:1000], lang='en')
                tts.save("p.mp3"); st.audio("p.mp3")

    # TAB 4: MIND MAP
    with tab4:
        st.subheader("🧠 Flowchart Mind Map")
        src = st.radio("Source:", ["YouTube", "PDF/Image", "Topic"], horizontal=True)
        m_data = ""
        if src == "YouTube":
            yt_l = st.text_input("Link for Map:")
            m_data = f"Topic from: {yt_l}" if yt_l else ""
        elif src == "PDF/Image":
            m_data = st.session_state.pdf_content
        else:
            m_data = st.text_input("Topic Name:")

        if st.button("Generate Map"):
            if m_data:
                prompt = f"Summary first, then Mermaid.js graph TD for: {m_data[:10000]}. Format: ---SUMMARY--- [text] ---MERMAID--- [code]"
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                out = res.choices[0].message.content
                if "---MERMAID---" in out:
                    st.info(out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip())
                    st_mermaid(out.split("---MERMAID---")[1].replace("```mermaid", "").replace("```", "").strip())

    # TAB 5: QUIZ
    with tab5:
        st.subheader("📝 Practice Quiz")
        if st.button("Generate 5 MCQs"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"5 MCQs from: {st.session_state.pdf_content[:6000]}"}])
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