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
        up_chat = st.file_uploader("Upload Engineering Notes", type=["pdf", "png", "jpg"], key="pdf_main")
        
        if up_chat:
            with st.spinner("Extracting Technical Data..."):
                if up_chat.type == "application/pdf":
                    try:
                        with pdfplumber.open(io.BytesIO(up_chat.read())) as pdf:
                            # Har page se text nikalna
                            st.session_state.pdf_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                        st.success("✅ PDF Synced Successfully!")
                    except Exception as e:
                        st.error(f"PDF Error: {e}")
                else:
                    # For Images (Handwritten notes)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([{"mime_type": up_chat.type, "data": up_chat.getvalue()}, "Extract all technical text accurately."])
                    st.session_state.pdf_content = res.text
                    st.success("✅ Image Text Extracted!")

        if ui := st.chat_input("Ask a question from your notes..."):
            if st.session_state.pdf_content:
                # Context length manage karne ke liye [:10000] limit lagayi hai
                prompt = f"Context: {st.session_state.pdf_content[:10000]}\n\nQuestion: {ui}\nAnswer as an expert engineering professor."
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                st.write("**Professor GPT:**", res.choices[0].message.content)
            else:
                st.warning("⚠️ Pehle PDF upload karein.")
    # --- TAB 2: SYLLABUS MAGIC ---
    with tab2:
        st.subheader("📋 University Syllabus Roadmap")
        syll_up = st.file_uploader("Upload Syllabus PDF", type=["pdf"], key="syll_tracker")
        
        if syll_up and st.button("Generate Study Checklist"):
            with st.spinner("Reading University Syllabus..."):
                with pdfplumber.open(io.BytesIO(syll_up.read())) as pdf:
                    syll_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                
                # Using Gemini-1.5-flash with proper configuration to avoid 404
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(f"Extract all chapter names and main topics from this syllabus as a clean bulleted list: {syll_text[:8000]}")
                
                # Clean list making
                st.session_state.roadmap = [line.strip("- ").strip() for line in res.text.split("\n") if line.strip()]
                st.success("✅ Roadmap Ready!")

        # Display Checklist
        if st.session_state.roadmap:
            st.write("### 🎯 Your Completion Tracker")
            for i, topic in enumerate(st.session_state.roadmap):
                st.checkbox(topic, key=f"roadmap_item_{i}")

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

    # --- TAB 7: ADVANCED TOPIC SEARCH (FINAL COLLEGE FIX) ---
    # --- TAB 7: TOPIC SEARCH (THE ULTIMATE BULLETPROOF VERSION) ---
    with tab7:
        st.subheader("🔍 Engineering Topic Research")
        st.write("Instant 360° Analysis: Definition, Diagram, & 5 Research-based PYQs.")
        
        # User input
        query = st.text_input("Enter Engineering Topic (e.g. Virtual Memory, BJT, Transformer):", key="search_final_final_v10")
        
        if st.button("Deep Research", key="btn_v10") and query:
            with st.spinner(f"Analyzing '{query}' for University Exams..."):
                # Strict prompt for Mermaid Version 10 stability
                prompt = f"""
                Act as an Engineering Professor. Provide a report for: '{query}'.
                Markers strictly: [1_DEF], [2_KEY], [3_CXP], [4_SMP], [5_MER], [6_PYQ].
                
                Rules for [5_MER]:
                - Provide ONLY pure Mermaid graph TD code.
                - Use square brackets [] for ALL node labels (e.g., A[Input] --> B[Process]).
                - NO round brackets (), NO quotes "", NO special characters like &.
                
                Rules for [6_PYQ]:
                - Provide exactly 5 REAL exam-oriented questions based on current university trends.
                """
                
                try:
                    # Using Groq to avoid Gemini 404 version errors
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": prompt}]
                    )
                    out = res.choices[0].message.content

                    # Robust Section Parser
                    def get_sec(m1, m2=None):
                        try:
                            s = out.split(m1)[1]
                            return s.split(m2)[0].strip() if m2 else s.strip()
                        except: return "Information being processed..."

                    # Displaying technical sections
                    st.markdown(f"## 📘 Technical Report: {query}")
                    st.info(f"**1. Standard Definition:**\n{get_sec('[1_DEF]', '[2_KEY]')}")
                    st.write(f"**2. Key Technical Keywords:**\n{get_sec('[2_KEY]', '[3_CXP]')}")
                    st.warning(f"**3. Technical Breakdown:**\n{get_sec('[3_CXP]', '[4_SMP]')}")
                    st.success(f"**4. Concept in Simple Words:**\n{get_sec('[4_SMP]', '[5_MER]')}")

                    # --- THE ULTIMATE FLOWCHART RENDERER ---
                    st.markdown("### 📊 5. Architecture Flowchart")
                    mer_raw = get_sec('[5_MER]', '[6_PYQ]')
                    
                    # Regex to isolate only the 'graph TD' part and remove AI talk
                    match = re.search(r"(graph (?:TD|LR|BT|RL)[\s\S]*?)(?=\[6_PYQ\]|---|```|$)", mer_raw)
                    
                    if match:
                        # Character cleaning to ensure Mermaid doesn't crash
                        clean_code = match.group(1).replace("```mermaid", "").replace("```", "").strip()
                        # Auto-fix: Convert rounded nodes () to square [] because AI often messes up ()
                        clean_code = clean_code.replace("(", "[").replace(")", "]")
                        
                        try:
                            st_mermaid(clean_code)
                        except Exception:
                            # If rendering still fails, show raw code so student doesn't lose data
                            st.code(clean_code, language="mermaid")
                            st.error("Visual render failed due to complex syntax, logic shown above.")
                    else:
                        st.code(mer_raw, language="mermaid")

                    # 5 Deep-researched Questions
                    st.markdown("### ❓ 6. Expected Exam Questions (PYQ Trends)")
                    st.write(get_sec('[6_PYQ]'))
                        
                except Exception as e:
                    st.error(f"System busy. Error: {e}")
    # --- TAB 8: LEGAL ---
    with tab8:
        st.header("⚖️ Legal & Policies")
        with st.expander("🛡️ Privacy Policy", expanded=True):
            st.write("We protect engineering data using Firebase Encryption. Files are not stored permanently.")
        with st.expander("📜 Terms of Service"):
            st.write("TopperGPT is an AI assistant. Cross-verify derivations with university textbooks.")
        st.write("Contact: support@toppergpt.com")