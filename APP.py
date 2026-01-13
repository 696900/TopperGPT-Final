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
   
    # --- TAB 1: SMART NOTE ANALYSIS (FINAL UI FIX) ---
    # --- TAB 1: SMART NOTE ANALYSIS (HYBRID MODE) ---
    with tab1:
        st.subheader("📚 Smart Note Analysis")
        
        # 1. File Uploader (Optional)
        up_notes = st.file_uploader(
            "Upload Notes (Optional - for context-based answers)", 
            type=["pdf", "png", "jpg", "jpeg"], 
            key="hybrid_uploader"
        )
        
        # 2. Background Syncing (If file is uploaded)
        if up_notes:
            if "current_file" not in st.session_state or st.session_state.current_file != up_notes.name:
                with st.spinner("Syncing technical data..."):
                    if up_notes.type == "application/pdf":
                        try:
                            with pdfplumber.open(io.BytesIO(up_notes.read())) as pdf:
                                st.session_state.pdf_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                            st.session_state.current_file = up_notes.name
                            st.toast("✅ Notes Synced! Using context mode.", icon="📚")
                        except Exception as e:
                            st.error(f"Sync Error: {e}")
                    else:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        res = model.generate_content([{"mime_type": up_notes.type, "data": up_notes.getvalue()}, "Extract text."])
                        st.session_state.pdf_content = res.text
                        st.session_state.current_file = up_notes.name
                        st.toast("✅ Image Synced!", icon="📸")

        # 3. Permanent Chat Interface (No Warning)
        st.markdown("---")
        
        # Minimal status indicator
        if st.session_state.get("pdf_content"):
            st.caption("🔍 **Mode:** Contextual (Analyzing your uploaded notes)")
        else:
            st.caption("🌐 **Mode:** General Engineering Knowledge (Hybrid Mode Active)")

        # Chat Input - ALWAYS VISIBLE AND ACTIVE
        ui_chat = st.chat_input("Ask any engineering question...")
        
        if ui_chat:
            with st.spinner("Professor GPT is thinking..."):
                # Hybrid Logic: Context + General Knowledge
                context = st.session_state.get("pdf_content", "No specific notes uploaded.")
                prompt = f"""
                You are an expert Engineering Professor. 
                Context from Student Notes (if any): {context[:12000]}
                
                Question: {ui_chat}
                
                Instructions:
                1. If the answer is in the notes, use it.
                2. If not in the notes, use your general engineering knowledge.
                3. Be technically accurate and provide a detailed explanation.
                """
                
                # Using Groq for instant results without timeout
                try:
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.markdown(f"**Professor GPT:** {res.choices[0].message.content}")
                except Exception as e:
                    st.error("Connection failed. Try again.")        
    # --- TAB 2: SYLLABUS MAGIC ---
    # --- TAB 2: SYLLABUS MAGIC (STABLE SUBJECT & MODULE LOCK) ---
    with tab2:
        st.markdown('<h3 style="text-align: center; margin-bottom: 5px;">📋 Engineering Syllabus Roadmap</h3>', unsafe_allow_html=True)
        
        syll_up = st.file_uploader("Upload Full Syllabus PDF", type=["pdf"], key="syll_final_pro_fix")
        
        if syll_up and st.button("🚀 Generate Organized Roadmap", use_container_width=True):
            with st.spinner("Extracting Semester I & II Subjects..."):
                try:
                    sem_data = {"Semester I": {}, "Semester II": {}}
                    with pdfplumber.open(io.BytesIO(syll_up.read())) as pdf:
                        total_pages = len(pdf.pages)
                        mid_page = total_pages // 2 
                        
                        # Known Engineering Subjects List for Filter
                        eng_subjects = ["Applied Mathematics", "Applied Physics", "Applied Chemistry", 
                                        "Engineering Mechanics", "Basic Electrical", "Engineering Graphics",
                                        "Programming", "Communication Skills"]

                        for i, page in enumerate(pdf.pages):
                            current_sem = "Semester I" if i < mid_page else "Semester II"
                            text = page.extract_text()
                            if not text: continue
                            
                            # Finding the Subject Name on the page
                            current_subj = "General Engineering"
                            for sub in eng_subjects:
                                if sub.lower() in text.lower():
                                    current_subj = sub
                                    break
                            
                            # Extracting 6 Modules strictly
                            modules = []
                            for line in text.split('\n'):
                                if any(line.strip().startswith(f"{n}") for n in ["01", "02", "03", "04", "05", "06"]):
                                    clean_m = line.strip()
                                    if len(clean_m) > 15 and clean_m not in modules:
                                        modules.append(clean_m)
                            
                            if len(modules) >= 4: # Validating it's a real syllabus page
                                if current_subj not in sem_data[current_sem]:
                                    sem_data[current_sem][current_subj] = modules[:6]

                    st.session_state.sem_data = sem_data
                    st.session_state.done_topics = []
                    st.success("✅ Syllabus Organized. Ab padhai par dhyan de!")
                except Exception as e:
                    st.error(f"Syllabus Error: {e}")

        # --- PROGRESS DASHBOARD (SLEEK & WORKING) ---
        if st.session_state.get("sem_data"):
            # Collecting ALL module IDs for calculation
            all_m_keys = []
            for sem, subs in st.session_state.sem_data.items():
                for s_name, m_list in subs.items():
                    for m_name in m_list:
                        all_m_keys.append(f"{sem}_{s_name}_{m_name}".replace(" ","_"))
            
            t_count = len(all_m_keys)
            # Logic to ensure tick updates the bar
            current_done = [d for d in st.session_state.get("done_topics", []) if d in all_m_keys]
            prog = int((len(current_done) / t_count) * 100) if t_count > 0 else 0

            # --- IPHONE SLEEK BAR UI ---
            st.markdown(f"""
                <style>
                    .stProgress > div > div > div > div {{ height: 8px !important; background-color: #4CAF50; border-radius: 10px; }}
                </style>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; padding: 0 5px;">
                    <span style="font-weight: bold; font-size: 14px;">MASTERY STATUS</span>
                    <span style="font-weight: bold; color: #4CAF50; font-size: 20px;">{prog}%</span>
                </div>
            """, unsafe_allow_html=True)
            st.progress(prog / 100)
            st.caption(f"Done: {len(current_done)} / Total: {t_count} Modules")

            st.divider()
            t1, t2 = st.tabs(["📘 Semester I", "📗 Semester II"])

            def render_modules(data, sem_tag):
                if not data:
                    st.info(f"No modules found for {sem_tag}. Regenerate please.")
                    return
                for subject, modules in data.items():
                    with st.expander(f"📚 {subject}"):
                        for m in modules:
                            u_key = f"{sem_tag}_{subject}_{m}".replace(" ", "_")
                            # Proper sequencing and tick handling
                            if st.checkbox(m, key=u_key, value=(u_key in st.session_state.done_topics)):
                                if u_key not in st.session_state.done_topics:
                                    st.session_state.done_topics.append(u_key)
                                    st.rerun()
                            else:
                                if u_key in st.session_state.done_topics:
                                    st.session_state.done_topics.remove(u_key)
                                    st.rerun()

            with t1: render_modules(st.session_state.sem_data["Semester I"], "S1")
            with t2: render_modules(st.session_state.sem_data["Semester II"], "S2")

            # --- BRANDED DOWNLOAD & SHARE ---
            st.divider()
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                st.download_button("📥 Download Tracker", f"TopperGPT Report: {prog}% Done", use_container_width=True)
            with c_d2:
                share_url = f"https://wa.me/?text=TopperGPT%20Mastery:%20{prog}%25"
                st.markdown(f'<a href="{share_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer;">Share Progress 🚀</button></a>', unsafe_allow_html=True)
    # --- TAB 3: ANSWER EVALUATOR ---
   # --- TAB 3: ANSWER EVALUATOR (STRICT MODERATOR MODE) ---
    with tab3:
        st.subheader("🖋️ Board Moderator: Answer Evaluation")
        st.write("Upload your handwritten answer. I will grade you like a strict University Examiner.")

        # 1. Context Setting (Morphine Strategy: Question is must)
        q_text = st.text_area("Step 1: Paste the Question here (so I can grade accurately):", placeholder="e.g. Explain the working of a BJT as an amplifier.")
        
        # 2. Image Upload
        ans_img = st.file_uploader("Step 2: Upload your handwritten answer (Image/PDF)", type=["png", "jpg", "jpeg", "pdf"])

        if st.button("🔍 Evaluate My Answer") and ans_img and q_text:
            with st.spinner("Moderator is checking your paper... Be ready for honest feedback."):
                try:
                    # Vision model call (Gemini for Image analysis)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Preparing the image data
                    img_data = ans_img.getvalue()
                    
                    # THE "STRICT MODERATOR" PROMPT (Your Founder Strategy)
                    moderator_prompt = f"""
                    ROLE: Strict Indian University Board Examiner (20 years experience).
                    QUESTION: {q_text}
                    
                    GRADING RULES:
                    1. Scan for Technical Keywords. No keywords = Heavy penalty.
                    2. Check for Diagram/Formula. If missing but required, deduct 50% marks.
                    3. Presentation: Underlining, labeling, and step-wise logic matter.
                    4. Illegible Handwriting = 0 marks.
                    
                    OUTPUT FORMAT (Strictly follow this):
                    ## 📊 PROVISIONAL SCORE: [X/10]
                    
                    ### ✅ WHAT YOU DID WELL:
                    (1 short sentence)
                    
                    ### ❌ WHY YOU LOST MARKS:
                    (Bullet points with specific misses)
                    
                    ### 💡 THE TOPPER'S TIP (MODEL ANSWER):
                    (Tell them exactly what keywords and diagram to add for 10/10)
                    
                    ---
                    **MODERATOR'S FINAL WARNING:** (Only if handwriting is bad)
                    """
                    
                    # Using Gemini Vision to 'read' the handwriting
                    response = model.generate_content([
                        {"mime_type": "image/jpeg", "data": img_data},
                        moderator_prompt
                    ])
                    
                    st.markdown(response.text)
                    
                    # 3. Viral Loop: Shareable Result [Your Viral Marketing Strategy]
                    st.divider()
                    st.caption("Proud of your score? Share it with your study group!")
                    share_text = f"I just got a {response.text.split('/10')[0][-1]}/10 from TopperGPT's Board Moderator! Can you beat me?"
                    st.download_button("📥 Download Evaluation Report", response.text, file_name="Evaluation_Report.txt")
                    
                except Exception as e:
                    st.error(f"Moderator is busy. Error: {e}")

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

    # --- TAB 5: FLASHCARDS (STRICT TOPIC LOCK) ---
    # --- TAB 5: FLASHCARDS (UNIVERSAL SYNC FIX) ---
    with tab5:
        st.subheader("🃏 Engineering Flashcard Generator")
        
        # 1. Direct File Uploader
        card_file = st.file_uploader(
            "Upload Notes (PDF/Image)", 
            type=["pdf", "png", "jpg"], 
            key="universal_card_sync"
        )
        
        # 2. Robust Extraction Logic
        if card_file:
            # File name check to prevent repeated processing
            if st.session_state.get("last_uploaded_card_file") != card_file.name:
                with st.spinner("Extracting text from your notes..."):
                    try:
                        if card_file.type == "application/pdf":
                            with pdfplumber.open(io.BytesIO(card_file.read())) as pdf:
                                # PDF ka poora text nikal kar state mein permanent save karna
                                st.session_state.flash_text_content = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                        else:
                            # Image/Handwritten notes extraction
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            res = model.generate_content([{"mime_type": card_file.type, "data": card_file.getvalue()}, "Extract all technical text."])
                            st.session_state.flash_text_content = res.text
                        
                        st.session_state.last_uploaded_card_file = card_file.name
                        st.toast(f"✅ Context Synced: {card_file.name}")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")

        # 3. Generation Button (Name changed as requested)
        if st.button("🚀 Generate Cards"):
            # Checking if content exists in state
            raw_data = st.session_state.get("flash_text_content", "")
            
            if raw_data:
                with st.spinner("AI is analyzing your specific topics..."):
                    # Strict context-based prompt
                    prompt = f"""
                    Context: {raw_data[:12000]}
                    
                    Instruction: Act as an Engineering Professor. 
                    Create exactly 10 'Question | Answer' flashcards based ONLY on the provided context.
                    If the context is about PCE, focus on Modulation/Signals. 
                    If it is about other subjects, focus on those specific core concepts.
                    Format: Question | Answer
                    """
                    
                    # High-speed processing via Groq
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.session_state.current_flashcards = res.choices[0].message.content.split("\n")
            else:
                #
                st.error("⚠️ Error: Pehle PDF upload karein taaki AI context read kar sake!")

        # 4. Display & Offline Save
        if st.session_state.get("current_flashcards"):
            st.markdown("---")
            # Creating a neat text file for download
            st.download_button(
                "📥 Download Flashcards (Text File)",
                data="\n".join(st.session_state.current_flashcards),
                file_name="TopperGPT_StudyCards.txt"
            )

            for i, line in enumerate(st.session_state.current_flashcards):
                if "|" in line:
                    q, a = line.split("|")
                    with st.expander(f"🔹 {q.strip()}"):
                        st.success(f"**Ans:** {a.strip()}")
    # --- TAB 6: UNIVERSITY VERIFIED PYQS (RESTORED) ---
    with tab6:
        st.subheader("❓ University Previous Year Questions")
        st.write("Get high-probability questions based on your University and Branch.")

        # 1. Selection Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            univ = st.selectbox("Select University:", 
                ["Mumbai University (MU)", "Pune University (SPPU)", "GTU", "VTU", "AKTU", "Other"])
        with col2:
            branch = st.selectbox("Select Branch:", 
                ["Computer/IT", "Mechanical", "Civil", "Electrical", "Electronics", "Chemical"])
        with col3:
            semester = st.selectbox("Semester:", [f"Sem {i}" for i in range(1, 9)])

        subj_name = st.text_input("Enter Subject Name (e.g., Engineering Mathematics, Thermodynamics):")

        # 2. Fetch Logic
        if st.button("🔍 Fetch Important PYQs"):
            if subj_name:
                with st.spinner(f"Searching {univ} database for {subj_name}..."):
                    # Prompt designed to act like a paper setter
                    prompt = f"""
                    Act as a University Paper Setter for {univ}. 
                    For the subject '{subj_name}' ({branch}, {semester}), provide:
                    1. 5 Most Repeated PYQs (Previous Year Questions).
                    2. 2 High-Probability 'Expected' questions for the upcoming exam.
                    3. Brief tips on how to score full marks in these specific questions.
                    Format: Clearly numbered with 'Year' if possible.
                    """
                    
                    try:
                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile", 
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.markdown("---")
                        st.markdown(f"### 📑 {subj_name} Question Bank")
                        st.write(res.choices[0].message.content)
                        
                        # Option to download these questions
                        st.download_button(
                            label="📥 Download Question Bank",
                            data=res.choices[0].message.content,
                            file_name=f"{subj_name}_PYQs.txt",
                            mime="text/plain"
                        )
                    except Exception as e:
                        st.error("Error fetching questions. Please check your connection.")
            else:
                st.warning("⚠️ Please enter a subject name first.")
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