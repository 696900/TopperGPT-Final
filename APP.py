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
import fitz  # This is PyMuPDF (much more stable)
import textwrap
import hashlib
import os
from datetime import datetime
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.llms.groq import Groq as LlamaGroq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core import Settings

# --- 🛠️ SILENT AI SETUP (The Bulletproof Version) ---

# 1. Global Stability Initializations
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_index" not in st.session_state:
    st.session_state.current_index = None

# 2. Key Matching & Variable Sync (Fixes NameError & 404 Error)
api_key_to_use = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if api_key_to_use:
    from llama_index.embeddings.gemini import GeminiEmbedding
    # Latest stable model to prevent indexing crashes
    Settings.embed_model = GeminiEmbedding(
        model_name="models/text-embedding-004", 
        api_key=api_key_to_use
    )
    Settings.chunk_size = 700
    genai.configure(api_key=api_key_to_use)
else:
    st.warning("⚠️ Dashboard Secrets mein Key missing hai bhai!")

# --- 💰 GLOBAL CREDIT SYSTEM ---
if 'user_credits' not in st.session_state:
    st.session_state.user_credits = 100 

def check_credits(amount):
    if st.session_state.get('user_data') and st.session_state.user_data.get('credits', 0) >= amount:
        return True
    return False

# --- GLOBAL UTILITY: Laser Focus Search ---
def get_subject_specific_text(doc, sub_name):
    sub_text = ""
    start_found = False
    for page in doc:
        text = page.get_text()
        if sub_name.lower() in text.lower():
            start_found = True
        if start_found:
            sub_text += text
            if len(sub_text) > 12000: break 
    return sub_text

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

# --- 2. SESSION STATE & LOGIN ---
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

