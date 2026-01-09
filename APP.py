import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
import pandas as pd
from streamlit_mermaid import st_mermaid
from groq import Groq
from gtts import gTTS

# --- 1. CONFIGURATION & FIREBASE ---
st.set_page_config(page_title="TopperGPT Advanced", layout="wide", page_icon="🎓")

if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Setup Error: {e}")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE (Saara Data Save Karne Ke Liye) ---
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "auto_syllabus" not in st.session_state: st.session_state.auto_syllabus = []
if "flashcards" not in st.session_state: st.session_state.flashcards = []

# --- 3. LOGIN PAGE ---
def login_page():
    st.title("🔐 TopperGPT Advanced Login")
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

# --- 4. MAIN APP ---
if st.session_state.user is None:
    login_page()
else:
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Hi, {st.session_state.user}")
        st.divider()
        st.subheader("💎 PRO Features")
        if st.button("🚀 Upgrade to PRO"):
            st.markdown("[Razorpay Link](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # --- TABS (Line Wise 1 to 7) ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💬 Chat PDF", "📋 Smart Tracker", "📝 Answer Eval", 
        "🧠 Mind Map", "🃏 Flashcards", "❓ Real PYQs", "⚖️ Legal"
    ])

    # --- TAB 1: CHAT WITH PDF (OCR Logic Included) ---
    with tab1:
        st.subheader("📚 Analyze your Study Material")
        up_1 = st.file_uploader("Upload Notes (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"], key="main_up")
        if up_1:
            if st.session_state.pdf_content == "" or st.session_state.get("last_file") != up_1.name:
                with st.spinner("🧠 Reading your notes..."):
                    try:
                        text = ""
                        if up_1.type == "application/pdf":
                            with pdfplumber.open(io.BytesIO(up_1.read())) as pdf:
                                text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                        if not text.strip():
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            res = model.generate_content([{"mime_type": up_1.type, "data": up_1.getvalue()}, "Extract text strictly."])
                            text = res.text
                        st.session_state.pdf_content = text
                        st.session_state.last_file = up_1.name
                        st.success("✅ Notes Synced!")
                    except Exception as e: st.error(f"Sync failed: {e}")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_input := st.chat_input("Ask from notes..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:12000]}\n\nQ: {u_input}"}])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # --- TAB 2: SMART SYLLABUS TRACKER (PDF SCANNER) ---
    with tab2:
        st.subheader("📋 Auto-Syllabus Planner")
        st.write("Apna Syllabus PDF upload karo, AI automatically checklist bana dega.")
        syll_up = st.file_uploader("Upload Syllabus PDF", type=["pdf"], key="syll_up")
        
        if syll_up and st.button("Generate My Roadmap"):
            with st.spinner("Analyzing Syllabus..."):
                with pdfplumber.open(io.BytesIO(syll_up.read())) as pdf:
                    syll_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                
                # Logic to convert messy PDF text into clean topics
                prompt = f"Identify all chapters and their major sub-topics from this syllabus text. Keep it concise. Text: {syll_text[:10000]}"
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(prompt)
                st.session_state.auto_syllabus = [t.strip() for t in res.text.split("\n") if t.strip()]
                st.success("Checklist Generated!")

        for i, topic in enumerate(st.session_state.auto_syllabus):
            st.checkbox(topic, key=f"topic_{i}")

    # --- TAB 3: ANSWER EVALUATOR (CONTEXT BASED) ---
    with tab3:
        st.subheader("📝 AI Answer Evaluator")
        # Step 1: Context (Question)
        target_q = st.text_area("Enter the Question (Taaki AI ko pata chale kya check karna hai):", height=100)
        # Step 2: Answer Upload
        ans_up = st.file_uploader("Upload your handwritten Answer (Photo/PDF)", type=["png", "jpg", "pdf"], key="ans_up")
        
        if st.button("Check My Answer") and target_q and ans_up:
            with st.spinner("Comparing Answer with Question Requirements..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([
                    {"mime_type": ans_up.type, "data": ans_up.getvalue()},
                    f"Task: Evaluate this answer sheet for the Question: '{target_q}'. 1. Give marks out of 10. 2. Point out missing keywords. 3. Suggest improvements."
                ])
                st.markdown("### 📊 AI Grading Report")
                st.info(res.text)

    # --- TAB 4: MIND MAP (STABLE MERMAID) ---
    with tab4:
        st.subheader("🧠 Visual Mind Map")
        m_topic = st.text_input("Topic for Map:", value=st.session_state.get("last_file", ""))
        if st.button("Generate Flowchart"):
            with st.spinner("Designing..."):
                prompt = f"Mermaid.js code strictly (graph TD) for: {m_topic}. Keep nodes short."
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                code = res.choices[0].message.content.replace("```mermaid", "").replace("```", "").strip()
                st_mermaid(code)

    # --- TAB 5: FLASHCARDS (WITH ANKI EXPORT) ---
    with tab5:
        st.subheader("🃏 Smart Flashcards")
        if st.button("Generate Cards from My Notes"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Create 5 Q&A Flashcards (Question|Answer format) from: {st.session_state.pdf_content[:5000]}"}])
                st.session_state.flashcards = res.choices[0].message.content.split("\n")
                st.success("Cards Created!")
        
        for card in st.session_state.flashcards:
            st.code(card)
        
        if st.session_state.flashcards:
            # Simple Anki CSV Export Logic
            csv_data = "Question,Answer\n" + "\n".join([c.replace("|", ",") for c in st.session_state.flashcards if "|" in c])
            st.download_button("📤 Export to Anki (.csv)", csv_data, "flashcards.csv")

    # --- TAB 6: VERIFIED PYQS (TRUST FIX) ---
    with tab6:
        st.subheader("❓ Verified PYQ Bank")
        exam_id = st.selectbox("Choose Exam:", ["JEE Main", "NEET", "Boards (CBSE/State)", "UPSC"])
        topic_id = st.text_input("Topic Name:")
        
        if st.button("Fetch Real Questions"):
            with st.spinner("Searching verified database..."):
                # Hybrid Prompt to prevent hallucination
                prompt = f"List 5 PREVIOUS YEAR QUESTIONS for {exam_id} on topic {topic_id}. Rule: If you are 100% sure of the year, tag it [REAL PYQ - YEAR]. If you are generating it, tag it [AI PRACTICE]."
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                st.write(res.choices[0].message.content)

    # --- TAB 7: LEGAL & CONTACT ---
    with tab7:
        st.header("⚖️ Legal & Policies")
        with st.expander("🛡️ Privacy & Terms"):
            st.write("We use Firebase for Auth. Your PDFs are processed but not sold. AI results should be textbook-verified.")
        st.write("Email: support@toppergpt.com | Neral, Maharashtra, India.")