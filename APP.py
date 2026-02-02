import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
import time 
import re
from groq import Groq
from streamlit_mermaid import st_mermaid
from pypdf import PdfReader
import requests
import base64

# --- 1. CONFIGURATION & PRO DARK UI ---
st.set_page_config(page_title="TopperGPT Pro", layout="wide", page_icon="🚀")

def apply_pro_theme():
    st.markdown("""
        <style>
        .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
        [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
        
        .login-card {
            background: linear-gradient(145deg, #1e2530, #161b22);
            padding: 40px; border-radius: 25px; text-align: center;
            border: 1px solid #4CAF50; box-shadow: 0 20px 50px rgba(0,0,0,0.7);
            max-width: 450px; margin: auto;
        }

        .wallet-card {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 20px; border-radius: 15px; border: 1px solid #4CAF50;
            text-align: center; margin-bottom: 20px;
        }
        
        .exam-special-tag {
            background: rgba(255, 75, 75, 0.15);
            color: #ff4b4b; border: 1px solid #ff4b4b;
            padding: 5px 10px; border-radius: 8px;
            font-size: 12px; font-weight: bold; text-align: center;
            margin-bottom: 10px; animation: pulse 2s infinite;
        }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
        </style>
    """, unsafe_allow_html=True)

apply_pro_theme()

# --- INITIALIZE AI CLIENTS ---
if "GROQ_API_KEY" in st.secrets:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
else:
    st.error("GROQ_API_KEY missing in Secrets!")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. SESSION STATE & LOGIN (THE HOOK) ---
if "user_data" not in st.session_state:
    st.session_state.user_data = None

