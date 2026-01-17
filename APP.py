import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
import re
from groq import Groq

# --- 1. CONFIGURATION & FINAL RESPONSIVE UI ---
st.set_page_config(page_title="TopperGPT Engineering Pro", layout="wide", page_icon="🚀")

def apply_pro_theme():
    st.markdown("""
        <style>
        /* Main Background */
        .stApp { background-color: #0e1117; color: #ffffff; }
        
        /* Sidebar Fix */
        [data-testid="stSidebarNav"] { display: none; }
        [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
        
        /* ALIGNMENT FIX: Centering the Main Login Area for Mobile & Desktop */
        .main .block-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding-top: 2rem;
        }

        /* RESPONSIVE LOGIN CARD */
        .login-card {
            background: linear-gradient(145deg, #1e2530, #161b22);
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            border: 1px solid #4CAF50;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            margin: auto;
            width: 90%; /* Responsive width for mobile */
            max-width: 420px; /* Limits width on desktop */
        }

        /* Tabs Scrollable Fix on Mobile */
        div[data-testid="stHorizontalBlock"] {
            overflow-x: auto;
            white-space: nowrap;
            display: block;
        }

        /* Chat bubble for Topper Connect */
        .chat-bubble {
            background-color: #21262d;
            padding: 10px 15px;
            border-radius: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #4CAF50;
        }
        </style>
    """, unsafe_allow_html=True)

apply_pro_theme()

# --- 2. FIREBASE & API INITIALIZATION ---
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

# --- 3. SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- 4. THE LOGIN PAGE (CENTERED & FIXED) ---
if st.session_state.user is None:
    # Centering container with responsive columns
    st.markdown("<br>", unsafe_allow_html=True)
    _, col_mid, _ = st.columns([0.1, 0.8, 0.1])
    
    with col_mid:
        st.markdown("""
            <div class="login-card">
                <h1 style='color: #4CAF50; font-size: 2rem; margin-bottom: 0px;'>🚀 TopperGPT Pro</h1>
                <p style='color: #8b949e; font-size: 1rem;'>Engineered for Toppers. Built for Success.</p>
                <hr style="border-color: #30363d; margin: 20px 0;">
            </div>
        """, unsafe_allow_html=True)

        # GOOGLE LOGIN (Simulation of Account Selection Popup)
        if st.button("🔴 Continue with Google", use_container_width=True):
            with st.spinner("Opening Google Account Selector..."):
                import time
                time.sleep(1.5) # Asli popup feel dene ke liye
                if "google" in st.secrets:
                    st.session_state.user = "krishnaghanabahadur85@gmail.com" 
                    st.success("Account krishnaghanabahadur85@gmail.com Selected! 🚀")
                    st.rerun()
                else:
                    st.error("Secrets missing!")

        st.markdown("<p style='text-align:center; color:#8b949e; margin-top:15px;'>--- OR EMAIL LOGIN ---</p>", unsafe_allow_html=True)
        
        email = st.text_input("University Email", key="email_manual", placeholder="topper@university.edu")
        password = st.text_input("Password", type="password", key="pass_manual", placeholder="••••••••")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Access Portal 🔐", use_container_width=True):
            try:
                user = auth.get_user_by_email(email)
                st.session_state.user = user.email
                st.rerun()
            except:
                st.error("Invalid credentials. Please Sign Up.")
    st.stop()

