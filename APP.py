import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
from groq import Groq

# --- 1. CONFIGURATION & UI ---
st.set_page_config(page_title="TopperGPT Pro", layout="wide", page_icon="🚀")

def apply_pro_theme():
    st.markdown("""
        <style>
        .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
        [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
        
        /* Wallet Card logic from Blueprint */
        .wallet-card {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #4CAF50;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .subscription-option {
            background: #1e2530;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #eab308;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

apply_pro_theme()

# --- 3. SESSION STATE ---
if "user_data" not in st.session_state:
    st.session_state.user_data = {"email": "verified.student@mu.edu", "credits": 5, "tier": "Free Tier"}

# --- 5. SIDEBAR (BLUEPRINT: SUBSCRIPTION & PAYMENT) ---
with st.sidebar:
    st.markdown("<h2 style='color: #4CAF50; margin-bottom:0;'>🎓 TopperGPT Pro</h2>", unsafe_allow_html=True)
    
    # Wallet Card
    st.markdown(f"""
        <div class="wallet-card">
            <p style="color: #eab308; font-weight: bold; margin: 0; font-size: 11px; letter-spacing: 1px;">CURRENT BALANCE</p>
            <p style="color: white; font-size: 28px; font-weight: 900; margin: 5px 0;">{st.session_state.user_data['credits']} 🔥</p>
            <p style="color: #8b949e; font-size: 11px; margin: 0;">Plan: {st.session_state.user_data['tier']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("💳 Choose Your Plan")
    
    # ASALI SELECTION LOGIC (Ab student choose kar payega)
    plan_choice = st.radio(
        "Available Packs:",
        ["Jugaad Pack (50 Credits @ ₹99)", "Monthly Pro (Unlimited @ ₹149)"],
        index=0,
        key="plan_selector"
    )
    
    # YOUR ACTIVE PUBLIC LINK
    # Note: Ek hi link par student apni pasand ka amount pay kar sakega
    payment_link = "https://rzp.io/rzp/AWiyLxEi" 
    
    # Unlock Button logic
    st.markdown(f"""
        <div style="margin-top: 20px;">
            <a href="{payment_link}" target="_blank" style="text-decoration: none;">
                <div style="
                    width: 100%;
                    background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%);
                    color: black;
                    text-align: center;
                    padding: 15px 0;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 16px;
                    cursor: pointer;
                    box-shadow: 0 4px 15px rgba(234, 179, 8, 0.4);
                ">
                    Unlock {plan_choice.split(' (')[0]} 🚀
                </div>
            </a>
            <p style="text-align: center; font-size: 10px; color: #8b949e; margin-top: 10px;">
                Securely opens Razorpay Portal in New Tab
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()
    if st.button("🔓 Secure Logout", use_container_width=True):
        st.session_state.user_data = None
        st.rerun()

# --- 6. MAIN CONTENT (TABS) ---
st.title("🚀 Engineering Study Studio")
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "💬 Chat PDF", "📊 Syllabus", "📝 Answer Eval", "🧠 MindMap", 
    "🃏 Flashcards", "❓ Engg PYQs", "🔍 Search", "🤝 Topper Connect", "⚖️ Legal"
])

# --- TAB LOGIC STARTS HERE (Same as your original code) ---
# ... rest of your tab logic starts here ...
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
    
    # Selection Mode
    m_mode = st.radio("Source Selection:", ["Enter Topic", "Use File Data"], horizontal=True, key="m_src_final")
    
    # Input Logic
    if m_mode == "Enter Topic":
        m_input = st.text_input("Engineering Concept (e.g. Back EMF):", key="m_topic_final")
    else:
        m_input = st.session_state.get("pdf_content", "")[:3000]
        if not m_input: 
            st.warning("⚠️ Pehle Tab 1 mein notes upload karein!")

    if st.button("Build Map", key="m_btn_final") and m_input:
        with st.spinner("AI is drawing the architecture..."):
            # Strict Prompt to ensure clean Mermaid code
            prompt = f"""
            Explain the engineering concept '{m_input}' in 5 clear lines. 
            Then, provide ONLY a Mermaid.js 'graph TD' flowchart.
            
            Format your response exactly like this:
            SUMMARY: [Your 5 lines here]
            MERMAID:
            graph TD
            A[Start] --> B[Process]
            
            Rules:
            - NO extra text, NO explanations after the code.
            - Use ONLY square brackets [] for nodes.
            """
            
            try:
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile", 
                    messages=[{"role": "user", "content": prompt}]
                )
                full_out = res.choices[0].message.content

                # 1. Extract Summary
                if "SUMMARY:" in full_out:
                    # MERMAID keyword tak ka text uthayenge
                    sum_text = full_out.split("SUMMARY:")[1].split("MERMAID:")[0].strip()
                    st.info(f"**Technical Summary:**\n\n{sum_text}")

                # 2. Extract & Force-Fix Mermaid Code
                if "graph TD" in full_out:
                    # AI ke kachre se sirf 'graph TD' wala part nikalna
                    match = re.search(r"graph\s+TD[\s\S]*", full_out)
                    if match:
                        # Character cleaning for Mermaid v10 compatibility
                        clean_code = match.group(0).replace("```mermaid", "").replace("```", "").strip()
                        
                        # AI aksar () use karta hai jo crash karta hai, hum use [] mein badal denge
                        clean_code = clean_code.replace("(", "[").replace(")", "]")
                        
                        # Sirf pehla logical block uthana
                        clean_code = clean_code.split("\n\n")[0]
                        
                        st.markdown("---")
                        st.markdown("### 📊 Architecture Flowchart")
                        
                        # Rendering the diagram
                        try:
                            st_mermaid(clean_code, height=450)
                        except Exception as render_err:
                            st.error("Visual rendering failed. Showing code instead:")
                            st.code(clean_code, language="mermaid")
                    else:
                        st.error("AI couldn't generate a proper diagram. Try again with a simpler topic.")
                
            except Exception as e:
                st.error(f"System Error: {e}")

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
    st.write("Instant 360° Analysis: Detailed Report, Architecture Flowchart, & 15+ PYQs.")
    
    query = st.text_input("Enter Engineering Topic (e.g. Transformer, BJT):", key="search_final_absolute_v1")
    
    if st.button("Deep Research", key="btn_absolute_v1") and query:
        with st.spinner(f"Analyzing '{query}' for University Exams..."):
            # Strongest prompt to ensure professional logic and 15+ PYQs
            prompt = f"""
            Act as an Engineering Professor. Provide a comprehensive report for: '{query}'.
            Use these markers exactly:
            [1_DEF] for a technical definition.
            [2_KEY] for 7-10 technical keywords.
            [3_CXP] for detailed technical breakdown/working.
            [4_SMP] for a simple 2-line explanation.
            [5_DOT] for ONLY Graphviz DOT code (digraph G {{...}}) showing its architecture.
            [6_PYQ] for at least 15 REAL university exam questions (2m, 5m, 10m mixed).
            """
            
            try:
                res = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile", 
                    messages=[{"role": "user", "content": prompt}]
                )
                out = res.choices[0].message.content

                def get_sec(m1, m2=None):
                    try:
                        parts = out.split(m1)
                        if len(parts) < 2: return "Data missing."
                        content = parts[1]
                        if m2 and m2 in content: content = content.split(m2)[0]
                        return content.strip().replace("```dot", "").replace("```", "")
                    except: return "Section error."

                # --- 1. DISPLAY ALL TEXT SECTIONS ---
                st.markdown(f"## 📘 Technical Report: {query}")
                st.info(f"**1. Standard Definition:**\n\n{get_sec('[1_DEF]', '[2_KEY]')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**2. Technical Keywords:**\n\n{get_sec('[2_KEY]', '[3_CXP]')}")
                with col2:
                    st.success(f"**4. Simple Explanation:**\n\n{get_sec('[4_SMP]', '[5_DOT]')}")
                
                st.warning(f"**3. Technical Breakdown (Working):**\n\n{get_sec('[3_CXP]', '[4_SMP]')}")

                # --- 2. THE "NO-FAIL" FLOWCHART (GRAPHVIZ) ---
                st.markdown("---")
                st.markdown("### 📊 5. Architecture Flowchart")
                dot_code = get_sec('[5_DOT]', '[6_PYQ]')
                
                if "digraph" in dot_code:
                    try:
                        # Graphviz seedha server se image render karta hai, blank nahi hoga
                        st.graphviz_chart(dot_code, use_container_width=True)
                    except:
                        st.code(dot_code, language="dot")
                        st.error("Flowchart rendering issues. Review logic in breakdown section.")
                else:
                    st.warning("Diagram currently unavailable for this complex topic.")

                # --- 3. MEGA PYQ WALL (15+ QUESTIONS) ---
                st.markdown("---")
                st.markdown("### ❓ 6. Expected Exam Questions (15+ Comprehensive PYQs)")
                st.write(get_sec('[6_PYQ]'))

            except Exception as e:
                st.error(f"System Busy. Error: {e}")
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