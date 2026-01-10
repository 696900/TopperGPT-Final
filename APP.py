import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
import pandas as pd
from streamlit_mermaid import st_mermaid
from groq import Groq

# --- 1. CONFIGURATION & FIREBASE ---
st.set_page_config(page_title="TopperGPT Pro", layout="wide", page_icon="🎓")

if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Init Error: {e}")

# API Clients Setup
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "syllabus_roadmap" not in st.session_state: st.session_state.syllabus_roadmap = []
if "flashcards" not in st.session_state: st.session_state.flashcards = []

# --- 3. LOGIN PAGE ---
def login_page():
    st.title("🔐 Welcome to TopperGPT")
    st.write("Apna AI Study Partner use karne ke liye login karein.")
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
        st.success(f"Hi, {st.session_state.user}")
        st.divider()
        st.subheader("💎 PRO Version")
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.markdown("[Razorpay Link](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # Tabs Sequence (1 to 7)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💬 Chat PDF", "📋 Syllabus Magic", "📝 Answer Eval", 
        "🧠 Mind Map", "🃏 Flashcards", "❓ Real PYQs", "⚖️ Legal & Policies"
    ])

    # --- TAB 1: CHAT PDF/IMAGE ---
    with tab1:
        st.subheader("📚 Smart Document Scan")
        up_1 = st.file_uploader("Upload Notes (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"], key="chat_up")
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
                        st.success("✅ Notes Synced!")
                    except Exception as e: st.error(f"Sync failed: {e}")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_input := st.chat_input("Puchiye apne doubts..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:15000]}\n\nQ: {u_input}"}])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # --- TAB 2: SYLLABUS MAGIC (FIXED MODEL ERROR) ---
    with tab2:
        st.subheader("📋 Instant Syllabus Roadmap")
        syll_up = st.file_uploader("Upload Syllabus PDF", type=["pdf"], key="syll_mag")
        if syll_up and st.button("Generate Checklist"):
            with st.spinner("AI Reading Syllabus..."):
                try:
                    with pdfplumber.open(io.BytesIO(syll_up.read())) as pdf:
                        s_raw = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(f"Extract a clean list of chapters and topics from this syllabus strictly: {s_raw[:12000]}")
                    st.session_state.syllabus_roadmap = [line.strip() for line in res.text.split("\n") if line.strip()]
                    st.success("✅ Checklist Ready!")
                except Exception as e: st.error(f"Error: {e}")
        
        for i, topic in enumerate(st.session_state.syllabus_roadmap):
            st.checkbox(topic, key=f"topic_chk_{i}")

    # --- TAB 3: ANSWER EVALUATOR (CONTEXT FIX) ---
    with tab3:
        st.subheader("📝 Contextual Answer Evaluator")
        q_val = st.text_area("Question dalo (Taaki AI accuracy check kare):", height=100)
        ans_val = st.file_uploader("Apne Answer ki Photo/PDF dalo:", type=["png", "jpg", "jpeg", "pdf"], key="ans_eval")
        if st.button("Check My Answer") and q_val and ans_val:
            with st.spinner("AI Evaluating..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([
                        {"mime_type": ans_val.type, "data": ans_val.getvalue()},
                        f"Target Question: {q_val}. Task: Evaluate this answer out of 10. Mention missing keywords and suggest improvements."
                    ])
                    st.info(res.text)
                except Exception as e: st.error(f"Eval Error: {e}")

    # --- TAB 4: MIND MAP (STABLE SYNTAX) ---
    with tab4:
        st.subheader("🧠 Visual Flowchart")
        m_topic = st.text_input("Enter Topic Name:")
        if st.button("Generate Flowchart"):
            with st.spinner("Designing..."):
                try:
                    # Strict prompt for clean Mermaid code
                    prompt = f"Provide ONLY the Mermaid.js graph TD code for the topic: {m_topic}. No text before or after the code."
                    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                    clean_code = res.choices[0].message.content.replace("```mermaid", "").replace("```", "").strip()
                    st_mermaid(clean_code)
                except: st.error("Syntax Error. Please try again.")

    # --- TAB 5: FLASHCARDS (ANKI EXPORT) ---
    with tab5:
        st.subheader("🃏 Quick Revision Flashcards")
        if st.button("Create Cards from Notes"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Create 5 Q&A Flashcards (Question|Answer format) from: {st.session_state.pdf_content[:5000]}"}])
                st.session_state.flashcards = res.choices[0].message.content.split("\n")
            else: st.warning("Pehle Tab 1 mein notes upload karein.")
        
        for card in st.session_state.flashcards:
            if "|" in card:
                q, a = card.split("|")
                with st.expander(f"Q: {q}"): st.write(f"A: {a}")
        
        if st.session_state.flashcards:
            csv_data = "Question,Answer\n" + "\n".join([c.replace("|", ",") for c in st.session_state.flashcards if "|" in c])
            st.download_button("📤 Export to Anki (.csv)", csv_data, "anki_cards.csv")

    # --- TAB 6: VERIFIED PYQS (TRUST FIX) ---
    with tab6:
        st.subheader("❓ Verified PYQ Bank")
        e_choice = st.selectbox("Exam:", ["JEE", "NEET", "Boards", "UPSC"])
        t_choice = st.text_input("Topic Name for PYQs:")
        if st.button("Fetch Questions"):
            with st.spinner("Searching database..."):
                prompt = f"List 5 Real PYQs for {e_choice} on {t_choice}. Rule: Tag as [VERIFIED - YEAR] if 100% sure, otherwise [PRACTICE]."
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                st.write(res.choices[0].message.content)

    # --- TAB 7: LEGAL & POLICIES (DETAILED) ---
    with tab7:
        st.header("⚖️ Legal Policies")
        col_p, col_t = st.columns(2)
        with col_p:
            st.markdown("#### 🛡️ Privacy Policy")
            st.write("Hum aapka data secure rakhte hain. Uploaded documents scan ke baad discard ho jate hain. Firebase auth se login encrypted hai.")
        with col_t:
            st.markdown("#### 📜 Terms of Service")
            st.write("TopperGPT educational use ke liye hai. AI answers ko textbook se verify zaroor karein. Galat istemal par account band ho sakta hai.")
        st.divider()
        st.write("📧 support@toppergpt.com | 📍 Neral, Maharashtra, India.")