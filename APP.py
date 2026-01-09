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
        if "firebase" in st.secrets:
            fb_dict = dict(st.secrets["firebase"])
            fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Init Error: {e}")

# API Clients - Stable Models
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. LOGIN PAGE ---
def login_page():
    st.title("🔐 TopperGPT Login")
    email = st.text_input("Email", placeholder="example@gmail.com")
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
        st.success(f"Hi, {st.session_state.user}!")
        st.divider()
        st.subheader("💎 Premium Plan")
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.markdown("[Pay via Razorpay](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # Define Tabs Line-Wise (Total 6)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💬 Chat PDF/Image", "🎥 YT Notes", "🎙️ Podcast", "🧠 Mind Map", "📝 Quiz", "⚖️ Legal"
    ])

    # --- TAB 1: PDF/IMAGE CHAT ---
    with tab1:
        st.subheader("📚 Analyze Notes")
        up_chat = st.file_uploader("Upload Notes", type=["pdf", "png", "jpg", "jpeg"], key="chat_main")
        if up_chat:
            if st.session_state.pdf_content == "" or st.session_state.get("last_file") != up_chat.name:
                with st.spinner("🧠 Scanning..."):
                    try:
                        f_bytes = up_chat.read()
                        text = ""
                        if up_chat.type == "application/pdf":
                            with pdfplumber.open(io.BytesIO(f_bytes)) as pdf:
                                text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                        if not text.strip():
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            res = model.generate_content(["Extract text strictly.", {"mime_type": up_chat.type, "data": f_bytes}])
                            text = res.text
                        st.session_state.pdf_content = text
                        st.session_state.last_file = up_chat.name
                        st.success("✅ Document Synced!")
                    except Exception as e: st.error(f"Sync failed: {e}")

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_input := st.chat_input("Ask doubts..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            with st.chat_message("user"): st.markdown(u_input)
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:12000]}\n\nQ: {u_input}"}])
            ans = res.choices[0].message.content
            st.chat_message("assistant").markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

    # --- TAB 2 & 3: YT & PODCAST (Standard Logic) ---
    with tab2:
        st.subheader("🎥 Video Summary")
        y_url = st.text_input("YouTube URL:")
        if y_url and st.button("Generate Summary"):
            try:
                v_id = y_url.split("v=")[-1].split("&")[0] if "v=" in y_url else y_url.split("/")[-1]
                t_data = YouTubeTranscriptApi.get_transcript(v_id, languages=['en', 'hi'])
                full_t = " ".join([t['text'] for t in t_data])
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Summarize: {full_t[:12000]}"}])
                st.markdown(res.choices[0].message.content)
            except: st.warning("Transcript restriction. Use Mind Map.")

    with tab3:
        st.subheader("🎙️ AI Podcast")
        p_txt = st.text_area("Notes:", value=st.session_state.pdf_content[:1500])
        if st.button("Generate Audio"):
            if p_txt:
                tts = gTTS(text=p_txt[:1000], lang='en')
                tts.save("p.mp3"); st.audio("p.mp3")

    # --- TAB 4: FIXED MIND MAP (Direct Upload + Session Support) ---
    with tab4:
     st.subheader("🧠 Visual Flowchart Mind Map")
    
    # 1. Source Selection with Direct Upload Option
    m_src = st.radio("Choose Source:", ["PDF/Image Upload", "Use Tab 1 Content", "YouTube", "Topic"], horizontal=True)
    
    m_text = ""

    # --- SOURCE LOGIC ---
    if m_src == "PDF/Image Upload":
        up_m = st.file_uploader("Mind Map ke liye file dalein:", type=["pdf", "png", "jpg", "jpeg"], key="m_up_tab4")
        if up_m:
            with st.spinner("Extracting content..."):
                try:
                    if up_m.type == "application/pdf":
                        with pdfplumber.open(io.BytesIO(up_m.read())) as pdf:
                            m_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                    else:
                        # Direct stream to fix 404 error
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content([{"mime_type": up_m.type, "data": up_m.getvalue()}, "Extract all text."])
                        m_text = res.text
                    if m_text:
                        st.success("✅ File processed successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")

    elif m_src == "Use Tab 1 Content":
        m_text = st.session_state.get("pdf_content", "")
        if not m_text:
            st.warning("⚠️ Pehle Tab 1 mein file upload karein ya 'PDF/Image Upload' select karein.")

    elif m_src == "YouTube":
        yt_l = st.text_input("Video Link for Map:", placeholder="https://youtube.com/...")
        if yt_l:
            m_text = f"Analyze topic from this video link: {yt_l}"

    elif m_src == "Topic":
        m_text = st.text_input("Enter Topic Name (e.g. 'Photosynthesis'):")

    # --- GENERATION LOGIC ---
    if st.button("🎨 Generate Mind Map"):
        if m_text:
            with st.spinner("🎨 Designing your Mind Map..."):
                try:
                    # Strict prompt to ensure clean Mermaid code
                    prompt = f"""
                    You are a Master Educator. 
                    1. Provide a 4-line summary of the topic.
                    2. Create a Mermaid.js flowchart (graph TD) strictly using only nodes and arrows.
                    
                    MATERIAL: {m_text[:12000]}
                    
                    STRICT FORMAT:
                    ---SUMMARY---
                    (your text summary)
                    ---MERMAID---
                    graph TD
                    (mermaid code only)
                    """
                    
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    out = res.choices[0].message.content
                    
                    if "---MERMAID---" in out:
                        sum_p = out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip()
                        mer_p = out.split("---MERMAID---")[1].replace("```mermaid", "").replace("```", "").strip()
                        
                        st.markdown("### 📝 Concept Summary")
                        st.info(sum_p)
                        
                        st.markdown("### 📊 Visual Flowchart")
                        # Visual Flowchart Display
                        st_mermaid(mer_p)
                        
                        # Download Section
                        st.divider()
                        st.download_button("📥 Download Mind Map (Text)", mer_p, file_name="mindmap.txt")
                        st.caption("💡 Tip: Copy this text to Mermaid.live to get an image.")
                    else:
                        st.write(out)
                except Exception as e:
                    st.error(f"Generation Error: {e}")
        else:
            st.error("⚠️ Content missing! Pehle file upload karein ya topic likhein.")
    # --- TAB 5: QUIZ ---
    with tab5:
        st.subheader("📝 Practice Quiz")
        if st.button("Generate MCQs"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"5 MCQs from: {st.session_state.pdf_content[:6000]}"}])
                st.markdown(res.choices[0].message.content)
            else: st.warning("Upload notes first in Tab 1.")

    # --- TAB 6: LEGAL (Separate Tab) ---
    with tab6:
    st.header("⚖️ Legal, Policies & Contact")
    st.write("Last Updated: January 9, 2026")
    st.divider()

    # Section 1: Privacy Policy
    with st.expander("🛡️ Privacy Policy (User Data Protection)", expanded=True):
        st.write("""
        TopperGPT aapki privacy ka pura samman karta hai. Hamari privacy policy niche di gayi hai:
        
        * **Data Collection:** Hum sirf aapka email address (Firebase login ke liye) collect karte hain taaki aapka progress save ho sake.
        * **Document Security:** Aap jo bhi PDF ya Image upload karte hain, wo hamare servers par permanently store **nahi** hoti. AI use real-time mein scan karke discard kar deta hai.
        * **No Third-Party Sharing:** Hum aapka personal data ya study material kisi bhi third-party company ke sath share nahi karte.
        * **Cookies:** Hum sirf session maintain karne ke liye zaruri cookies ka use karte hain.
        """)

    # Section 2: Terms of Service
    with st.expander("📜 Terms of Service (User Agreement)", expanded=False):
        st.write("""
        TopperGPT use karne se pehle ye shartein dhyan se padhein:
        
        * **Fair Use Policy:** Ye platform educational purpose ke liye hai. AI tokens ka misuse (spamming) karne par account suspend kiya ja sakta hai.
        * **Account Security:** Aap apne login credentials ki security ke liye khud zimmedar hain.
        * **Content Accuracy:** AI dwara generate ki gayi summary ya quiz 100% accurate ho ye zaruri nahi. Hum hamesha apne textbook se verify karne ki salah dete hain.
        * **Service Availability:** Hum koshish karte hain ki app 24/7 chale, lekin maintenance ke waqt service thodi der ke liye band ho sakti hai.
        """)

    # Section 3: Payment & Refund Policy
    with st.expander("💰 Refund & Subscription Policy", expanded=False):
        st.write("""
        PRO plans aur payments ke liye niche di gayi policies lagu hain:
        
        * **Payments:** Saare payments Razorpay ke secure gateway se hote hain.
        * **Refund:** Agar payment ke baad 48 ghante tak PRO features activate nahi hote, toh aap refund claim kar sakte hain.
        * **Cancellations:** Aap apni subscription kisi bhi waqt cancel kar sakte hain, lekin current month ka payment non-refundable hoga.
        """)

    # Section 4: Contact & Support
    st.subheader("📩 Support & Contact Us")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("##### **Headquarters:**")
        st.write("TopperGPT AI Solutions")
        st.write("Neral, Karjat, Maharashtra, India - 410101")
    
    with col_r:
        st.markdown("##### **Customer Support:**")
        st.write("📧 **Email:** support@toppergpt.com")
        st.write("💬 **WhatsApp:** +91 XXX-XXX-XXXX (Query support)")
        st.write("⏱️ **Response Time:** 24-48 Working Hours")

    st.divider()
    st.caption("© 2026 TopperGPT. All rights reserved. Made with ❤️ for Students.")
       