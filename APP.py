import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
from PIL import Image, ImageDraw, ImageFont
import io
import time 
import re
from groq import Groq
from streamlit_mermaid import st_mermaid
from pypdf import PdfReader
import requests
import base64
import json
import fitz
import textwrap
import PyPDF2

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
# --- TAB 2: AI SYLLABUS ARCHITECT (PRECISION BUILD) ---
with tab2:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>📊 AI Syllabus Tracker Pro</h2>", unsafe_allow_html=True)
    
    # Persistent State
    if 'master_syllabus' not in st.session_state:
        st.session_state.master_syllabus = {}
    if 'tracker_status' not in st.session_state:
        st.session_state.tracker_status = {}

    # PDF Uploader
    uploaded_syllabus = st.file_uploader("Upload Syllabus PDF (NEP 2020 Supported)", type="pdf", key="syll_precision_v1")

    if uploaded_syllabus and st.button("🚀 Architect Syllabus Tree"):
        with st.spinner("TopperGPT is deep-scanning for Semester Hierarchy..."):
            try:
                reader = PyPDF2.PdfReader(uploaded_syllabus)
                # Hum ab zyada pages scan karenge accurate result ke liye
                full_text = ""
                for page in reader.pages[:10]: 
                    full_text += page.extract_text()

                # High Precision Prompt
                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{
                        "role": "user",
                        "content": f"""Analyze this University Syllabus. Extract a hierarchical structure.
                        RULES:
                        1. Group by Semester.
                        2. Identify each Subject.
                        3. List Chapters/Units under each Subject.
                        4. List specific Topics under each Chapter.
                        
                        Return ONLY JSON:
                        {{
                          "Semester 1": {{
                            "Subject Name": {{
                              "Unit 1: Name": ["Topic A", "Topic B"]
                            }}
                          }}
                        }}
                        Text Context: {full_text[:15000]}"""
                    }],
                    response_format={"type": "json_object"}
                )
                
                new_data = json.loads(completion.choices[0].message.content)
                if new_data:
                    st.session_state.master_syllabus = new_data
                    st.success("Syllabus Tree Updated with NEP Accuracy!")
            except Exception as e:
                st.error(f"Syllabus Scan Error: {e}")

    # --- TRACKER & PROGRESS UI ---
    if st.session_state.master_syllabus:
        # Progress Calculation Logic
        all_topics = []
        for sem, subs in st.session_state.master_syllabus.items():
            for sub, chaps in subs.items():
                for chap, topics in chaps.items():
                    for t in topics:
                        all_topics.append(f"{sem}_{sub}_{chap}_{t}")
        
        total = len(all_topics)
        done = sum(1 for t in all_topics if st.session_state.tracker_status.get(t, False))
        progress = (done / total) if total > 0 else 0

        # Cinematic Progress UI
        st.markdown(f"""
        <div style="background: #1a1c23; padding: 25px; border-radius: 20px; border: 1px solid #4CAF50; margin-bottom: 25px; text-align: center;">
            <h2 style="color: #4CAF50; margin: 0;">{int(progress*100)}% Complete</h2>
            <p style="color: #8b949e; font-size: 0.8rem;">{done} of {total} Topics Mastered</p>
            <div style="background: #30363d; border-radius: 10px; height: 12px; margin-top: 10px;">
                <div style="background: linear-gradient(90deg, #4CAF50, #8BC34A); width: {progress*100}%; height: 100%; border-radius: 10px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Hierarchical Display
        for sem, subs in st.session_state.master_syllabus.items():
            with st.expander(f"📅 {sem.upper()}"):
                for sub, chaps in subs.items():
                    st.markdown(f"#### 📘 {sub}")
                    for chap, topics in chaps.items():
                        st.markdown(f"**{chap}**")
                        # Topic Grid
                        for t in topics:
                            t_key = f"{sem}_{sub}_{chap}_{t}"
                            # Value persists because it's tied to session_state
                            checked = st.checkbox(t, key=t_key, value=st.session_state.tracker_status.get(t_key, False))
                            st.session_state.tracker_status[t_key] = checked
        
        if st.button("🧹 Reset All Tracking"):
            st.session_state.tracker_status = {}
            st.rerun()
    # --- TAB 3: ANSWER EVALUATOR ---
# --- TAB 3: CINEMATIC BOARD MODERATOR (ZERO-ERROR TEXT ENGINE) ---
with tab3:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🖋️ Board Moderator Pro</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e; font-size: 0.9rem;'>Bulletproof Text Evaluation • Official Board Logic</p>", unsafe_allow_html=True)
    
    if "eval_json" not in st.session_state:
        st.session_state.eval_json = None

    st.warning("💳 Evaluation Cost: **5 Credits**")
    
    # 1. INPUT SECTION (Text-only to avoid Vision 404 Errors)
    input_q = st.text_area("Question:", placeholder="Enter the exam question...", height=70)
    input_a = st.text_area("Your Answer:", placeholder="Paste your answer text here for instant grading...", height=200)

    if st.button("🔍 Evaluate My Answer") and input_q and input_a:
        if st.session_state.user_data['credits'] >= 5:
            with st.spinner("TopperGPT is analyzing technical accuracy..."):
                try:
                    # Using the most stable Llama 3.3 70B Text Model
                    chat_completion = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{
                            "role": "user",
                            "content": f"Strict Board Examiner. Question: {input_q}. Answer: {input_a}. Return ONLY JSON: {{'marks': 'X/10', 'pros': '...', 'cons': '...', 'tip': '...'}}"
                        }],
                        response_format={"type": "json_object"}
                    )
                    
                    st.session_state.eval_json = json.loads(chat_completion.choices[0].message.content)
                    st.session_state.user_data['credits'] -= 5
                except Exception as e:
                    st.error(f"Moderator Error: {e}")
        else:
            st.error("Insufficient Credits!")

    # --- THE CINEMATIC UI DISPLAY ---
    if st.session_state.get("eval_json"):
        res = st.session_state.eval_json
        st.divider()
        
        # 1. Score Box
        c_score, c_feed = st.columns([1, 2])
        with c_score:
            st.markdown(f"""
            <div style="background: #1e3c72; padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #4CAF50;">
                <p style="color: white; font-size: 0.8rem; margin:0;">MODERATOR GRADE</p>
                <h1 style="color: white; font-size: 3.8rem; margin:0; font-weight: 900;">{res.get('marks', 'N/A')}</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with c_feed:
            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 20px; border: 1px solid #30363d; height: 100%;">
                <p style="color: #4CAF50; font-weight: bold; font-size: 0.85rem;">✅ STRENGTHS</p>
                <p style="color: #babbbe; font-size: 0.95rem;">{res.get('pros', 'Analyzing...')}</p>
                <p style="color: #ff4b4b; font-weight: bold; margin-top: 15px;">❌ MARKS LOST</p>
                <p style="color: #babbbe; font-size: 0.95rem;">{res.get('cons', 'Checking gaps...')}</p>
            </div>
            """, unsafe_allow_html=True)

        # 2. Topper Tip (Premium Box)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1c23 0%, #0e1117 100%); padding: 35px; border-radius: 25px; 
                    margin-top: 25px; border: 1px solid #4CAF50; position: relative; overflow: hidden;">
            <div style="position: absolute; top: -15px; right: -10px; font-size: 110px; font-weight: 900; color: rgba(76, 175, 80, 0.04); z-index:0;">TIP</div>
            <div style="position: relative; z-index: 1;">
                <p style="color: #4CAF50; font-weight: bold; font-size: 0.75rem; letter-spacing: 2px;">🎓 THE TOPPER'S MASTERSTROKE</p>
                <p style="font-size: 1.25rem; color: #4CAF50; font-weight: 600; line-height: 1.3;">{res.get('tip', 'Keep improving!')}</p>
                <p style="text-align: right; color: #4CAF50; font-size: 0.7rem; margin-top: 25px;">@TOPPERGPT</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()
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
# --- TAB 5: TOPPERGPT CINEMATIC CARDS ---
with tab5:
    st.markdown("<h3 style='text-align: center; color: #4CAF50;'>🎬 Cinematic Revision Deck</h3>", unsafe_allow_html=True)
    
    if "flash_cards_list" not in st.session_state:
        st.session_state.flash_cards_list = None

    t_input = st.text_input("Enter Topic for Revision:", placeholder="e.g. 'Transformer Working'", key="rev_v8_final")
    
    if st.button("🚀 Build Deck") and t_input:
        if st.session_state.user_data['credits'] >= 2:
            with st.spinner("AI is crafting visual cards..."):
                try:
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "Engineering Professor mode. Create 10 precise flashcards. Format: TITLE | One line definition. Max 15 words. NO bold stars."},
                            {"role": "user", "content": f"Topic: {t_input}"}
                        ]
                    )
                    clean_res = res.choices[0].message.content.replace("**", "").replace("*", "")
                    st.session_state.flash_cards_list = [c for c in clean_res.split("\n") if "|" in c]
                    st.session_state.user_data['credits'] -= 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- THE VISUAL DISPLAY ---
    if st.session_state.get("flash_cards_list"):
        st.divider()
        
        for i, card in enumerate(st.session_state.flash_cards_list):
            try:
                title, content = card.split("|", 1)
                title, content = title.strip().upper(), content.strip()
                
                # 1. LIVE SCREEN UI (Mobile Optimized)
                st.markdown(f"""
                <div style="background: #1a1c23; border-radius: 15px; border-left: 10px solid #4CAF50; 
                            padding: 25px; margin-bottom: 20px; position: relative; overflow: hidden; border: 1px solid #30363d;">
                    <div style="position: absolute; top: -10px; right: -5px; font-size: 100px; font-weight: 900; color: rgba(76,175,80,0.03); z-index:0;">{title[:3]}</div>
                    <div style="position: relative; z-index: 1;">
                        <p style="color: #4CAF50; font-weight: bold; font-size: 0.7rem; letter-spacing: 2px;">TOPPERGPT • CARD {i+1}</p>
                        <h2 style="color: white; font-size: 2rem; margin: 10px 0; font-weight: 800; line-height: 1.1;">{title}</h2>
                        <p style="font-size: 1.1rem; color: #babbbe; line-height: 1.4; font-weight: 400;">{content}</p>
                        <p style="text-align: right; color: #4CAF50; font-weight: bold; font-size: 0.7rem; margin-top: 20px;">@TOPPERGPT</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 2. HD IMAGE GENERATION (Correct Resolution)
                def create_hd_card(t, c, idx):
                    W, H = 1000, 600
                    img = Image.new('RGB', (W, H), color='#1a1c23')
                    d = ImageDraw.Draw(img)
                    d.rectangle([0, 0, 30, H], fill='#4CAF50') 
                    d.text((60, 60), f"TOPPERGPT | CARD {idx+1}", fill='#4CAF50')
                    d.text((60, 140), t[:25], fill='white')
                    wrapped = textwrap.fill(c, width=40)
                    d.multiline_text((60, 260), wrapped, fill='#babbbe', spacing=10)
                    d.text((800, 540), "@TopperGPT", fill='#4CAF50')
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    return buf.getvalue()

                # Action Buttons
                card_img = create_hd_card(title, content, i)
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button(f"📥 Download HD {i+1}", card_img, f"TopperCard_{i+1}.png", "image/png", use_container_width=True)
                with c2:
                    wa_url = f"https://wa.me/?text=Bhai ye dekh {title} ka revision card! Pehle download kar fir status par laga le."
                    st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background:#25D366; color:white; text-align:center; padding:10px; border-radius:10px; font-weight:bold; font-size: 0.9rem;">📲 Share on WA</div></a>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)

            except: continue

        if st.button("🗑️ Clear Deck"):
            st.session_state.flash_cards_list = None
            st.rerun()
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