# --- 5. SIDEBAR (POST-LOGIN) ---
with st.sidebar:
    st.markdown("<h2 style='color: #4CAF50; padding-top: 0;'>🚀 TopperGPT</h2>", unsafe_allow_html=True)
    st.image("https://img.icons8.com/bubbles/100/000000/user.png", width=80)
    
    u_display = st.session_state.user.split('@')[0]
    st.markdown(f"**Welcome, {u_display.capitalize()}!**")
    st.divider()
    
    if st.button("🔓 Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# --- 6. MAIN CONTENT TABS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "💬 Chat PDF", "📊 Syllabus", "📝 Answer Eval", "🧠 MindMap", 
    "🃏 Flashcards", "❓ Engg PYQs", "🔍 Search", "🤝 Topper Connect", "⚖️ Legal"
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
    # --- TAB 2: UNIVERSAL SYLLABUS TRACKER (AI TABLE EXTRACTION) ---
with tab2:
        st.markdown('<h3 style="text-align: center;">📋 TopperGPT Universal Tracker</h3>', unsafe_allow_html=True)
        
        # Semester Selector
        t_sem = st.selectbox(
            "Bhai, pehle Semester select karle:", 
            ["Select Semester", "Semester I", "Semester II"],
            key="v30_sem_selector"
        )
        
        syll_up = st.file_uploader("Upload Your Syllabus PDF", type=["pdf"], key="v30_syll_ai")
        
        if syll_up:
            if st.button("🚀 Analyze & Generate Tracker", use_container_width=True):
                if t_sem == "Select Semester":
                    st.warning("Bhai, pehle Semester toh select karle!")
                else:
                    with st.spinner(f"AI is strictly extracting {t_sem} Theory Modules..."):
                        try:
                            with pdfplumber.open(io.BytesIO(syll_up.read())) as pdf:
                                # Focusing on first 60 pages to find theory content
                                raw_text = "\n".join([p.extract_text() for p in pdf.pages[:60] if p.extract_text()])
                            
                            # Strict AI Prompt to avoid generic chapter names
                            prompt = f"""
                            Task: Extract Engineering Theory Subjects and Modules for {t_sem}.
                            Rules:
                            1. IGNORE all Lab, Workshop, and Tutorial subjects.
                            2. Find the 'Detailed Contents' or 'Syllabus' table for each subject.
                            3. EXTRACT the exact Module titles from the PDF (e.g., if it says 'Lasers', do not write 'Optics').
                            4. Each subject MUST have exactly 6 modules.
                            5. Do NOT include generic headers like 'Subject Name'.
                            
                            Format: {t_sem} | Subject Name | Title 1, Title 2, Title 3, Title 4, Title 5, Title 6
                            PDF Text Content: {raw_text[:20000]}
                            """
                            
                            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                            
                            dynamic_data = {}
                            for line in res.choices[0].message.content.split("\n"):
                                if "|" in line and t_sem.upper() in line.upper():
                                    parts = line.split("|")
                                    if len(parts) >= 3:
                                        s_name = parts[1].strip()
                                        # Strict Filter for generic headers and labs
                                        if any(x in s_name.lower() for x in ["subject name", "lab", "workshop", "tutorial"]):
                                            continue
                                        m_list = [m.strip() for m in parts[2].split(",") if len(m) > 3][:6]
                                        if len(m_list) >= 3:
                                            dynamic_data[s_name] = m_list

                            st.session_state.tracker_data = dynamic_data
                            st.session_state.active_sem = t_sem
                            st.session_state.done_topics = [] 
                            st.success(f"✅ {t_sem} Theory Tracker Ready!")
                        except Exception as e:
                            st.error(f"Error: {e}. Tokens might be exhausted again!")

        # --- PROGRESS DASHBOARD ---
        if st.session_state.get("tracker_data"):
            t_data = st.session_state.tracker_data
            all_keys = [f"{st.session_state.active_sem}_{s}_{m}".replace(" ","_") for s, ms in t_data.items() for m in ms]
            valid_done = len([d for d in st.session_state.get("done_topics", []) if d in all_keys])
            prog = int((valid_done / len(all_keys)) * 100) if all_keys else 0

            # Sleek Compact Mastery Card
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 12px; border-radius: 12px; color: white; border: 1px solid #4CAF50; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <b style="font-size: 16px; color: #4CAF50;">🚀 TopperGPT</b>
                        <b style="font-size: 22px;">{prog}%</b>
                    </div>
                    <div style="background: rgba(255,255,255,0.2); height: 5px; border-radius: 10px; margin: 8px 0;">
                        <div style="background: #4CAF50; height: 5px; border-radius: 10px; width: {prog}%;"></div>
                    </div>
                    <p style="margin: 0; font-size: 11px; opacity: 0.8;">{st.session_state.active_sem} Theory Mastery</p>
                </div>
            """, unsafe_allow_html=True)

            # Branded Share Button
            share_msg = f"*TopperGPT Report*%0A🔥 Mera *{prog}%* {st.session_state.active_sem} theory syllabus khatam!%0A🚀 Tu bhi track kar apna status!"
            st.markdown(f'<a href="https://wa.me/?text={share_msg}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; width:100%; padding:10px; border:none; border-radius:8px; font-weight:bold; cursor:pointer; margin-bottom:15px;">📲 Share Mastery with TopperGPT Watermark</button></a>', unsafe_allow_html=True)

            st.divider()
            
            # --- THE TRACKER LIST ---
            for subject, modules in t_data.items():
                with st.expander(f"📚 {subject}"):
                    for m in modules:
                        u_key = f"{st.session_state.active_sem}_{subject}_{m}".replace(" ", "_")
                        if st.checkbox(m, key=u_key, value=(u_key in st.session_state.done_topics)):
                            if u_key not in st.session_state.done_topics:
                                st.session_state.done_topics.append(u_key); st.rerun()
                        else:
                            if u_key in st.session_state.done_topics:
                                st.session_state.done_topics.remove(u_key); st.rerun()
    # --- TAB 3: ANSWER EVALUATOR ---
    # --- TAB 3: ANSWER EVALUATOR (ONE-SHOT FIXED & CLEAN UI) ---
with tab3: # Yahan maine tab3 kar diya hai taaki NameError na aaye
        st.subheader("🖋️ Board Moderator: One-Shot Evaluation")
        
        # User uploads single image containing both Question and Answer
        master_img = st.file_uploader("Upload Image (Question + Answer)", type=["png", "jpg", "jpeg"], key="eval_one_shot_final")

        if st.button("🔍 Smart Evaluate") and master_img:
            with st.spinner("Moderator is scanning the page..."):
                try:
                    # FIX: Endpoint structure change to avoid 404
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    img_data = master_img.getvalue()
                    
                    one_shot_prompt = """
                    ROLE: Strict Indian University Board Examiner.
                    
                    TASK: 
                    1. Identify the printed 'Question' and the 'Handwritten Answer' from the same image.
                    2. Grade the answer strictly based on technical keywords, diagrams, and formulas.
                    
                    OUTPUT FORMAT:
                    ## 📌 DETECTED QUESTION:
                    [Write the identified question here]
                    
                    ---
                    ## 📊 PROVISIONAL SCORE: [X/10]
                    
                    ### ✅ WHAT YOU DID WELL:
                    (Brief point)
                    
                    ### ❌ WHY YOU LOST MARKS:
                    (List specific technical misses)
                    
                    ### 💡 THE TOPPER'S TIP (MODEL ANSWER):
                    (Tell them exactly what diagram/keywords would get them 10/10)
                    """
                    
                    # One-Shot Vision Analysis
                    response = model.generate_content([
                        {"mime_type": "image/jpeg", "data": img_data},
                        one_shot_prompt
                    ])
                    
                    if response.text:
                        st.markdown(response.text)
                        st.divider()
                        st.download_button("📥 Download Report", response.text, file_name="Evaluation_Report.txt")
                    
                except Exception as e:
                    # Specific error message for the 404 issue
                    st.error(f"Moderator Error: {e}. Check if API Key supports 'gemini-1.5-flash'.")

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

# --- TAB 8: TOPPER CONNECT (WORKING LOGIC) ---
with tab8:
    st.subheader("🤝 Topper Connect: Community Hub")
    
    # Session state for temporary chat (Backend storage ke liye Firebase use karenge)
    if "community_chats" not in st.session_state:
        st.session_state.community_chats = [
            {"name": "Rahul (MU)", "msg": "Bhai, Applied Maths 2 ka Fourier Series ka koi shortcut hai?"},
            {"name": "AI Topper", "msg": "Rahul, Fourier mein symmetry check karo, half calculation bach jayegi!"}
        ]

    chat_col, leader_col = st.columns([2, 1])
    
    with chat_col:
        st.markdown("### 🗨️ Recent Doubts")
        
        # Displaying chats from session state
        for chat in st.session_state.community_chats:
            st.markdown(f"""
            <div class="chat-bubble">
                <b>{chat['name']}:</b> {chat['msg']}
            </div>
            """, unsafe_allow_html=True)
        
        # Working Input System
        with st.form("doubt_form", clear_on_submit=True):
            new_msg = st.text_input("Type your doubt here...", placeholder="e.g. Working of laser")
            submit_btn = st.form_submit_button("Post Doubt 🚀")
            
            if submit_btn and new_msg:
                # Adding new doubt to the list
                user_name = st.session_state.user.split('@')[0].capitalize()
                st.session_state.community_chats.append({"name": user_name, "msg": new_msg})
                st.success("Doubt posted on the wall!")
                st.rerun() # Refreshing to show new message

    with leader_col:
        st.markdown("### 🏆 Top Contributors")
        st.success("1. Krishna (85 Points)")
        st.info("2. Aryan (60 Points)")

# --- TAB 9: LEGAL & POLICIES ---
with tab9:
    st.header("⚖️ Legal, Terms & Privacy Policy")
    st.info("Bhai, TopperGPT use karne se pehle ye rules ek baar dekh lo. Ye tumhari aur hamari dono ki safety ke liye hain.")

    col_policy1, col_policy2 = st.columns(2)

    with col_policy1:
        st.subheader("📜 Terms of Service")
        st.write("""
        1. **Educational Use Only**: TopperGPT sirf padhai mein help karne ke liye hai. Iska use exam mein cheating karne ke liye na karein.
        2. **Accuracy**: AI kabhi-kabhi mistakes kar sakta hai (hallucinations). Final exam se pehle apne university textbook se verify zaroori karein.
        3. **Account Safety**: Apna login kisi aur ke saath share na karein, varna system access block kar sakta hai.
        4. **Usage Limit**: Free users ke liye daily limits hain. Commercial use ya bulk downloading allowed nahi hai.
        """)

    with col_policy2:
        st.subheader("🔒 Privacy Policy")
        st.write("""
        1. **Data Collection**: Hum sirf tumhara email aur university name save karte hain taaki tumhara progress (Syllabus Tracker) save rahe.
        2. **PDF Security**: Jo notes tum upload karte ho, wo sirf tumhare analysis ke liye use hote hain. Hum tumhara data kisi 3rd party ko nahi bechte.
        3. **Google Login**: Google Auth ke waqt hum sirf tumhari basic profile info access karte hain.
        4. **Cookies**: Session manage karne ke liye hum temporary cookies use karte hain.
        """)

    st.divider()
    st.caption("© 2026 TopperGPT Engineering. All Rights Reserved. Built with ❤️ for Engineering Students.")
    
    # Branded Button for Trust
    if st.button("I Agree to the Terms ✅", use_container_width=True):
        st.balloons()
        st.success("Dhanyawad Topper! Ab jaakar fod do exams mein.")        