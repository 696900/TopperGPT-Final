import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
import re
from streamlit_mermaid import st_mermaid
from groq import Groq

# --- 1. CONFIGURATION & FIREBASE ---
st.set_page_config(page_title="TopperGPT Engineering Pro", layout="wide", page_icon="🎓")

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

# --- 2. SESSION STATE INITIALIZATION (All Keys) ---
def init_state():
    state_keys = {
        "user": None,
        "pdf_content": "",
        "messages": [],
        "roadmap": [],
        "flashcards": [],
        "last_file": None
    }
    for key, value in state_keys.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# --- 3. AUTH LOGIC ---
if st.session_state.user is None:
    st.title("🔐 Engineering TopperGPT Login")
    email = st.text_input("Email", placeholder="student@university.edu")
    password = st.text_input("Password", type="password")
    if st.button("Access Portal"):
        try:
            try: user = auth.get_user_by_email(email)
            except: user = auth.create_user(email=email, password=password)
            st.session_state.user = user.email
            st.rerun()
        except Exception as e: st.error(f"Auth Error: {e}")
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Hi, {st.session_state.user}")
        if st.button("🚀 Upgrade to PRO"):
            st.markdown("[Razorpay Link](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # --- TABS 1 TO 8 (STRICT SEQUENCE) ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "💬 Chat PDF", "📋 Syllabus Magic", "📝 Answer Eval", 
        "🧠 MindMap", "🃏 Flashcards", "❓ Engg PYQs", "🔍 Topic Search","⚖️ Legal"
    ])

    # --- TAB 1: CHAT PDF ---
    with tab1:
        st.subheader("📚 Smart Document Analysis")
        up_chat = st.file_uploader("Upload Notes", type=["pdf", "png", "jpg", "jpeg"], key="chat_up")
        if up_chat:
            with st.spinner("Scanning..."):
                if up_chat.type == "application/pdf":
                    with pdfplumber.open(io.BytesIO(up_chat.read())) as pdf:
                        st.session_state.pdf_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([{"mime_type": up_chat.type, "data": up_chat.getvalue()}, "Extract all technical text."])
                    st.session_state.pdf_content = res.text
                st.success("✅ Notes Synced!")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_in := st.chat_input("Ask anything from your notes..."):
            st.session_state.messages.append({"role": "user", "content": u_in})
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:12000]}\n\nQ: {u_in}"}])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # --- TAB 2: SYLLABUS MAGIC ---
    with tab2:
        st.subheader("📋 University Syllabus Roadmap")
        syll_f = st.file_uploader("Upload Syllabus PDF", type=["pdf"], key="syll_up")
        if syll_f and st.button("Magic: Generate Roadmap"):
            with st.spinner("AI Reading Syllabus..."):
                with pdfplumber.open(io.BytesIO(syll_f.read())) as pdf:
                    raw_s = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Extract engineering chapters and topics as a clean list: {raw_s[:10000]}")
                st.session_state.roadmap = [line.strip() for line in res.text.split("\n") if line.strip()]
        for i, topic in enumerate(st.session_state.roadmap):
            st.checkbox(topic, key=f"syll_chk_{i}")

    # --- TAB 3: ANSWER EVALUATOR ---
    with tab3:
        st.subheader("📝 Engineering Answer Evaluator")
        q_eval = st.text_area("Question (Paste from paper/book):")
        ans_eval = st.file_uploader("Upload Handwritten Answer Image", type=["png", "jpg", "jpeg"], key="eval_up")
        if st.button("Evaluate Now") and q_eval and ans_eval:
            with st.spinner("Checking accuracy..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([{"mime_type": ans_eval.type, "data": ans_eval.getvalue()}, f"Evaluate for question: {q_eval}. Mark out of 10 and give technical feedback."])
                st.info(res.text)

    # --- TAB 4: MIND MAP (SYNTAX ERROR FIXED) ---
    with tab4:
        st.subheader("🧠 Concept MindMap & Summary")
        m_mode = st.radio("Source:", ["Enter Topic", "Use File"], horizontal=True)
        m_txt = st.text_input("Engineering Topic:") if m_mode == "Enter Topic" else st.session_state.pdf_content[:4000]
        
        if st.button("Generate Visual Map") and m_txt:
            with st.spinner("Creating..."):
                prompt = f"1. Technical Summary (5 lines). 2. Mermaid graph TD code ONLY. Topic: {m_txt}. FORMAT: ---SUMMARY--- [text] ---MERMAID--- [code]"
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                out = res.choices[0].message.content
                if "---MERMAID---" in out:
                    st.info(out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip())
                    code = re.search(r"graph TD.*", out, re.DOTALL).group(0).replace("```", "").strip()
                    st_mermaid(code)

    # --- TAB 5: FLASHCARDS ---
    with tab5:
        st.subheader("🃏 Smart Engineering Flashcards")
        if st.button("Generate AI Cards"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Create 5 Flashcards (Q|A) from: {st.session_state.pdf_content[:5000]}"}])
                st.session_state.flashcards = res.choices[0].message.content.split("\n")
            else: st.warning("Upload notes in Tab 1 first.")
        for card in st.session_state.flashcards:
            if "|" in card:
                q, a = card.split("|")
                with st.expander(f"Q: {q}"): st.write(f"A: {a}")

    # --- TAB 6: ENGG PYQS ---
    with tab6:
        st.subheader("❓ University Verified PYQs")
        c1, c2 = st.columns(2)
        univ = c1.selectbox("University:", ["Mumbai University", "DBATU", "Pune University", "VTU", "GTU", "Other"])
        sem = c2.selectbox("Semester:", [f"Semester {i}" for i in range(1, 9)])
        subj = st.text_input("Subject & Branch:")
        if st.button("Fetch PYQs"):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"5 Real PYQs for {univ}, {sem}, {subj}. Tag [VERIFIED] if year is known."}])
            st.write(res.choices[0].message.content)

    # --- TAB 7: TOPIC SEARCH ---
    with tab7:
        st.subheader("🔍 Instant Topic Research")
        s_query = st.text_input("Search Engineering Topic (e.g., Fourier Transform):")
        if st.button("Deep Dive Search") and s_query:
            with st.spinner("Analyzing Topic..."):
                prompt = f"Detailed technical summary, Mermaid flowchart code, and 2 PYQs for topic: {s_query}. Format: ---SUMMARY--- [text] ---MERMAID--- [code] ---PYQ--- [questions]"
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                out = res.choices[0].message.content
                if "---SUMMARY---" in out:
                    st.markdown("### 📝 Technical Concept")
                    st.info(out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip())
                    st.markdown("### 📊 Architecture")
                    code = re.search(r"graph TD.*", out.split("---MERMAID---")[1], re.DOTALL).group(0).split("---PYQ---")[0].replace("```", "").strip()
                    st_mermaid(code)
                    st.markdown("### ❓ Expected Questions")
                    st.warning(out.split("---PYQ---")[1].strip())

     # --- TAB 8: LEGAL ---
    with tab8:
        st.header("⚖️ Engineering Policies")
        with st.expander("🛡️ Privacy Policy"): st.write("We protect engineering data using Firebase Encryption.")
        with st.expander("📜 Terms & Support"): st.write("For help: support@toppergpt.com")
                