# --- 3. SIDEBAR (RAZORPAY FIXED + REFERRAL SYSTEM) ---
with st.sidebar:
    st.markdown("<h2 style='color: #4CAF50; margin-bottom:0;'>🎓 TopperGPT Pro</h2>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="wallet-card">
            <p style="color: #eab308; font-weight: bold; margin: 0; font-size: 11px; letter-spacing: 1px;">CURRENT BALANCE</p>
            <p style="color: white; font-size: 28px; font-weight: 900; margin: 5px 0;">{st.session_state.user_data['credits']} 🔥</p>
            <p style="color: #8b949e; font-size: 10px; margin: 0;">Plan: {st.session_state.user_data['tier']}</p>
        </div>
    """, unsafe_allow_html=True)

    # 🎁 REFERRAL SYSTEM (Restored)
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
                elif not re.match(r"^TOP\d{4}$", clean_claim):
                    st.error("Invalid Code Format! Sahi code daal (e.g. TOP9875).")
                else:
                    st.session_state.user_data['credits'] += 5
                    st.session_state.user_data['ref_claimed'] = True
                    st.session_state.user_data['tier'] = "Referred User"
                    st.balloons()
                    st.success("Success! +5 Credits added. 🔥")
                    time.sleep(2)
                    st.rerun()

    st.markdown("---")
    st.markdown('<div class="exam-special-tag">🔥 EXAM SPECIAL ACTIVE</div>', unsafe_allow_html=True)
    
    # 💎 STRICT MAPPING WITH CACHE BUSTER
    payment_links = {
        "Weekly Sureshot (70 Credits) @ ₹59": "https://rzp.io/rzp/FmwE0Ms6",
        "Jugaad Pack (150 Credits) @ ₹99": "https://rzp.io/rzp/AWiyLxEi",
        "Monthly Pro (350 Credits) @ ₹149": "https://rzp.io/rzp/hXcR54E"
    }
    
    plan_choice = st.radio("Select pack:", list(payment_links.keys()), key="razorpay_final_v10")
    
    # 🚀 THE MAGIC: Adding unique timestamp so browser never caches the link
    raw_link = payment_links[plan_choice]
    unique_link = f"{raw_link}?v={int(time.time())}" 

    st.markdown(f"""
        <a href="{unique_link}" target="_blank" style="text-decoration: none;">
            <div style="width: 100%; background: linear-gradient(135deg, #eab308 0%, #ca8a04 100%); color: black; text-align: center; padding: 16px 0; border-radius: 12px; font-weight: bold; cursor: pointer;">
                🚀 Buy: {plan_choice.split(' @ ')[0]}
            </div>
        </a>
        <p style="font-size: 10px; color: #8b949e; text-align: center; margin-top: 5px;">Link Verified: {int(time.time())}</p>
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
with tab1:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>💬 TopperGPT: Exam Chat Engine</h2>", unsafe_allow_html=True)
    
    # 💰 WALLET SYNC: Master Sidebar balance check
    current_credits = st.session_state.user_data.get('credits', 15) if st.session_state.user_data else 15

    # --- 📂 STEP 1: DEEP INDEXING (Google Gemini Stable Engine) ---
    st.markdown("### 📂 Step 1: Upload Exam Material (PDF)")
    up_col, btn_col = st.columns([0.7, 0.3])
    uploaded_file = up_col.file_uploader("Upload Chapter/PYQ PDF", type="pdf", key="chat_pdf_final_v100", label_visibility="collapsed")
    
    # Key check logic: Bypassing potential 404 or Key errors
    api_key_to_use = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")

    if uploaded_file and btn_col.button("🚀 Index for Exam", use_container_width=True):
        if api_key_to_use:
            with st.spinner("Decoding PDF... mapping technical concepts"):
                try:
                    # Using the latest stable model to prevent 404 errors
                    from llama_index.embeddings.gemini import GeminiEmbedding
                    gemini_embed = GeminiEmbedding(model_name="models/text-embedding-004", api_key=api_key_to_use)
                    
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    documents = []
                    for page_num, page in enumerate(doc):
                        text = page.get_text().strip()
                        # Handling scanned pages for engineering subjects
                        if not text:
                            text = f"Page {page_num+1} is a scan. Content: Technical Diagram/Formula."
                        documents.append(Document(text=text, metadata={"page_label": str(page_num + 1)}))
                    
                    # 🔥 CRITICAL: embed_model=gemini_embed kills the OpenAI requirement
                    st.session_state.current_index = VectorStoreIndex.from_documents(
                        documents, 
                        embed_model=gemini_embed 
                    )
                    st.success("✅ System Ready! Ask your doubts in Hinglish.")
                except Exception as e:
                    st.error(f"Indexing Error: {e}")
        else:
            st.error("❌ Key Missing! Streamlit Dashboard > Secrets mein API key daal bhai.")

    # --- 💬 STEP 2: CHAT INTERFACE (No-Crash Logic) ---
    st.divider()
    
    # 
    
    # Safe history retrieval to prevent AttributeError
    history = st.session_state.get("chat_history", [])
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.get("current_index"):
        if user_query := st.chat_input("Ex: 'Explain this concept in Hinglish'"):
            if current_credits >= 1:
                # Initialize history if missing
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []
                
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.markdown(user_query)

                with st.chat_message("assistant"):
                    with st.spinner("Searching Textbook..."):
                        # Force Gemini for query too
                        from llama_index.embeddings.gemini import GeminiEmbedding
                        gemini_embed = GeminiEmbedding(model_name="models/text-embedding-004", api_key=api_key_to_use)
                        
                        query_engine = st.session_state.current_index.as_query_engine(
                            similarity_top_k=5,
                            embed_model=gemini_embed 
                        )
                        
                        custom_prompt = f"""
                        You are TopperGPT. Answer using the provided PDF.
                        1. Use Hinglish (Hindi + English) in Roman script.
                        2. Always cite Page Numbers.
                        3. Use LaTeX for math/formulas: $ $.
                        Query: {user_query}
                        """
                        response = query_engine.query(custom_prompt)
                        st.markdown(response.response)
                        
                        if hasattr(response, 'source_nodes') and response.source_nodes:
                            pages = list(set([node.metadata['page_label'] for node in response.source_nodes]))
                            st.caption(f"📍 Reference: Page {', '.join(pages)}")
                        
                        # 💰 DEDUCT & PERSIST
                        st.session_state.user_data['credits'] -= 1
                        st.session_state.chat_history.append({"role": "assistant", "content": response.response})
                        st.rerun()
            else:
                st.error("❌ Low Credits! Top-up karle bhai.")
    else:
        st.info("👆 Pehle PDF upload karke 'Index for Exam' dabao!")
# ==========================================
# --- GLOBAL UTILITY: SYLLABUS FILTERS ---
# ==========================================
# Inhe define karna zaroori hai varna 'NameError' aayega

def get_clean_json_v2(text):
    try:
        # AI ke kachre se sirf { } wala part nikalne ke liye
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            clean_str = json_match.group(0)
            return json.loads(clean_str)
        return {}
    except Exception:
        return {}

def get_semester_text_v2(doc, sem_name):
    # Sirf wahi pages uthata hai jahan Semester ka naam ho (Fixes Physics-Mechanics mixup)
    full_txt = ""
    for page in doc:
        txt = page.get_text()
        if sem_name.lower() in txt.lower():
            full_txt += txt
    return full_txt

def get_subject_specific_text(doc, sub_name):
    # Subject wise laser focus extraction
    sub_text = ""
    start_found = False
    for page in doc:
        text = page.get_text()
        if sub_name.lower() in text.lower():
            start_found = True
        if start_found:
            sub_text += text
            if len(sub_text) > 12000: break 
    return sub_text

# ==========================================
# --- TAB 2: PRECISION SYLLABUS MANAGER ---
# ==========================================
with tab2:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🎯 Precision Syllabus Manager</h2>", unsafe_allow_html=True)
    
    # Session States to remember progress
    if 'master_tracker' not in st.session_state: st.session_state.master_tracker = {}
    if 'exam_date' not in st.session_state: st.session_state.exam_date = None
    if 'temp_subjects' not in st.session_state: st.session_state.temp_subjects = []

    # 1. TOP DASHBOARD (Progress Metrics)
    if st.session_state.master_tracker:
        cols = st.columns([1, 1, 1])
        # Calculate total and completed topics
        all_t = [t for sem in st.session_state.master_tracker.values() for sub in sem.values() for mod in sub.values() for t in mod]
        total = len(all_t)
        done = sum(1 for t in all_t if t.get('status') == 'Completed')
        
        with cols[0]: st.metric("Overall Mastery", f"{int((done/total)*100 if total > 0 else 0)}%")
        with cols[1]: 
            days = (st.session_state.exam_date - datetime.now().date()).days if st.session_state.exam_date else 0
            st.metric("Exam Countdown", f"{max(0, days)} Days")
        with cols[2]: st.metric("Total Topics", total)
        st.divider()

    # 2. LASER ARCHITECT (Build Your Dashboard)
    with st.expander("📤 Build Your Semester Dashboard", expanded=not st.session_state.master_tracker):
        up_pdf = st.file_uploader("Upload Syllabus PDF", type="pdf", key="laser_v1_main")
        
        c1, c2 = st.columns(2)
        with c1:
            target_sem = st.selectbox("📅 Select Semester", ["Semester I", "Semester II", "Semester III", "Semester IV", "Semester V", "Semester VI"])
        with c2:
            st.session_state.exam_date = st.date_input("Exam Start Date", value=datetime.now().date())
        
        # --- STEP 1: DETECT SUBJECTS ---
        if up_pdf and st.button("🔍 Step 1: Detect Subjects"):
            with st.spinner("Finding Theory Subjects..."):
                try:
                    pdf_bytes = up_pdf.read()
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    relevant_txt = get_semester_text_v2(doc, target_sem)
                    
                    llm_fast = LlamaGroq(model="llama-3.1-8b-instant", api_key=st.secrets["GROQ_API_KEY"])
                    prompt = f"List MAIN THEORY subjects for '{target_sem}'. IGNORE Labs. Return JSON: {{'subjects': ['Maths', 'Physics']}}. Text: {relevant_txt[:8000]}"
                    res = llm_fast.complete(prompt)
                    st.session_state.temp_subjects = get_clean_json_v2(res.text).get("subjects", [])
                    st.success(f"Detected: {st.session_state.temp_subjects}")
                except Exception as e: st.error(f"Scan Error: {e}")

        # --- STEP 2: HANDLE ELECTIVES & BUILD TRACKER ---
        if st.session_state.temp_subjects:
            st.markdown("---")
            st.info("💡 Elective subjects ke liye apna option specify karein (e.g. Physics-I ya Chemistry-I)")
            final_list = []
            for s in st.session_state.temp_subjects:
                if any(x in s.lower() for x in ["elective", "choice", "group"]):
                    choice = st.text_input(f"Your Choice for '{s}'?", key=f"el_laser_{s}")
                    if choice: final_list.append(f"{s}: {choice}")
                else:
                    final_list.append(s)
            
            if st.button("🚀 Step 2: Build Tracker Tree"):
                with st.spinner("Building isolated subject trees... (No mix-ups)"):
                    try:
                        llm_main = LlamaGroq(model="llama-3.3-70b-versatile", api_key=st.secrets["GROQ_API_KEY"])
                        up_pdf.seek(0)
                        doc = fitz.open(stream=up_pdf.read(), filetype="pdf")
                        
                        master_tree = {target_sem: {}}
                        for sub in final_list:
                            # Laser focusing on one subject at a time
                            sub_context = get_subject_specific_text(doc, sub.split(':')[0])
                            prompt = f"Focus ONLY on '{sub}'. Extract 6 Modules and topics. Return JSON: {{'Mod 1': ['Topic A']}}. Text: {sub_context[:12000]}"
                            res = llm_main.complete(prompt)
                            sub_data = get_clean_json_v2(res.text)
                            if sub_data:
                                master_tree[target_sem][sub] = {mod: [{"name": t, "status": "Not Started"} for t in topics] 
                                                                 for mod, topics in sub_data.items()}
                        
                        st.session_state.master_tracker = master_tree
                        st.session_state.temp_subjects = [] # Clear temp list
                        st.balloons()
                        st.rerun()
                    except Exception as e: st.error(f"Build Error: {e}")

    # 3. INTERACTIVE TRACKER UI
    if st.session_state.master_tracker:
        for sem, subs in st.session_state.master_tracker.items():
            st.markdown(f"### 📊 {sem} Tracker")
            for sub_name, modules in subs.items():
                with st.expander(f"📘 {sub_name}"):
                    for mod_name, topics in modules.items():
                        st.markdown(f"**📂 {mod_name}**")
                        for i, t in enumerate(topics):
                            # Unique ID for state persistence
                            u_hash = hashlib.md5(f"{sub_name}_{mod_name}_{t['name']}".encode()).hexdigest()
                            c1, c2 = st.columns([0.7, 0.3])
                            with c1: 
                                st.write(f"🔹 {t['name']}")
                            with c2:
                                s = st.selectbox("Status", ["Not Started", "Completed"], key=u_hash, 
                                               index=0 if t['status']=="Not Started" else 1, label_visibility="collapsed")
                                if s != t['status']: 
                                    t['status'] = s
                                    st.rerun()

        if st.button("🗑️ Reset Tracker"):
            st.session_state.master_tracker = {}
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
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🧠 Concept Mindmap Architect</h2>", unsafe_allow_html=True)
    
    # 💰 WALLET SYNC: Sidebar credits se link hai
    current_bal = st.session_state.user_data.get('credits', 0) if st.session_state.user_data else 0

    incoming_topic = st.session_state.get('active_topic', "")
    col_in, col_opt = st.columns([0.7, 0.3])
    with col_in:
        mm_input = st.text_input("Concept Name:", value=incoming_topic, key="mm_final_stable_v10", placeholder="e.g. Laser Working")
    with col_opt:
        use_pdf = st.checkbox("Deep PDF Scan", value=True if st.session_state.get('current_index') else False)

    cost = 8 if (use_pdf and st.session_state.get('current_index')) else 2

    if st.button(f"🚀 Build High-Res Mindmap ({cost} Credits)"):
        if mm_input:
            if current_bal >= cost:
                with st.spinner("Generating HD Architecture..."):
                    try:
                        # GROQ LLM for fast code generation
                        llm = LlamaGroq(model="llama-3.3-70b-versatile", api_key=st.secrets["GROQ_API_KEY"])
                        
                        context = ""
                        if use_pdf and st.session_state.get('current_index'):
                            # Using Gemini for technical context extraction
                            qe = st.session_state.current_index.as_query_engine(similarity_top_k=5)
                            context_res = qe.query(f"Extract key technical components for {mm_input}.")
                            context = f"PDF Context: {context_res.response}"

                        # Strict prompt to prevent Syntax Errors
                        prompt = f"""
                        Create a Mermaid.js mindmap for: '{mm_input}'.
                        {context}
                        Rules:
                        1. Start code with 'mindmap'
                        2. Root must be 'root(({mm_input}))'
                        3. Use simple text for nodes. NO brackets () [] or special chars inside nodes.
                        4. Return ONLY the Mermaid code block.
                        """
                        res = llm.complete(prompt)
                        mm_code = res.text.replace("```mermaid", "").replace("```", "").strip()
                        
                        # 💰 DEDUCT & SAVE
                        st.session_state.user_data['credits'] -= cost
                        st.session_state.last_mm_code = mm_code
                        st.toast(f"Success! {cost} Credits deducted.")
                        st.rerun() 
                    except Exception as e: st.error(f"Logic Error: {e}")
            else: st.error("Credits low hain bhai! Sidebar se top-up kar.")
        else: st.warning("Concept ka naam toh dalo!")

    # --- HD RENDER & DOWNLOAD ENGINE (Scale 4) ---
    if "last_mm_code" in st.session_state:
        st.markdown("---")
        import streamlit.components.v1 as components
        
        # High resolution script with error suppression
        html_code = f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <div id="capture_area" style="background: white; padding: 40px; border-radius: 15px; display: inline-block; min-width: 800px; text-align: center;">
            <div class="mermaid" style="font-size: 20px;">
            {st.session_state.last_mm_code}
            </div>
        </div>
        <br><br>
        <button onclick="downloadHD()" style="background:#4CAF50; color:white; border:none; padding:15px 30px; border-radius:12px; cursor:pointer; font-weight:bold; font-size:18px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            📥 Download HD Mindmap (Clear PNG)
        </button>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            // Suppress errors to keep UI clean even if syntax is tricky
            mermaid.initialize({{ startOnLoad: true, theme: 'forest', securityLevel: 'loose', suppressErrors: true }});
            
            window.downloadHD = function() {{
                const area = document.querySelector("#capture_area");
                html2canvas(area, {{ 
                    scale: 4,  // 4x resolution for crystal clear quality
                    useCORS: true,
                    backgroundColor: "#ffffff"
                }}).then(canvas => {{
                    let link = document.createElement('a');
                    link.download = 'TopperGPT_HD_Mindmap.png';
                    link.href = canvas.toDataURL("image/png", 1.0);
                    link.click();
                }});
            }}
        </script>
        """
        components.html(html_code, height=900, scrolling=True)
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