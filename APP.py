import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
from streamlit_mermaid import st_mermaid
from groq import Groq
from gtts import gTTS

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
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.markdown("[Razorpay Link](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # Sequence 1 to 7 (As per your upgrade ideas)
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💬 Chat PDF", "📋 Syllabus Magic", "📝 Answer Eval", 
        "🧠 Mind Map", "🃏 Flashcards", "❓ Real PYQs", "⚖️ Legal & Policies"
    ])

    # --- TAB 1: CHAT PDF ---
    with tab1:
        st.subheader("📚 Smart Document Scan")
        up_1 = st.file_uploader("Upload Notes", type=["pdf", "png", "jpg", "jpeg"], key="main_up")
        if up_1:
            with st.spinner("🧠 Scanning..."):
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
                    st.success("✅ Notes Loaded!")
                except Exception as e: st.error(f"Error: {e}")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_input := st.chat_input("Ask from notes..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:15000]}\n\nQ: {u_input}"}])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # --- TAB 2: SYLLABUS MAGIC (LAZY FIX - PDF TO CHECKLIST) ---
    with tab2:
        st.subheader("📋 Instant Syllabus Roadmap")
        syll_up = st.file_uploader("Upload Syllabus PDF (AI will create the roadmap)", type=["pdf"])
        if syll_up and st.button("Generate My Roadmap"):
            with st.spinner("Decoding Syllabus..."):
                try:
                    with pdfplumber.open(io.BytesIO(syll_up.read())) as pdf:
                        s_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(f"Extract a list of major chapters and their sub-topics from this syllabus strictly as a clean list: {s_text[:12000]}")
                    st.session_state.syllabus_roadmap = [line.strip() for line in res.text.split("\n") if line.strip()]
                    st.success("✅ Checklist Ready!")
                except Exception as e: st.error(f"Scan failed: {e}")
        
        for i, topic in enumerate(st.session_state.syllabus_roadmap):
            st.checkbox(topic, key=f"syll_{i}")

    # --- TAB 3: ANSWER EVALUATOR (CONTEXT FIX) ---
    with tab3:
        st.subheader("📝 Contextual Answer Evaluation")
        q_text = st.text_area("Step 1: Paste Question here (Taaki AI accuracy check kare):")
        ans_up = st.file_uploader("Step 2: Upload Handwritten Answer", type=["png", "jpg", "jpeg", "pdf"], key="eval_up")
        if st.button("Evaluate Answer") and q_text and ans_up:
            with st.spinner("AI checking your work..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([
                        {"mime_type": ans_up.type, "data": ans_up.getvalue()},
                        f"Question: {q_text}. Task: Check this handwritten answer. Give marks out of 10. Mention keywords that are missing."
                    ])
                    st.info(res.text)
                except Exception as e: st.error(f"Eval Error: {e}")

    # --- TAB 4: MIND MAP ---
    with tab4:
        st.subheader("🧠 Visual Flowchart")
        m_in = st.text_input("Topic for Mind Map:")
        if st.button("Generate Flowchart"):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Mermaid graph TD code for: {m_in}"}])
            st_mermaid(res.choices[0].message.content.replace("```mermaid", "").replace("```", "").strip())

    # --- TAB 5: FLASHCARDS (MOBILE FIX & ANKI) ---
    with tab5:
        st.subheader("🃏 Smart Swipe Flashcards")
        if st.button("Create Cards from My Notes"):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Create 5 Q&A Flashcards (Question|Answer format) from: {st.session_state.pdf_content[:5000]}"}])
            st.session_state.flashcards = res.choices[0].message.content.split("\n")
        
        for card in st.session_state.flashcards:
            if "|" in card:
                q, a = card.split("|")
                with st.expander(f"Question: {q}"): st.write(f"Answer: {a}")
        
        if st.session_state.flashcards:
            csv_data = "Question,Answer\n" + "\n".join([c.replace("|", ",") for c in st.session_state.flashcards if "|" in c])
            st.download_button("📤 Export to Anki (.csv)", csv_data, "cards.csv")

    # --- TAB 6: VERIFIED PYQS (TRUST FIX) ---
    with tab6:
        st.subheader("❓ Verified PYQ Bank")
        e_name = st.selectbox("Exam:", ["JEE", "NEET", "Boards", "UPSC"])
        t_name = st.text_input("Topic for PYQs:")
        if st.button("Get Questions"):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"List 5 REAL PYQs for {e_name} on topic {t_name}. Strictly tag as [VERIFIED - YEAR] only if 100% sure, otherwise [PRACTICE]."}] )
            st.write(res.choices[0].message.content)

    # --- TAB 7: LEGAL & POLICIES (DETAILED) ---
    with tab7:
        st.header("⚖️ Legal, Terms & Policies")
        with st.expander("🛡️ Privacy Policy", expanded=True):
            st.write("We use Firebase for secure auth. Uploaded PDFs are discarded after processing.")
        with st.expander("📜 Terms of Service"):
            st.write("TopperGPT is for study only. Verify AI results with textbooks.")
        st.write("Email: support@toppergpt.com | 📍 Neral, Maharashtra, India.")