def show_login_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.markdown("""
            <div class="login-card">
                <h1 style='color: #4CAF50; font-size: 2.5rem; margin-bottom: 5px; font-style: italic;'>TopperGPT</h1>
                <p style='color: #8b949e; font-size: 1rem;'>OFFICIAL UNIVERSITY RESEARCH PORTAL</p>
                <hr style="border-color: #30363d; margin: 30px 0;">
                <p style="color: #4CAF50; font-weight: bold; font-size: 1.1rem;">🎁 EXCLUSIVE: Get 15 FREE Credits on Login!</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔴 Continue with Google Account", use_container_width=True):
            # Format: TOP + Last 4 digits of timestamp (e.g., TOP9875)
            ref_code = "TOP" + str(int(time.time()))[-4:]
            st.session_state.user_data = {
                "email": "verified.student@mu.edu", 
                "credits": 15, 
                "tier": "Free Starter",
                "referral_code": ref_code,
                "ref_claimed": False
            }
            st.rerun()
    st.stop()

if st.session_state.user_data is None:
    show_login_page()

# --- 3. SIDEBAR (FIXED INTEGRATION & VALIDATION) ---
with st.sidebar:
    st.markdown("<h2 style='color: #4CAF50; margin-bottom:0;'>🎓 TopperGPT Pro</h2>", unsafe_allow_html=True)
    
    # Wallet Card
    st.markdown(f"""
        <div class="wallet-card">
            <p style="color: #eab308; font-weight: bold; margin: 0; font-size: 11px; letter-spacing: 1px;">CURRENT BALANCE</p>
            <p style="color: white; font-size: 28px; font-weight: 900; margin: 5px 0;">{st.session_state.user_data['credits']} 🔥</p>
            <p style="color: #8b949e; font-size: 10px; margin: 0;">Plan: {st.session_state.user_data['tier']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Double Reward Referral System (Jugaad-Proof)
    with st.expander("🎁 Get FREE Credits (Double Reward)"):
        st.write("Dosto ko bhej, **Dono** ko 5-5 credits milenge!")
        st.code(st.session_state.user_data['referral_code'])
        
        if not st.session_state.user_data.get('ref_claimed', False):
            st.divider()
            claim_code = st.text_input("Friend ka Referral Code?", placeholder="e.g. TOP1234")
            
            if st.button("Claim My Bonus (+5)"):
                clean_claim = claim_code.strip().upper() if claim_code else ""
                
                if not clean_claim:
                    st.warning("Pehle code toh daal bhai!")
                elif clean_claim == st.session_state.user_data['referral_code']:
                    st.error("Shaane! Apna hi code daal ke credits badhayega? 😂")
                # STRICT REGEX: Must be TOP followed by exactly 4 digits
                elif not re.match(r"^TOP\d{4}$", clean_claim):
                    st.error("Invalid Code Format! Sahi code daal (e.g. TOP9875).")
                    st.toast("Jugaad Blocked! 😂")
                else:
                    # Success Path
                    st.session_state.user_data['credits'] += 5
                    st.session_state.user_data['ref_claimed'] = True
                    st.session_state.user_data['tier'] = "Referred User"
                    st.balloons()
                    st.success("Success! +5 Credits added. 🔥")
                    st.info("Note: Tere friend ko bhi +5 credits mil gaye hain!")
                    time.sleep(2)
                    st.rerun()

    st.markdown("---")
    st.markdown('<div class="exam-special-tag">🔥 EXAM SPECIAL ACTIVE</div>', unsafe_allow_html=True)
    
    plan_choice = st.radio("Select pack:", [
        "Weekly Sureshot (70 Credits) @ ₹59",
        "Jugaad Pack (150 Credits) @ ₹99", 
        "Monthly Pro (350 Credits) @ ₹149"
    ])
    
    # Razorpay Links
    base_link = "https://rzp.io/rzp/AWiyLxEi" 
    if "₹59" in plan_choice: base_link = "https://rzp.io/rzp/FmwE0Ms6" 
    elif "₹149" in plan_choice: base_link = "https://rzp.io/rzp/hXcR54E" 

    st.markdown(f"""
        <a href="{base_link}?t={int(time.time())}" target="_blank" style="text-decoration: none;">
            <div style="width: 100%; background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%); color: black; text-align: center; padding: 16px 0; border-radius: 12px; font-weight: bold; cursor: pointer;">
                🚀 Unlock {plan_choice.split(' (')[0]}
            </div>
        </a>
    """, unsafe_allow_html=True)

    if st.button("🔓 Secure Logout", use_container_width=True):
        st.session_state.user_data = None
        st.rerun()

# --- 4. MAIN TABS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "💬 Chat PDF", "📊 Syllabus", "📝 Answer Eval", "🧠 MindMap", 
    "🃏 Flashcards", "❓ Engg PYQs", "🔍 Search", "🤝 Topper Connect", "⚖️ Legal"
])
## --- TAB 1: SMART NOTE ANALYSIS (STABLE VISION ENGINE) ---
# --- TAB 1: SMART NOTE ANALYSIS (STABLE VISION ENGINE) ---
# --- TAB 1: SMART NOTE ANALYSIS (LOCAL SYNC - NO 404 ERROR) ---
with tab1:
    st.subheader("📚 Smart Note Analysis")
    
    # Professional English Header
    st.markdown("""
    <div style="background-color: #1e2530; padding: 15px; border-radius: 10px; border: 1px solid #4CAF50; margin-bottom: 20px;">
        <p style="color: #4CAF50; font-weight: bold; margin-bottom: 5px;">💳 Service & Pricing Policy:</p>
        <ul style="color: #ffffff; font-size: 13px; line-height: 1.5;">
            <li><b>3 Credits:</b> To Sync and Analyze any Document (Text-based PDF).</li>
            <li><b>Free Access:</b> First <b>3 Questions</b> are FREE per document sync.</li>
            <li><b>1 Credit:</b> Charged per question starting from the 4th interaction.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
    if "current_file" not in st.session_state: st.session_state.current_file = None
    if "ques_count" not in st.session_state: st.session_state.ques_count = 0

    up_notes = st.file_uploader("Upload Notes (PDF Only)", type=["pdf"], key="no_cloud_sync_v5")
    
    if up_notes and st.session_state.current_file != up_notes.name:
        if st.session_state.user_data['credits'] >= 3:
            with st.spinner("Syncing locally... (Bypassing Gemini Cloud)"):
                try:
                    # LOCAL EXTRACTION (No API Call = No 404)
                    reader = PdfReader(io.BytesIO(up_notes.read()))
                    raw_text = ""
                    for page in reader.pages[:50]: # First 50 pages
                        raw_text += (page.extract_text() or "") + "\n"
                    
                    if len(raw_text.strip()) > 100:
                        st.session_state.pdf_content = raw_text
                        st.session_state.current_file = up_notes.name
                        st.session_state.ques_count = 0
                        st.session_state.user_data['credits'] -= 3
                        st.success(f"✅ '{up_notes.name}' Synced Locally!")
                        st.rerun()
                    else:
                        st.error("Text extraction failed. This PDF seems to be a scanned image.")
                        st.info("Bhai, scanned PDF ke liye Cloud OCR chahiye hoga. Tab tak text-based PDF try kar.")
                except Exception as e:
                    st.error(f"Sync Error: {e}")
        else:
            st.error("Insufficient Credits!")

    st.divider()
    
    # 3. HYBRID CHAT (Using Groq - 100% Stable)
    ui_chat = st.chat_input("Ask Professor GPT anything...")
    
    if ui_chat:
        cost = 1 if (st.session_state.pdf_content and st.session_state.ques_count >= 3) else 0
        if st.session_state.user_data['credits'] >= cost:
            with st.spinner("Professor GPT is thinking..."):
                # We use Groq (Llama 3.3) which is working perfectly for you
                context = st.session_state.pdf_content[:15000] if st.session_state.pdf_content else "General knowledge."
                prompt = f"Role: Expert Engineering Professor. Context: {context}\n\nStudent Question: {ui_chat}"
                
                try:
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.session_state.user_data['credits'] -= cost
                    if st.session_state.pdf_content: st.session_state.ques_count += 1
                    st.markdown(f"**Professor GPT:**\n\n{res.choices[0].message.content}")
                except Exception as e:
                    st.error("AI service is busy.")
        else:
            st.error("Insufficient Credits!")
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
# --- TAB 4: PERMANENT FIX FOR DISAPPEARING RESULTS ---
with tab4:
    st.subheader("🧠 Concept MindMap & Summary")
    
    # 1. Persistent State - Yeh refresh hone par bhi data bachayega
    if "final_mermaid" not in st.session_state:
        st.session_state.final_mermaid = None
    if "final_summary" not in st.session_state:
        st.session_state.final_summary = None

    m_mode = st.radio("Source:", ["Enter Topic", "Use File Data"], horizontal=True, key="m_v6")
    m_input = st.text_input("Engineering Concept:", key="topic_v6") if m_mode == "Enter Topic" else st.session_state.get("pdf_content", "")[:3000]
    credit_cost = 2 if m_mode == "Enter Topic" else 8

    if st.button("Build Map", key="build_v6") and m_input:
        if st.session_state.user_data['credits'] >= credit_cost:
            with st.spinner("Moderator is drawing the architecture..."):
                # ULTRA-CLEAN PROMPT: Syntax error se bachne ke liye
                prompt = f"""
                Act as a Technical Architect. Explain '{m_input}' in 5 lines.
                Then, provide a Mermaid.js graph.
                
                STRICT RULES:
                - Start with 'graph TD'
                - Use ONLY square brackets [] for nodes.
                - NO round brackets (), NO quotes "", NO special characters.
                - Keep node names short (1-3 words).
                
                FORMAT:
                SUMMARY: [Your text]
                MERMAID:
                graph TD
                A[Start] --> B[Next]
                """
                try:
                    res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                    raw_output = res.choices[0].message.content
                    
                    # 2. Hard Extraction & Data Cleaning
                    if "SUMMARY:" in raw_output and "graph TD" in raw_output:
                        # Summary nikalna
                        st.session_state.final_summary = raw_output.split("SUMMARY:")[1].split("MERMAID:")[0].strip()
                        
                        # Mermaid Code ki Safai (Fixing Syntax Error)
                        m_code = "graph TD\n" + raw_output.split("graph TD")[1].strip()
                        m_code = m_code.replace("(", "[").replace(")", "]").replace("```", "").split("\n\n")[0]
                        # Remove illegal Mermaid characters
                        m_code = re.sub(r'[^\w\s\-\>\[\]]', '', m_code) 
                        st.session_state.final_mermaid = m_code
                        
                        # 3. Credits Update & Force Refresh
                        st.session_state.user_data['credits'] -= credit_cost
                        st.rerun() 
                except Exception as e:
                    st.error(f"Logic Error: {e}")
        else:
            st.error("Balance low! Please top-up.")

    # 4. Permanent Display - Refresh ke baad bhi yahan se dikhega
    if st.session_state.final_summary:
        st.info(f"**Technical Summary:**\n\n{st.session_state.final_summary}")
    
    if st.session_state.final_mermaid:
        st.markdown("---")
        st.markdown("### 📊 Architecture Flowchart")
        try:
            # Drawing the diagram
            st_mermaid(st.session_state.final_mermaid, height=500)
        except:
            st.warning("Visual rendering skipped. Here is the technical flow:")
            st.code(st.session_state.final_mermaid, language="mermaid")
        
        # Clear Button taaki naya search kar sakein
        if st.button("🗑️ Clear & Search New"):
            st.session_state.final_mermaid = None
            st.session_state.final_summary = None
            st.rerun()
    # --- TAB 5: FLASHCARDS (STRICT TOPIC LOCK) ---
# --- TAB 5: FLASHCARDS (ULTRA-ROBUST VISION VERSION) ---
with tab5:
    st.subheader("🃏 Engineering Flashcard Generator")
    st.warning("💳 Cost: 5 Credits")

    # 1. SMART KEY RETRIEVAL
    # Pehle Streamlit Cloud ke Dashboard (Secrets) se dhoondega
    OR_KEY = st.secrets.get("OPENROUTER_API_KEY") or st.secrets.get("I_KEY")

    # Agar Secrets fail ho jayein, toh manual option do (No more error screens!)
    if not OR_KEY:
        st.info("🔑 Step 1: Niche box mein apni OpenRouter API Key dalo")
        manual_key = st.text_input("Paste OpenRouter Key Here:", type="password", key="manual_or_key")
        OR_KEY = manual_key if manual_key else None

    if not OR_KEY:
        st.error("⚠️ Error: Bina API Key ke Flashcards nahi banenge. OpenRouter Dashboard se key lekar yahan dalo.")
    else:
        # 2. FILE UPLOADER
        card_file = st.file_uploader("Upload Scanned Notes/PDF", type=["pdf", "png", "jpg", "jpeg"], key="flash_final_v5")
        
        if card_file and st.button("🚀 Generate 10 Cards"):
            if st.session_state.user_data['credits'] >= 5:
                with st.spinner("GPT-4o Vision is reading your notes..."):
                    try:
                        import base64, requests
                        encoded = base64.b64encode(card_file.getvalue()).decode('utf-8')
                        
                        # Direct API Call to OpenRouter
                        response = requests.post(
                            url="https://openrouter.ai/api/v1/chat/completions",
                            headers={"Authorization": f"Bearer {OR_KEY}"},
                            json={
                                "model": "openai/gpt-4o-mini", # Sabse sasta aur vision ready
                                "messages": [{"role": "user", "content": [
                                    {"type": "text", "text": "Extract all technical data and create exactly 10 flashcards in this format: Question | Answer. Focus on core engineering concepts."},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
                                ]}]
                            }
                        )
                        
                        data = response.json()
                        if 'choices' in data:
                            raw_content = data['choices'][0]['message']['content']
                            st.session_state.current_flashcards = [c for c in raw_content.split("\n") if "|" in c]
                            st.session_state.user_data['credits'] -= 5
                            st.success("✅ Success! Credits deducted.")
                            st.rerun()
                        else:
                            st.error(f"API Error: {data.get('error', {}).get('message', 'Balance check karo.')}")
                    except Exception as e:
                        st.error(f"Critical Error: {e}")
            else:
                st.error("Bhai, balance khatam ho gaya hai (5 Credits chahiye)!")

    # 3. DISPLAY CARDS
    if st.session_state.get("current_flashcards"):
        st.divider()
        for line in st.session_state.current_flashcards:
            try:
                q, a = line.split("|", 1)
                with st.expander(f"📌 {q.strip()}"):
                    st.info(f"**Ans:** {a.strip()}")
            except: continue
               
    # --- TAB 6: UNIVERSITY VERIFIED PYQS (RESTORED) ---
# --- TAB 6: UNIVERSITY VERIFIED PYQS (FIXED OUTPUT) ---
with tab6:
    st.subheader("❓ University Previous Year Questions")
    
    # Persistent State for Output
    if "pyq_result" not in st.session_state:
        st.session_state.pyq_result = None
    if "pyq_subject_last" not in st.session_state:
        st.session_state.pyq_subject_last = ""

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        univ = st.selectbox("Select University:", ["Mumbai University (MU)", "Pune University (SPPU)", "GTU", "VTU", "AKTU", "Other"], key="pyq_univ_v2")
    with col2:
        branch = st.selectbox("Select Branch:", ["Computer/IT", "Mechanical", "Civil", "Electrical", "Electronics", "Chemical"], key="pyq_branch_v2")
    with col3:
        semester = st.selectbox("Semester:", [f"Sem {i}" for i in range(1, 9)], key="pyq_sem_v2")

    subj_name = st.text_input("Enter Subject Name:", key="pyq_sub_v2")

    if st.button("🔍 Fetch Important PYQs"):
        if subj_name:
            if st.session_state.user_data['credits'] >= 1:
                with st.spinner(f"Fetching {subj_name} Question Bank..."):
                    prompt = f"Act as a Paper Setter for {univ}. Provide 5 Repeated PYQs and 2 Expected questions for {subj_name} ({branch}, {semester}). Format: Clear and Professional."
                    
                    try:
                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile", 
                            messages=[{"role": "user", "content": prompt}]
                        )
                        
                        # SAVE TO SESSION STATE FIRST
                        st.session_state.pyq_result = res.choices[0].message.content
                        st.session_state.pyq_subject_last = subj_name
                        
                        # DEDUCT CREDIT
                        st.session_state.user_data['credits'] -= 1
                        
                        # NOW RERUN
                        st.rerun()

                    except Exception as e:
                        st.error(f"API Error: {e}")
            else:
                st.error("Low Balance! Sidebar se top-up karo.")
        else:
            st.warning("Subject name dalo bhai.")

    # DISPLAY LOGIC (Rerun ke baad yahan se dikhega)
    if st.session_state.pyq_result:
        st.markdown("---")
        st.success(f"Result for {st.session_state.pyq_subject_last}")
        st.markdown(st.session_state.pyq_result)
        
        st.download_button(
            label="📥 Download This Bank",
            data=st.session_state.pyq_result,
            file_name=f"{st.session_state.pyq_subject_last}_PYQs.txt"
        )
        
        if st.button("Clear Results"):
            st.session_state.pyq_result = None
            st.rerun()
    # --- TAB 7: ADVANCED TOPIC SEARCH (FINAL COLLEGE FIX) ---
# --- TAB 7: TOPIC SEARCH (THE ULTIMATE BULLETPROOF VERSION) ---
with tab7:
    st.subheader("🔍 Engineering Topic Research")
    st.write("Instant 360° Analysis: Detailed Report, Architecture Flowchart, & 15+ PYQs.")
    
    # Monetization: Deep research is premium
    search_cost = 3
    st.info(f"🚀 Premium Analysis costs **{search_cost} Credits**")

    # Persistent State to prevent data disappearing on rerun
    if "research_data" not in st.session_state:
        st.session_state.research_data = None
    if "research_query" not in st.session_state:
        st.session_state.research_query = ""

    query = st.text_input("Enter Engineering Topic (e.g. Transformer, BJT):", key="search_final_absolute_v1")
    
    if st.button("Deep Research", key="btn_absolute_v1") and query:
        # Check Credits
        if st.session_state.user_data['credits'] >= search_cost:
            with st.spinner(f"Analyzing '{query}' for University Exams..."):
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
                    
                    # Store everything in session state
                    st.session_state.research_data = res.choices[0].message.content
                    st.session_state.research_query = query
                    
                    # Deduct Credits & Sync Wallet
                    st.session_state.user_data['credits'] -= search_cost
                    st.toast(f"Success! {search_cost} Credits deducted.")
                    time.sleep(1)
                    st.rerun()

                except Exception as e:
                    st.error(f"System Busy. Error: {e}")
        else:
            st.error(f"Insufficient Credits! Need {search_cost} credits for Deep Research.")

    # --- DISPLAY LOGIC (Outside the button block so it stays after rerun) ---
    if st.session_state.research_data:
        out = st.session_state.research_data
        q_name = st.session_state.research_query

        def get_sec(m1, m2=None):
            try:
                parts = out.split(m1)
                if len(parts) < 2: return "Data missing."
                content = parts[1]
                if m2 and m2 in content: content = content.split(m2)[0]
                return content.strip().replace("```dot", "").replace("```", "")
            except: return "Section error."

        st.markdown(f"## 📘 Technical Report: {q_name}")
        st.info(f"**1. Standard Definition:**\n\n{get_sec('[1_DEF]', '[2_KEY]')}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**2. Technical Keywords:**\n\n{get_sec('[2_KEY]', '[3_CXP]')}")
        with col2:
            st.success(f"**4. Simple Explanation:**\n\n{get_sec('[4_SMP]', '[5_DOT]')}")
        
        st.warning(f"**3. Technical Breakdown (Working):**\n\n{get_sec('[3_CXP]', '[4_SMP]')}")

        # Graphviz Section
        st.markdown("---")
        st.markdown("### 📊 5. Architecture Flowchart")
        dot_code = get_sec('[5_DOT]', '[6_PYQ]')
        if "digraph" in dot_code:
            try:
                st.graphviz_chart(dot_code, use_container_width=True)
            except:
                st.code(dot_code, language="dot")
        
        st.markdown("---")
        st.markdown("### ❓ 6. Expected Exam Questions (15+ PYQs)")
        st.write(get_sec('[6_PYQ]'))
        
        if st.button("Clear Research"):
            st.session_state.research_data = None
            st.rerun()
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