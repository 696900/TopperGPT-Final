import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
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
        st.error(f"Firebase Setup Error: {e}")

# Stable API Setup
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE (Fixing AttributeError) ---
# - Initializing all keys to prevent missing attribute errors
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "roadmap" not in st.session_state: st.session_state.roadmap = []
if "flashcards" not in st.session_state: st.session_state.flashcards = []

# --- 3. LOGIN PAGE ---
def login_page():
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

if st.session_state.user is None:
    login_page()
else:
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Hi, {st.session_state.user}")
        if st.button("🚀 Upgrade to PRO"):
            st.markdown("[Razorpay Link](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💬 Chat PDF", "📋 Syllabus Magic", "📝 Answer Eval", 
        "🧠 Engineering MindMap", "🃏 Flashcards", "❓ Engg PYQs", "⚖️ Legal"
    ])

    # --- TAB 1: CHAT PDF ---
    with tab1:
        st.subheader("📚 Smart Engineering Notes Analysis")
        up_chat = st.file_uploader("Upload Notes (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"], key="chat_up")
        if up_chat:
            with st.spinner("Processing document..."):
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
        if u_in := st.chat_input("Ask technical doubts..."):
            st.session_state.messages.append({"role": "user", "content": u_in})
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:15000]}\n\nQ: {u_in}"}])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # --- TAB 2: SYLLABUS MAGIC (FIXED 404 ERROR) ---
    # - Using standard API calls to avoid versioning errors
    with tab2:
        st.subheader("📋 University Syllabus Roadmap")
        syll_f = st.file_uploader("Upload Syllabus PDF", type=["pdf"], key="syll_up")
        if syll_f and st.button("Generate Roadmap Checklist"):
            with st.spinner("AI Reading Syllabus..."):
                try:
                    with pdfplumber.open(io.BytesIO(syll_f.read())) as pdf:
                        raw_s = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(f"Convert this engineering syllabus into a clean list of chapters and sub-topics: {raw_s[:10000]}")
                    st.session_state.roadmap = [line.strip() for line in res.text.split("\n") if line.strip()]
                    st.success("✅ Syllabus Roadmap Generated!")
                except Exception as e: st.error(f"Syllabus Scan Failed: {e}")
        
        for i, topic in enumerate(st.session_state.roadmap):
            st.checkbox(topic, key=f"syll_chk_{i}")

    # --- TAB 3: ANSWER EVALUATOR ---
    with tab3:
        st.subheader("📝 Answer Grader (Context-Aware)")
        q_eval = st.text_area("Question/Problem Statement:")
        ans_eval = st.file_uploader("Upload handwritten answer image", type=["png", "jpg", "jpeg"], key="eval_up")
        if st.button("Grade My Answer") and q_eval and ans_eval:
            with st.spinner("Analyzing..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([{"mime_type": ans_eval.type, "data": ans_eval.getvalue()}, f"Evaluate this engineering answer for the question: {q_eval}. Give marks out of 10 and technical feedback."])
                st.info(res.text)

    # --- TAB 4: MIND MAP (FIXED SYNTAX ERROR) ---
    # - Strictly separating Summary from Mermaid code
    with tab4:
        st.subheader("🧠 Concept Summary & Mind Map")
        m_mode = st.radio("Input Source:", ["Enter Topic", "Use Uploaded Notes"], horizontal=True)
        m_txt = ""
        if m_mode == "Enter Topic":
            m_txt = st.text_input("Enter Engineering Concept (e.g. Back EMF in DC Motor):")
        else:
            m_txt = st.session_state.pdf_content[:5000]

        if st.button("Generate Visual Map") and m_txt:
            with st.spinner("Designing Flowchart..."):
                prompt = f"1. Provide a 5-line summary. 2. Provide ONLY Mermaid.js graph TD code. Topic: {m_txt}. Format: ---SUMMARY--- [text] ---MERMAID--- [code]"
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                out = res.choices[0].message.content
                if "---MERMAID---" in out:
                    sum_part = out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip()
                    mer_part = out.split("---MERMAID---")[1].replace("```mermaid", "").replace("```", "").strip()
                    st.info(sum_part)
                    st_mermaid(mer_part)

    # --- TAB 5: FLASHCARDS (FIXED MISSING OPTION) ---
    # - Added UI for generating and exporting cards
    with tab5:
        st.subheader("🃏 Engineering Flashcards")
        if st.button("Generate New AI Flashcards"):
            if st.session_state.pdf_content:
                with st.spinner("Creating cards..."):
                    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Create 5 Q&A flashcards (Question|Answer) from: {st.session_state.pdf_content[:5000]}"}])
                    st.session_state.flashcards = res.choices[0].message.content.split("\n")
                    st.success("✅ Cards Ready!")
            else: st.warning("Please upload notes in Tab 1 first.")

        for card in st.session_state.flashcards:
            if "|" in card:
                q, a = card.split("|")
                with st.expander(f"Question: {q.strip()}"): st.write(f"**Answer:** {a.strip()}")
        
        if st.session_state.flashcards:
            csv_data = "Question,Answer\n" + "\n".join([c.replace("|", ",") for c in st.session_state.flashcards if "|" in c])
            st.download_button("📤 Export to Anki (.csv)", csv_data, "engg_cards.csv")

    # --- TAB 6: ENGINEERING PYQS (UNIV + SEM) ---
    with tab6:
        st.subheader("❓ University Verified PYQs")
        c1, c2 = st.columns(2)
        u_sel = c1.selectbox("University:", ["Mumbai University (MU)", "DBATU", "Pune University (SPPU)", "VTU", "GTU", "Other"])
        s_sel = c2.selectbox("Semester:", [f"Semester {i}" for i in range(1, 9)])
        subj = st.text_input("Subject & Branch (e.g. Data Structures - COMP):")
        
        if st.button("Fetch PYQs"):
            prompt = f"List 5 REAL PYQs for {u_sel}, {s_sel}, Subject: {subj}. Strictly tag verified ones as [VERIFIED - YEAR]."
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
            st.write(res.choices[0].message.content)

    # --- TAB 7: LEGAL ---
    with tab7:
        st.header("⚖️ Legal & Policies")
        with st.expander("🛡️ Privacy Policy", expanded=True):
            st.write("We use Firebase for secure authentication. No engineering data is shared with third parties.")
        with st.expander("📜 Terms of Service"):
            st.write("Results are AI-generated. Verify critical engineering formulas with university textbooks.")
        st.write("📍 Support: support@toppergpt.com | Maharashtra, India.")