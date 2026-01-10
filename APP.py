import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
import re
from streamlit_mermaid import st_mermaid
from groq import Groq

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="TopperGPT Engineering Pro", layout="wide", page_icon="🎓")

if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Init Error: {e}")

# Stable API Setup
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE INITIALIZATION ---
# [Fixes AttributeError & State Errors]
state_keys = {
    "user": None, 
    "pdf_content": "", 
    "messages": [], 
    "roadmap": [], 
    "flashcards": []
}
for key, val in state_keys.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- 3. HELPER FUNCTIONS ---
def safe_mermaid_parser(text):
    """Extracts only valid Mermaid code to prevent Syntax Errors."""
    try:
        match = re.search(r"(graph\s+(?:TD|LR|BT|RL)[\s\S]*?)(?=\n\n|---|```|$)", text)
        if match:
            return match.group(1).strip()
        return None
    except:
        return None

# --- 4. LOGIN PAGE ---
if st.session_state.user is None:
    st.title("🔐 Engineering TopperGPT Login")
    email_in = st.text_input("Email")
    pass_in = st.text_input("Password", type="password")
    if st.button("Access Portal"):
        try:
            try:
                user = auth.get_user_by_email(email_in)
            except:
                user = auth.create_user(email=email_in, password=pass_in)
            st.session_state.user = user.email
            st.rerun()
        except Exception as e:
            st.error(f"Auth Error: {e}")
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🎓 TopperGPT Pro")
        st.success(f"User: {st.session_state.user}")
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # --- TABS (STRICT 1-8 SEQUENCE) ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "💬 Chat PDF", 
        "📋 Syllabus Magic", 
        "📝 Answer Eval", 
        "🧠 MindMap", 
        "🃏 Flashcards", 
        "❓ Engg PYQs", 
        "🔍 Topic Search", 
        "⚖️ Legal"
    ])

    # --- TAB 1: CHAT PDF ---
    with tab1:
        st.subheader("📚 Smart Note Analysis")
        up_chat = st.file_uploader("Upload Notes (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"], key="chat_up")
        if up_chat:
            with st.spinner("Processing..."):
                if up_chat.type == "application/pdf":
                    with pdfplumber.open(io.BytesIO(up_chat.read())) as pdf:
                        st.session_state.pdf_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([{"mime_type": up_chat.type, "data": up_chat.getvalue()}, "Extract all technical text."])
                    st.session_state.pdf_content = res.text
                st.success("✅ Notes Synced!")
        
        if u_chat := st.chat_input("Ask anything from your notes..."):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:10000]}\n\nQ: {u_chat}"}])
            st.write(res.choices[0].message.content)

    # --- TAB 2: SYLLABUS MAGIC ---
    with tab2:
        st.subheader("📋 Instant Syllabus Roadmap")
        syll_f = st.file_uploader("Upload Syllabus PDF", type=["pdf"], key="syll_up")
        if syll_f and st.button("Generate Roadmap"):
            with st.spinner("AI Reading Syllabus..."):
                with pdfplumber.open(io.BytesIO(syll_f.read())) as pdf:
                    raw_s = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Extract all engineering chapters and sub-topics from this syllabus as a clean list: {raw_s[:10000]}")
                st.session_state.roadmap = [line.strip() for line in res.text.split("\n") if line.strip()]
        
        for i, t in enumerate(st.session_state.roadmap):
            st.checkbox(t, key=f"s_chk_{i}")

    # --- TAB 3: ANSWER EVALUATOR ---
    with tab3:
        st.subheader("📝 Answer Grader")
        q_eval = st.text_area("Step 1: Paste Question here:")
        ans_eval = st.file_uploader("Step 2: Upload Handwritten Answer", type=["png", "jpg", "jpeg", "pdf"], key="ans_up")
        if st.button("Grade My Answer") and q_eval and ans_eval:
            with st.spinner("Evaluating..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([{"mime_type": ans_eval.type, "data": ans_eval.getvalue()}, f"Evaluate for question: {q_eval}. Give marks out of 10."])
                st.info(res.text)

    # --- TAB 4: MIND MAP ---
    # --- TAB 4: ENGINEERING MIND MAP (ULTRA-STABLE) ---
    with tab4:
        st.subheader("🧠 Concept MindMap & Summary")
        
        # Choice of source
        m_mode = st.radio("Source Selection:", ["Enter Topic", "Use File Data"], horizontal=True, key="m_src_final")
        
        # Getting input text
        if m_mode == "Enter Topic":
            m_input = st.text_input("Engineering Concept (e.g. Back EMF):", key="m_topic_final")
        else:
            m_input = st.session_state.get("pdf_content", "")[:3000]
            if not m_input:
                st.warning("⚠️ Pehle Tab 1 mein notes upload karein!")

        if st.button("Build Map", key="m_btn_final") and m_input:
            with st.spinner("Creating Visual Roadmap..."):
                # Strict prompt to force correct Mermaid structure
                prompt = f"""
                Explain the engineering concept '{m_input}' in 5 clear lines.
                Then, provide ONLY a Mermaid.js flowchart using 'graph TD'.
                Ensure every node is connected and use simple words.
                Format your response exactly like this:
                SUMMARY: [Your 5 lines here]
                MERMAID:
                graph TD
                A[Start] --> B[Process]
                """
                
                try:
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": prompt}]
                    )
                    full_out = res.choices[0].message.content

                    # 1. Extract Summary
                    if "SUMMARY:" in full_out:
                        sum_text = full_out.split("SUMMARY:")[1].split("MERMAID:")[0].strip()
                        st.info(f"**Technical Summary:**\n\n{sum_text}")

                    # 2. Extract & Fix Mermaid Code (Fixes Syntax Errors)
                    #
                    if "graph TD" in full_out:
                        # Regex to find code starting from graph TD until the end or next marker
                        match = re.search(r"graph\s+TD[\s\S]*", full_out)
                        if match:
                            clean_code = match.group(0).replace("```mermaid", "").replace("```", "").strip()
                            # Extra safety: removing conversational filler
                            clean_code = clean_code.split("\n\n")[0]
                            
                            st.markdown("---")
                            st.markdown("### 📊 Architecture Flowchart")
                            st_mermaid(clean_code)
                        else:
                            st.error("AI generated invalid diagram syntax. Please try a simpler topic.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- TAB 5: FLASHCARDS ---
    with tab5:
        st.subheader("🃏 Engineering Flashcards")
        if st.button("Generate AI Cards"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Create 5 Q&A pairs (Q|A) from: {st.session_state.pdf_content[:5000]}"}])
                st.session_state.flashcards = res.choices[0].message.content.split("\n")
            else: st.warning("Please upload notes in Tab 1 first.")
        
        for c in st.session_state.flashcards:
            if "|" in c:
                q, a = c.split("|")
                with st.expander(f"Q: {q}"): st.write(f"A: {a}")

    # --- TAB 6: ENGG PYQS ---
    with tab6:
        st.subheader("❓ University Verified PYQs")
        c1, c2 = st.columns(2)
        u_sel = c1.selectbox("Univ:", ["Mumbai University", "DBATU", "Pune University", "VTU", "GTU"])
        s_sel = c2.selectbox("Sem:", [f"Semester {i}" for i in range(1, 9)])
        subj = st.text_input("Subject/Branch:")
        if st.button("Fetch Questions"):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"5 Real PYQs for {u_sel}, {s_sel}, Subject: {subj}. Tag [VERIFIED] if year is sure."}])
            st.write(res.choices[0].message.content)

    # --- TAB 7: TOPIC SEARCH ---
    with tab7:
        st.subheader("🔍 Instant Topic Research")
        s_query = st.text_input("Enter Engineering Topic:")
        if st.button("Deep Search") and s_query:
            with st.spinner("Analyzing..."):
                prompt = f"Technical summary and Mermaid graph TD code for: {s_query}. Use markers: [SUM] [MER]"
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                raw = res.choices[0].message.content
                
                sum_part = re.search(r"\[SUM\](.*?)(?=\[MER\]|$)", raw, re.DOTALL)
                if sum_part: st.markdown(f"**Concept:** {sum_part.group(1).strip()}")
                
                m_code_search = safe_mermaid_parser(raw)
                if m_code_search: st_mermaid(m_code_search)

    # --- TAB 8: LEGAL ---
    with tab8:
        st.header("⚖️ Legal & Policies")
        with st.expander("🛡️ Privacy Policy", expanded=True):
            st.write("We protect engineering data using Firebase Encryption. Files are not stored permanently.")
        with st.expander("📜 Terms of Service"):
            st.write("TopperGPT is an AI assistant. Cross-verify derivations with university textbooks.")
        st.write("Contact: support@toppergpt.com")