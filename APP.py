import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
from streamlit_mermaid import st_mermaid
from groq import Groq

# --- 1. CONFIG & FIREBASE ---
st.set_page_config(page_title="TopperGPT Engineering Pro", layout="wide", page_icon="🎓")

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
if "roadmap" not in st.session_state: st.session_state.roadmap = []

# --- 3. LOGIN PAGE ---
def login_page():
    st.title("🔐 Engineering TopperGPT Login")
    email = st.text_input("Email")
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
        st.subheader("📚 Smart Note Analysis")
        up_chat = st.file_uploader("Upload Notes", type=["pdf", "png", "jpg", "jpeg"], key="chat_up")
        if up_chat:
            with st.spinner("Scanning..."):
                if up_chat.type == "application/pdf":
                    with pdfplumber.open(io.BytesIO(up_chat.read())) as pdf:
                        st.session_state.pdf_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([{"mime_type": up_chat.type, "data": up_chat.getvalue()}, "Extract text."])
                    st.session_state.pdf_content = res.text
                st.success("✅ Notes Synced!")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_in := st.chat_input("Ask doubts..."):
            st.session_state.messages.append({"role": "user", "content": u_in})
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:15000]}\n\nQ: {u_in}"}])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # --- TAB 2: SYLLABUS MAGIC (FIXED ERROR) ---
    with tab2:
        st.subheader("📋 Engineering Syllabus Roadmap")
        syll_f = st.file_uploader("Upload University Syllabus PDF", type=["pdf"])
        if syll_f and st.button("Generate Checklist"):
            with st.spinner("AI Reading Syllabus..."):
                with pdfplumber.open(io.BytesIO(syll_f.read())) as pdf:
                    raw_s = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Extract a clean list of engineering chapters and topics: {raw_s[:10000]}")
                st.session_state.roadmap = [line.strip() for line in res.text.split("\n") if line.strip()]
        
        for i, topic in enumerate(st.session_state.roadmap):
            st.checkbox(topic, key=f"syll_{i}")

    # --- TAB 3: ANSWER EVALUATOR ---
    with tab3:
        st.subheader("📝 Engineering Answer Evaluator")
        q_eval = st.text_area("Question:")
        ans_eval = st.file_uploader("Upload Answer Image", type=["png", "jpg", "jpeg"], key="eval_up")
        if st.button("Check Accuracy") and q_eval and ans_eval:
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content([{"mime_type": ans_eval.type, "data": ans_eval.getvalue()}, f"Check this answer for: {q_eval}. Give marks and missing engineering points."])
            st.info(res.text)

    # --- TAB 4: MIND MAP (DUAL MODE + SUMMARY) ---
    with tab4:
        st.subheader("🧠 Mind Map & Concept Summary")
        m_mode = st.radio("Choose Input:", ["Enter Topic", "Upload PDF/Image"], horizontal=True, key="m_mode_fix")
        m_input_text = ""
        
        if m_mode == "Enter Topic":
            m_input_text = st.text_input("Engineering Topic (e.g. 8051 Architecture):", key="m_topic_fix")
        else:
            m_up = st.file_uploader("Upload reference for Map", type=["pdf", "png", "jpg"], key="m_up_fix")
            if m_up:
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([{"mime_type": m_up.type, "data": m_up.getvalue()}, "Extract text strictly for mindmap."])
                m_input_text = res.text

        if st.button("Generate Visual Map", key="m_btn_fix") and m_input_text:
            with st.spinner("Designing Flowchart..."):
                # Strict prompt to prevent Syntax Error
                prompt = f"Tasks: 1. 5-line technical summary. 2. Mermaid graph TD code ONLY. Topic: {m_input_text[:5000]}. Format: ---SUMMARY--- [text] ---MERMAID--- [code]"
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                out = res.choices[0].message.content
                
                if "---MERMAID---" in out:
                    # Clear separation for Mermaid Version 10.2.4 compatibility
                    sum_section = out.split("---SUMMARY---")[1].split("---MERMAID---")[0].strip()
                    mer_section = out.split("---MERMAID---")[1].replace("```mermaid", "").replace("```", "").strip()
                    
                    st.info(sum_section)
                    try:
                        st_mermaid(mer_section)
                    except:
                        st.error("Syntax issues detected. Please try a more specific topic.")
    with tab5:
        st.subheader("🃏 Engineering Flashcards")
        # Added generation button because option was missing
        source_flash = st.radio("Card Source:", ["Use Current Notes", "Enter Custom Topic"], horizontal=True)
        
        if st.button("Generate AI Flashcards"):
            with st.spinner("Creating Cards..."):
                if source_flash == "Use Current Notes" and st.session_state.pdf_content:
                    f_context = st.session_state.pdf_content[:6000]
                else:
                    f_context = st.text_input("Topic Name for Flashcards:")

                if f_context:
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": f"Create 5 engineering flashcards (Question|Answer format) from: {f_context}"}]
                    )
                    st.session_state.flashcards = res.choices[0].message.content.split("\n")
                    st.success("✅ Cards Ready!")
                else:
                    st.warning("Pehle notes upload karein ya topic likhein!")

        # Display Logic
        for card in st.session_state.flashcards:
            if "|" in card:
                q, a = card.split("|")
                with st.expander(f"Question: {q.strip()}"):
                    st.write(f"**Answer:** {a.strip()}")                    
    # --- TAB 6: ENGINEERING PYQS (UNIV + SEM) ---
    with tab6:
        st.subheader("❓ Verified Engineering PYQs")
        col1, col2 = st.columns(2)
        univ = col1.selectbox("University:", ["Mumbai University (MU)", "DBATU", "Pune University (SPPU)", "VTU", "GTU", "Anna University", "Other"])
        sem = col2.selectbox("Semester:", [f"Semester {i}" for i in range(1, 9)])
        branch = st.text_input("Branch (e.g. COMP, IT, EXTC, MECH):")
        subject = st.text_input("Subject Name:")
        
        if st.button("Fetch Verified PYQs"):
            prompt = f"List 5 REAL PYQs for {univ}, {sem}, {branch}, Subject: {subject}. Tag as [VERIFIED - YEAR] if sure, else [PRACTICE]."
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
            st.write(res.choices[0].message.content)

    # --- TAB 7: LEGAL (MEDIUM DETAILED) ---
    with tab7:
        st.header("⚖️ Terms & Policies")
        with st.expander("🛡️ Privacy Policy", expanded=True):
            st.write("TopperGPT respects engineering student data privacy. We use Firebase for Auth. Files are processed real-time and not stored permanently.")
        with st.expander("📜 Terms of Service"):
            st.write("This AI is an assistant. Always cross-verify complex derivations and circuit diagrams with your university's prescribed textbooks.")
        st.write("📍 Support: support@toppergpt.com | Neral, Maharashtra.")