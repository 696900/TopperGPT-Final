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
from PIL import Image
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
# --- 🛠️ SILENT AI SETUP (v1 Stable Lock) ---
api_key_to_use = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if api_key_to_use:
    from llama_index.llms.gemini import Gemini
    from llama_index.embeddings.gemini import GeminiEmbedding
    
    # ✅ FIX: Using transport="rest" and proper model naming
    Settings.llm = Gemini(
        model_name="models/gemini-1.5-flash", 
        api_key=api_key_to_use,
        transport="rest"  # <--- Ye line 404 errors ko khatam kar degi!
    )
    Settings.embed_model = GeminiEmbedding(
        model_name="models/text-embedding-004", 
        api_key=api_key_to_use,
        transport="rest"  # <--- Stable transport lock
    )
# --- 💎 REVENUE LOOP: MASTER CREDIT CHECKER (MUST BE AT TOP) ---
def use_credits(amount):
    """Checks and deducts credits from session state."""
    if "user_data" in st.session_state and st.session_state.user_data is not None:
        current_credits = st.session_state.user_data.get('credits', 0)
        if current_credits >= amount:
            st.session_state.user_data['credits'] -= amount
            return True
    return False
# --- 1. CONFIGURATION: PRO BALANCED MODE ---
st.set_page_config(
    page_title="TopperGPT Pro", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# 🖋️ PROFESSIONAL UI STYLES
EVAL_CSS = """
<style>
.block-container { max-width: 92% !important; padding-top: 2rem !important; }
.stApp { background-color: #0d1117 !important; color: #ffffff !important; }

/* Sidebar & Wallet */
[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
.wallet-card { 
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
    padding: 20px; border-radius: 15px; border: 1px solid #4CAF50; 
    text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

/* Professional Referral Box */
.referral-container {
    background: rgba(76, 175, 80, 0.05);
    border: 1px solid #4CAF50; padding: 15px; border-radius: 12px; margin-bottom: 20px;
}

/* Cinematic Payment Option */
.pay-card {
    background: #1c2128; border: 1px solid #30363d;
    padding: 12px; border-radius: 10px; margin-bottom: 10px;
    transition: 0.3s; cursor: pointer;
}
.pay-card:hover { border-color: #4CAF50; background: #22272e; }
</style>
"""
st.markdown(EVAL_CSS, unsafe_allow_html=True)

# --- 2. GLOBAL LOGIC & KEYS ---
if "user_data" not in st.session_state: st.session_state.user_data = None

# 🛠️ AI SETUP
api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    Settings.embed_model = GeminiEmbedding(model_name="models/text-embedding-004", api_key=api_key)
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 3. LOGIN PAGE ---
if st.session_state.user_data is None:
    _, col_mid, _ = st.columns([1, 1.2, 1])
    with col_mid:
        st.markdown('<div style="text-align:center; padding:40px; background:#161b22; border-radius:20px; border:1px solid #4CAF50;">'
                    '<h1 style="color:#4CAF50; font-style:italic; margin:0;">TopperGPT</h1>'
                    '<p style="color:#8b949e; letter-spacing: 1px;">UNIVERSITY RESEARCH PORTAL</p>'
                    '<hr style="border-color:#30363d;"><p style="color:#4CAF50; font-weight:bold;">🎁 +15 FREE Credits on Login</p></div>', unsafe_allow_html=True)
        if st.button("🔴 Secure Google Login", use_container_width=True):
            st.session_state.user_data = {
                "email": "student@mu.edu", "credits": 15, 
                "referral_code": "TOP" + str(int(time.time()))[-4:], "ref_claimed": False
            }
            st.rerun()
    st.stop()

# --- 4. SIDEBAR (FOUNDER EDITION) ---
# --- 4. SIDEBAR: CINEMATIC WALLET & PREMIUM REFERRAL ---
with st.sidebar:
    st.markdown("<h2 style='color: #4CAF50; margin-bottom:10px; font-style:italic;'>🎓 TopperGPT Pro</h2>", unsafe_allow_html=True)
    
    # Wallet Card with Glow effect
    st.markdown(f'''
        <div class="wallet-card">
            <p style="margin:0; font-size:11px; color:#eab308; font-weight:bold; letter-spacing:1px;">AVAILABLE CREDITS</p>
            <h1 style="margin:5px 0; color:white; font-size:42px; font-weight:900;">{st.session_state.user_data["credits"]} <span style="font-size:20px;">🔥</span></h1>
            <p style="margin:0; font-size:10px; color:#8b949e;">Plan: Premium Student</p>
        </div>
    ''', unsafe_allow_html=True)

    # 🎁 REFERRAL SYSTEM: THE "GIFT CARD" DESIGN
    st.markdown("<p style='font-weight:bold; color:#4CAF50; font-size:14px; margin-top:20px;'>🎁 REFER & EARN FREE CREDITS</p>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown(f'''
            <div style="background: rgba(76, 175, 80, 0.08); border: 2px dashed #4CAF50; padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 10px;">
                <p style="color: #c9d1d9; font-size: 13px; margin-bottom: 5px;">Share this code with a friend. Both get <b>+5 Credits</b>!</p>
                <div style="background: #0d1117; padding: 10px; border-radius: 8px; border: 1px solid #30363d;">
                    <code style="color: #4CAF50; font-size: 18px; font-weight: bold;">{st.session_state.user_data['referral_code']}</code>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        if not st.session_state.user_data.get('ref_claimed', False):
            claim_input = st.text_input("Friend's Referral Code?", placeholder="Enter TOPXXXX", key="ref_v108")
            if st.button("Claim My Bonus (+5)", use_container_width=True):
                clean_claim = claim_input.strip().upper()
                
                if not clean_claim:
                    st.warning("Pehle code toh dalo bhai!")
                elif clean_claim == st.session_state.user_data['referral_code']:
                    st.error("Shaane! Apna hi code daal ke credits badhayega? 😂")
                else:
                    # Success Path
                    st.session_state.user_data['credits'] += 5
                    st.session_state.user_data['ref_claimed'] = True
                    st.balloons()
                    st.success("Boom! +5 Credits added. 🔥")
                    st.rerun()

    st.markdown("---")
    
    # 💎 REFILL PACKS: DYNAMIC CARDS
    st.markdown("<p style='font-weight:bold; color:#4CAF50; font-size:14px; margin-bottom:15px;'>💎 PREMIUM REFILL PACKS</p>", unsafe_allow_html=True)
    
    refill_packs = [
        {"name": "Weekly Sureshot", "credits": "70 Credits", "price": "₹59", "url": "https://rzp.io/rzp/FmwE0Ms6"},
        {"name": "Jugaad Pack", "credits": "150 Credits", "price": "₹99", "url": "https://rzp.io/rzp/AWiyLxEi"},
        {"name": "Monthly Pro", "credits": "350 Credits", "price": "₹149", "url": "https://rzp.io/rzp/hXcR54E"}
    ]

    for pack in refill_packs:
        st.markdown(f'''
            <a href="{pack['url']}" target="_blank" style="text-decoration: none;">
                <div class="pay-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color:#4CAF50; font-weight:bold;">{pack['name']}</span>
                        <span style="color:white; font-weight:bold;">{pack['price']}</span>
                    </div>
                    <div style="text-align: left; font-size: 11px; color: #8b949e; margin-top: 5px;">
                        Instant {pack['credits']} Added to Wallet
                    </div>
                </div>
            </a>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔓 Secure Logout", use_container_width=True):
        st.session_state.user_data = None
        st.rerun()
# --- 5. MAIN TABS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "💬 Chat PDF", "📊 Syllabus", "📝 Answer Eval", "🧠 MindMap", 
    "🃏 Flashcards", "❓ Engg PYQs", "🔍 Search", "🤝 Topper Connect", "⚖️ Legal"
])
## --- TAB 1: SMART NOTE ANALYSIS (STABLE VISION ENGINE) ---
# --- TAB 1: TOPPERGPT CHAT ENGINE (V126 - GLOBAL SYNCED) ---
with tab1:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>💬 TopperGPT: Exam Chat Engine</h2>", unsafe_allow_html=True)
    
    # Imports strictly for PDF handling
    import fitz
    from llama_index.core import VectorStoreIndex, Document

    # --- 📂 STEP 1: INDEXING ---
    st.markdown("### 📂 Step 1: Upload Exam Material (PDF)")
    up_col, btn_col = st.columns([0.7, 0.3])
    uploaded_file = up_col.file_uploader("Upload Chapter PDF", type="pdf", key="pdf_v126")
    
    if uploaded_file and btn_col.button("🚀 Index for Exam", use_container_width=True):
        with st.spinner("Decoding PDF... mapping technical concepts"):
            try:
                # Fast Stream Processing with PyMuPDF
                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                documents = []
                for i, page in enumerate(doc):
                    text = page.get_text().strip() or f"Diagram/Table Content Page {i+1}"
                    documents.append(Document(text=text, metadata={"page_label": str(i+1)}))
                
                # 🔥 CRITICAL: Uses Global Settings (Gemini) defined at the top
                st.session_state.current_index = VectorStoreIndex.from_documents(documents)
                st.success("✅ System Ready! Phod de exam.")
                st.rerun()
            except Exception as e:
                st.error(f"Indexing Error: {str(e)}")

    st.divider()

    # --- 💬 STEP 2: STABLE CHAT ---
    if "chat_history" not in st.session_state: 
        st.session_state.chat_history = []

    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.get("current_index"):
        if user_query := st.chat_input("Ex: Explain the working principle in Hinglish"):
            # Sync with your wallet (1 credit per query)
            if use_credits(1):
                st.session_state.chat_history.append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.markdown(user_query)

                with st.chat_message("assistant"):
                    with st.spinner("Analyzing Textbook..."):
                        try:
                            # Uses global LLM and Embed settings automatically
                            qe = st.session_state.current_index.as_query_engine(similarity_top_k=3)
                            res = qe.query(f"Answer in simple Hinglish: {user_query}")
                            
                            st.markdown(res.response)
                            st.session_state.chat_history.append({"role": "assistant", "content": res.response})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Chat Engine Busy: {e}")
                            st.session_state.user_data['credits'] += 1 # Auto-Refund on fail
            else:
                st.error("❌ Low Balance! Sidebar se pack buy karlo.")
    else:
        st.info("👆 Pehle PDF upload karke 'Index for Exam' dabao!")
# ==========================================
# --- GLOBAL UTILITY: SYLLABUS FILTERS ---
# ==========================================

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
            # Limit to 10 pages to avoid mixing with other subjects
            if len(sub_text) > 15000: break 
    return sub_text

# ==========================================
# --- TAB 2: PRECISION SYLLABUS MANAGER ---
# ==========================================
with tab2:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🎯 Precision Syllabus Manager</h2>", unsafe_allow_html=True)
    
    if 'master_tracker' not in st.session_state: st.session_state.master_tracker = {}

    # 1. TOP DASHBOARD (Metrics)
    if st.session_state.master_tracker:
        cols = st.columns(3)
        all_t = [t for sem in st.session_state.master_tracker.values() for sub in sem.values() for mod in sub.values() for t in mod]
        total = len(all_t)
        done = sum(1 for t in all_t if t.get('status') == 'Completed')
        with cols[0]: st.metric("Overall Mastery", f"{int((done/total)*100 if total > 0 else 0)}%")
        with cols[2]: st.metric("Total Topics", total)
        st.divider()

    # 2. BUILD ENGINE (Hard-Filtered Subject Detection)
    with st.expander("📤 Build Your Semester Tracker", expanded=not st.session_state.master_tracker):
        up_pdf = st.file_uploader("Upload Syllabus PDF", type="pdf", key="final_stable_v100")
        
        c1, c2 = st.columns(2)
        with c1:
            target_sem = st.selectbox("📅 Select Semester", ["Semester I", "Semester II", "Semester III", "Semester IV"])
        with c2:
            st.session_state.exam_date = st.date_input("Exam Start Date", value=datetime.now().date())
        
        if up_pdf and st.button("🚀 Step 1: Detect & Build Tracker"):
            with st.spinner(f"Filtering {target_sem} Data..."):
                try:
                    pdf_bytes = up_pdf.read()
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    
                    # SEMESTER SPECIFIC FILTER: Sirf relevant pages scan karega
                    relevant_txt = ""
                    for page in doc:
                        text = page.get_text()
                        if target_sem.lower() in text.lower():
                            relevant_txt += text
                    
                    # THEORY ONLY PROMPT: Labs aur extra electives ko block karne ke liye
                    llm_main = LlamaGroq(model="llama-3.3-70b-versatile", api_key=st.secrets["GROQ_API_KEY"])
                    prompt = f"""
                    Engineering Professor Mode. From this text for '{target_sem}':
                    1. List ONLY the 5-6 MAIN THEORY subjects (e.g., Maths, Physics, Chemistry, Mechanics).
                    2. IGNORE ALL Labs, Practical subjects, and Workshop.
                    3. For each subject, extract exactly 6 Units and their sub-topics.
                    4. IMPORTANT: No duplicate subjects or extra elective inputs.
                    
                    Return ONLY valid JSON: 
                    {{ "Subject Name": {{ "Unit 1": ["Topic A", "Topic B"] }} }}
                    
                    Text: {relevant_txt[:12000]}
                    """
                    
                    res = llm_main.complete(prompt)
                    clean_data = get_clean_json_v2(res.text)
                    
                    if clean_data:
                        # Converting to Tracker Format with Status
                        st.session_state.master_tracker = {target_sem: {}}
                        for sub, mods in clean_data.items():
                            st.session_state.master_tracker[target_sem][sub] = {
                                mod: [{"name": t, "status": "Not Started"} for t in topics] 
                                for mod, topics in mods.items()
                            }
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("AI couldn't extract subjects. Text clear nahi hai.")
                        
                except Exception as e: st.error(f"Scan Error: {e}")

    # 3. INTERACTIVE UI (Double Column Layout)
    if st.session_state.master_tracker:
        for sem, subs in st.session_state.master_tracker.items():
            st.markdown(f"### 📊 {sem} Tracker")
            for sub_name, modules in subs.items():
                with st.expander(f"📘 {sub_name}", expanded=True):
                    for mod_name, topics in modules.items():
                        st.markdown(f"**📂 {mod_name}**")
                        for i, t in enumerate(topics):
                            u_hash = hashlib.md5(f"{sub_name}_{mod_name}_{t['name']}".encode()).hexdigest()
                            c1, c2 = st.columns([0.7, 0.3])
                            with c1: st.write(f"🔹 {t['name']}")
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
# --- TAB 3: TOPPERGPT PRO EVALUATOR (V119 - TWO-STEP LOGIC) ---
with tab3:
    st.markdown(EVAL_CSS, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🖋️ TopperGPT: Pro Moderator</h2>", unsafe_allow_html=True)
    
    # 💰 REVENUE LOOP: Master Cost
    eval_cost = 5

    # Step-by-step state management
    if "extracted_text" not in st.session_state: st.session_state.extracted_text = None
    if "eval_result" not in st.session_state: st.session_state.eval_result = None

    ans_file = st.file_uploader("Upload Answer Sheet Photo", type=["jpg", "png", "jpeg"], key="v119_file")
    
    if ans_file:
        img = Image.open(ans_file).convert("RGB")
        # Step 1: PIL Image Resize (Jugaad No. 1 - Prevent size error)
        img.thumbnail((800, 800)) 
        st.image(img, caption="Document Detected", width=300)

        # --- STEP A: THE EYE (OCR) ---
        if st.button(f"🔍 Scan Handwriting ({eval_cost} Credits)"):
            if use_credits(eval_cost):
                with st.spinner("Moderator is reading..."):
                    try:
                        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        
                        # Sirf text nikalne ka prompt
                        response = model.generate_content(["Transcribe the handwritten text from this image exactly.", img])
                        
                        if response.text:
                            st.session_state.extracted_text = response.text
                            st.rerun()
                    except Exception as e:
                        st.session_state.user_data['credits'] += eval_cost # Refund
                        st.error("Server busy! Ek baar phir try karo.")
            else:
                st.error("Bhai credits khatam!")

    # --- STEP B: THE BRAIN (EVALUATION) ---
    if st.session_state.extracted_text and not st.session_state.eval_result:
        st.success("✅ Scanning Complete!")
        # Student text dekh sakta hai (Trust building)
        edited_text = st.text_area("Check/Edit Scanned Text:", value=st.session_state.extracted_text, height=200)
        
        if st.button("📝 Generate Marks & Feedback"):
            with st.spinner("Professor is marking..."):
                try:
                    marking_prompt = f"""
                    Evaluate this student answer as a Board Examiner:
                    ANSWER: {edited_text}
                    Return ONLY JSON:
                    {{"question": "string", "marks": int, "feedback": "string", "improvement": "string"}}
                    """
                    
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": marking_prompt}],
                        response_format={"type": "json_object"}
                    )
                    st.session_state.eval_result = json.loads(res.choices[0].message.content)
                    st.rerun()
                except:
                    st.error("Format error! Phir se 'Generate Marks' dabao.")

    # --- FINAL DISPLAY ---
    if st.session_state.eval_result:
        res = st.session_state.eval_result
        st.divider()
        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            st.markdown(f'<div class="eval-card"><div class="score-circle">{res.get("marks", 0)}/10</div></div>', unsafe_allow_html=True)
        with c2:
            st.info(f"**Question:** {res.get('question', 'N/A')}")
            st.success(f"**Feedback:** {res.get('feedback', 'N/A')}")
        
        if st.button("🔄 New Evaluation"):
            st.session_state.extracted_text = None
            st.session_state.eval_result = None
            st.rerun()
# --- TAB 4: CONCEPT MINDMAP ARCHITECT (REVENUE SYNCED) ---
# --- TAB 4: CINEMATIC COLOURFUL MINDMAP (V113 - REVENUE SYNCED) ---
with tab4:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🎨 Vibrant Concept Architect</h2>", unsafe_allow_html=True)
    
    # Wallet Sync & UI
    incoming_topic = st.session_state.get('active_topic', "")
    col_in, col_opt = st.columns([0.7, 0.3])
    
    with col_in:
        mm_input = st.text_input("Concept Name:", value=incoming_topic, key="mm_v113_vibrant", placeholder="e.g. Laser Action")
    with col_opt:
        use_pdf = st.checkbox("Deep PDF Scan", value=True if st.session_state.get('current_index') else False)

    # 💰 Revenue Loop Cost
    mm_cost = 5 if (use_pdf and st.session_state.get('current_index')) else 2

    if st.button(f"🚀 Generate Vibrant Mindmap ({mm_cost} Credits)"):
        if mm_input:
            # --- START REVENUE LOOP ---
            if use_credits(mm_cost):
                with st.spinner("Designing Colourful Architecture..."):
                    try:
                        context = ""
                        if use_pdf and st.session_state.get('current_index'):
                            qe = st.session_state.current_index.as_query_engine(similarity_top_k=3)
                            context_res = qe.query(f"Extract main branches for {mm_input}.")
                            context = f"PDF Context: {context_res.response}"

                        # Prompt Optimized for Colour & Fit
                        prompt = f"""
                        Create a Mermaid.js mindmap for: '{mm_input}'. {context}
                        Rules:
                        1. Start with 'mindmap'
                        2. Root is 'root(({mm_input}))'
                        3. Limit to 4-5 main branches so it fits the screen.
                        4. NO special characters.
                        """
                        
                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        
                        st.session_state.last_mm_code = res.choices[0].message.content.replace("```mermaid", "").replace("```", "").strip()
                        st.toast(f"Success! {mm_cost} Credits Deducted.")
                        st.rerun() 
                        
                    except Exception as e:
                        # Refund on error
                        st.session_state.user_data['credits'] += mm_cost
                        st.error(f"Logic Error: {e}")
            else:
                st.error("Credits low hain bhai! Sidebar se top-up kar.")

    # --- 🎭 VIBRANT RENDERING ENGINE (Screen-Fit & Colourful) ---
    if "last_mm_code" in st.session_state:
        st.markdown("---")
        import streamlit.components.v1 as components
        
        # HTML with Responsive Container
        html_code = f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <div id="capture_area" style="
            background: #0d1117; 
            padding: 20px; 
            border-radius: 20px; 
            border: 2px solid #4CAF50;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
        ">
            <div class="mermaid" style="width: 100%; max-width: 800px;">
            {st.session_state.last_mm_code}
            </div>
        </div>
        <br>
        <button onclick="downloadHD()" style="
            width: 100%; background: #4CAF50; color: white; border: none; 
            padding: 15px; border-radius: 12px; font-weight: bold; cursor: pointer;
        ">
            📥 Download Vibrant Mindmap (PNG)
        </button>
        
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            
            mermaid.initialize({{ 
                startOnLoad: true, 
                theme: 'forest', 
                securityLevel: 'loose',
                themeVariables: {{
                    fontSize: '20px',
                    primaryColor: '#4CAF50',
                    nodeBorder: '#4CAF50',
                    mainBkg: '#1c2128',
                    textColor: '#fff'
                }}
            }});
            
            window.downloadHD = function() {{
                const area = document.querySelector("#capture_area");
                html2canvas(area, {{ scale: 3, backgroundColor: "#0d1117" }}).then(canvas => {{
                    let link = document.createElement('a');
                    link.download = 'TopperGPT_Vibrant_Map.png';
                    link.href = canvas.toDataURL("image/png");
                    link.click();
                }});
            }}
        </script>
        """
        components.html(html_code, height=650, scrolling=True)
    # --- TAB 5: FLASHCARDS (STRICT TOPIC LOCK) ---
# --- TAB 5: TOPPERGPT CINEMATIC CARDS (REVENUE SYNCED) ---
with tab5:
    st.markdown("<h3 style='text-align: center; color: #4CAF50;'>🎬 Cinematic Revision Deck</h3>", unsafe_allow_html=True)
    
    if "flash_cards_list" not in st.session_state:
        st.session_state.flash_cards_list = None

    t_input = st.text_input("Enter Topic for Revision:", placeholder="e.g. 'Transformer Working'", key="rev_v8_final")
    
    # 💰 Cost for generating a professional deck
    card_cost = 2

    if st.button(f"🚀 Build Deck ({card_cost} Credits)") and t_input:
        # --- START REVENUE LOOP ---
        if use_credits(card_cost):
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
                    
                    st.toast(f"Deck Created! {card_cost} Credits deducted.")
                    st.rerun()
                except Exception as e:
                    # Refund on error
                    st.session_state.user_data['credits'] += card_cost
                    st.error(f"Error: {e}")
        else:
            st.error("Bhai credits khatam! Sidebar se top-up kar lo.")

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
                    # Limited title for image
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
# --- TAB 6: UNIVERSITY VERIFIED PYQS (V114 - REVENUE SYNCED) ---
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

    # 💰 Cost for University Research
    pyq_cost = 1

    if st.button(f"🔍 Fetch Important PYQs ({pyq_cost} Credit)"):
        if subj_name:
            # --- START REVENUE LOOP ---
            if use_credits(pyq_cost):
                with st.spinner(f"Fetching {subj_name} Question Bank..."):
                    prompt = f"Act as a Paper Setter for {univ}. Provide 5 Repeated PYQs and 2 Expected questions for {subj_name} ({branch}, {semester}). Format: Clear and Professional."
                    
                    try:
                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile", 
                            messages=[{"role": "user", "content": prompt}]
                        )
                        
                        # SAVE TO SESSION STATE
                        st.session_state.pyq_result = res.choices[0].message.content
                        st.session_state.pyq_subject_last = subj_name
                        
                        st.toast(f"Success! {pyq_cost} Credit deducted.")
                        st.rerun()

                    except Exception as e:
                        # Refund on error
                        st.session_state.user_data['credits'] += pyq_cost
                        st.error(f"API Error: {e}")
            else:
                st.error("Low Balance! Sidebar se top-up karo.")
        else:
            st.warning("Subject name dalo bhai.")

    # DISPLAY LOGIC
    if st.session_state.pyq_result:
        st.markdown("---")
        st.success(f"Result for {st.session_state.pyq_subject_last}")
        st.markdown(st.session_state.pyq_result)
        
        st.download_button(
            label="📥 Download This Bank",
            data=st.session_state.pyq_result,
            file_name=f"{st.session_state.pyq_subject_last}_PYQs.txt",
            use_container_width=True
        )
        
        if st.button("🗑️ Clear Results"):
            st.session_state.pyq_result = None
            st.rerun()
    # --- TAB 7: ADVANCED TOPIC SEARCH (FINAL COLLEGE FIX) ---
# --- TAB 7: TOPIC SEARCH (THE ULTIMATE BULLETPROOF VERSION) ---
# --- TAB 7: TOPIC RESEARCH (PRO VISUALS WITH GRAPHVIZ) ---
with tab7:
    st.subheader("🔍 Engineering Topic Research")
    st.write("Instant 360° Analysis: Detailed Report, Architecture Flowchart, & 15+ PYQs.")
    
    search_cost = 3
    roadmap_cost = 2 
    st.info(f"🚀 Premium Analysis: **{search_cost} Credits** | AI Roadmap: **{roadmap_cost} Credits**")

    if "research_data" not in st.session_state: st.session_state.research_data = None
    if "research_query" not in st.session_state: st.session_state.research_query = ""

    col_q, col_d = st.columns([0.7, 0.3])
    query = col_q.text_input("Enter Engineering Topic (e.g. Transformer):", key="search_final_absolute_v1")
    exam_date = col_d.date_input("Target Exam Date", key="roadmap_date_v1")
    
    if st.button("Deep Research", key="btn_absolute_v1") and query:
        if st.session_state.user_data['credits'] >= search_cost:
            with st.spinner(f"Analyzing '{query}'..."):
                # Updated Prompt: Mermaid ko nikal kar Graphviz DOT code mangwaya hai
                prompt = f"""
                Act as an Engineering Professor. Provide a comprehensive report for: '{query}'.
                Use these markers exactly:
                [1_DEF] for technical definition.
                [2_KEY] for 7-10 technical keywords.
                [3_CXP] for detailed technical breakdown/working.
                [4_SMP] for a simple 2-line explanation.
                [5_DOT] for ONLY Graphviz DOT code (digraph G {{...}}) showing its architecture. Use clean labels.
                [6_PYQ] for at least 15 REAL university exam questions.
                """
                try:
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.session_state.research_data = res.choices[0].message.content
                    st.session_state.research_query = query
                    st.session_state.user_data['credits'] -= search_cost 
                    st.rerun()
                except Exception as e: st.error(f"System Busy. Error: {e}")

    if st.session_state.research_data:
        out = st.session_state.research_data
        q_name = st.session_state.research_query

        def get_sec(m1, m2=None):
            try:
                parts = out.split(m1)
                if len(parts) < 2: return "Data missing."
                content = parts[1]
                if m2 and m2 in content: content = content.split(m2)[0]
                return content.strip().replace("```dot", "").replace("```", "").replace("```gv", "")
            except: return "Section error."

        st.markdown(f"## 📘 Technical Report: {q_name}")
        st.info(f"**1. Standard Definition:**\n\n{get_sec('[1_DEF]', '[2_KEY]')}")
        
        c1, c2 = st.columns(2)
        with c1: st.write(f"**2. Technical Keywords:**\n\n{get_sec('[2_KEY]', '[3_CXP]')}")
        with c2: st.success(f"**4. Simple Explanation:**\n\n{get_sec('[4_SMP]', '[5_DOT]')}")
        
        st.warning(f"**3. Technical Breakdown:**\n\n{get_sec('[3_CXP]', '[4_SMP]')}")

        # --- HD GRAPHVIZ FLOWCHART (Better than Mermaid) ---
        st.markdown("---")
        st.markdown("### 📊 5. Architecture Flowchart")
        dot_code = get_sec('[5_DOT]', '[6_PYQ]')
        if "digraph" in dot_code:
            # Graphviz is built-in to Streamlit and renders beautiful SVGs
            st.graphviz_chart(dot_code, use_container_width=True)
        else:
            st.info("Generating architecture visuals...")
        
        st.markdown("---")
        st.markdown("### ❓ 6. Expected Exam Questions (15+ PYQs)")
        st.write(get_sec('[6_PYQ]'))

        # --- PREMIUM ROADMAP VIEW ---
        st.markdown("---")
        st.markdown("### 📅 Personalized Study Roadmap")
        days_left = (exam_date - datetime.now().date()).days
        
        if st.button(f"Generate Plan for {days_left} Days ({roadmap_cost} Credits)"):
            if st.session_state.user_data['credits'] >= roadmap_cost:
                with st.spinner("AI Mentor is planning..."):
                    rm_prompt = f"Create a Day-by-Day study plan for: {q_name}. Days left: {days_left}. Use 'Day X:' format."
                    rm_res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": rm_prompt}]
                    )
                    st.session_state.user_data['credits'] -= roadmap_cost
                    st.success("Plan Generated!")
                    roadmap_text = rm_res.choices[0].message.content
                    days_data = roadmap_text.split("Day")
                    
                    for day in days_data:
                        if day.strip() and ":" in day:
                            d_num, d_text = day.split(':', 1)
                            st.markdown(f"""
                                <div style="background: #1a1c23; padding: 12px; border-radius: 8px; border-left: 4px solid #4CAF50; margin-bottom: 8px; border: 1px solid #30363d;">
                                    <span style="color: #4CAF50; font-weight: bold;">DAY {d_num.strip()}</span>: 
                                    <span style="color: #e6edf3;">{d_text.strip()}</span>
                                </div>
                            """, unsafe_allow_html=True)
            else: st.error("Credits low hain!")

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