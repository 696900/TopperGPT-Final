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
from supabase import create_client, Client
from datetime import datetime, timedelta
import math

# --- 🛠️ SILENT AI SETUP (The Bulletproof Version) ---
@st.cache_resource
def initialize_all_ai():
    api_key_gemini = st.secrets.get("VISION_ENTERPRISE_KEY") or st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    api_key_groq = st.secrets.get("GROQ_API_KEY")
    
    loaded_model = None
    loaded_groq_client = None

    if api_key_gemini:
        import google.generativeai as genai
        genai.configure(api_key=api_key_gemini)
        loaded_model = genai.GenerativeModel(
            model_name='gemini-1.5-flash', 
            generation_config={"temperature": 0.1}
        )
        
        from llama_index.embeddings.gemini import GeminiEmbedding
        from llama_index.core import Settings
        Settings.embed_model = GeminiEmbedding(
            model_name="models/text-embedding-004", 
            api_key=api_key_gemini
        )

    if api_key_groq:
        from llama_index.llms.groq import Groq as LlamaGroq
        from groq import Groq
        from llama_index.core import Settings
        
        Settings.llm = LlamaGroq(model="llama-3.3-70b-versatile", api_key=api_key_groq)
        loaded_groq_client = Groq(api_key=api_key_groq)
        
    return loaded_model, loaded_groq_client

model, groq_client = initialize_all_ai()

# ==========================================
# --- STEP 1: GLOBAL STABLE AI SETUP (FIXED) ---
# ==========================================
api_key_gemini = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if api_key_gemini:
    import google.generativeai as genai
    genai.configure(api_key=api_key_gemini)
    from llama_index.embeddings.gemini import GeminiEmbedding
    from llama_index.core import Settings
    Settings.embed_model = GeminiEmbedding(
        model_name="models/text-embedding-004", 
        api_key=api_key_gemini
    )

# --- 🛰️ SUPABASE CLOUD INITIALIZATION ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 🔐 TEST LOGIN LOGIC (Local-Only Mode for Lab Testing) ---
def handle_test_login():
    # Asli data early access ke waqt on karenge, abhi local session use karo
    st.session_state.user_data = {
        "email": "krishnaghanabahadur85@gmail.com",
        "name": "Krishna (Dev)",
        "credits": 100,
        "referral_code": "TOPTEST",
        "ref_claimed": False
    }
    return True

# --- 💎 REVENUE LOOP: MASTER CREDIT CHECKER ---
def use_credits(amount):
    """Checks and deducts credits locally during testing."""
    if "user_data" in st.session_state and st.session_state.user_data is not None:
        current_credits = st.session_state.user_data.get('credits', 0)
        if current_credits >= amount:
            st.session_state.user_data['credits'] -= amount
            return True
    return False

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="TopperGPT", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# 🖋️ PROFESSIONAL UI STYLES
EVAL_CSS = """
<style>
.block-container { max-width: 92% !important; padding-top: 2rem !important; }
.stApp { background-color: #0d1117 !important; color: #ffffff !important; }
[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
.wallet-card { 
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
    padding: 20px; border-radius: 15px; border: 1px solid #4CAF50; 
    text-align: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
.pay-card {
    background: #1c2128; border: 1px solid #30363d;
    padding: 12px; border-radius: 10px; margin-bottom: 10px;
    transition: 0.3s; cursor: pointer;
}
.pay-card:hover { border-color: #4CAF50; background: #22272e; }
.price-tag {
    background: #4CAF50; color: white; padding: 2px 8px; 
    border-radius: 5px; font-size: 13px; font-weight: bold;
}
</style>
"""
st.markdown(EVAL_CSS, unsafe_allow_html=True)

if "user_data" not in st.session_state: st.session_state.user_data = None

# --- 3. LOGIN PAGE (DIRECT BYPASS MODE) ---
if st.session_state.user_data is None:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    _, col_mid, _ = st.columns([1, 1.4, 1])
    
    with col_mid:
        import os
        if os.path.exists("logo.png"):
            st.image("logo.png", width=220)
        else:
            st.markdown("<h1 style='text-align: center; font-size: 80px;'>🎓</h1>", unsafe_allow_html=True)
            
        st.markdown('''
            <div style="text-align:center; padding:35px; background:#161b22; border-radius:20px; border:1px solid #4CAF50; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                <h1 style="color:#4CAF50; font-style:italic; margin:0; font-size: 38px;">TopperGPT</h1>
                <p style="color:#8b949e; letter-spacing: 2px; font-size: 11px; font-weight: bold;">UNIVERSITY RESEARCH PORTAL</p>
                <hr style="border-color:#30363d;">
                <p style="color:#ffffff; font-weight:500;">Bypass enabled for UI & Feature Testing.</p>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 Enter TopperGPT Lab", use_container_width=True):
            handle_test_login()
            st.rerun()
    st.stop()

# --- 4. SIDEBAR LAYOUT (ALL FEATURES RESTORED) ---
with st.sidebar:
    import os
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center;'>🎓</h1>", unsafe_allow_html=True)

    st.markdown("<h2 style='color: #4CAF50; margin-bottom:10px; font-style:italic; text-align: center;'>TopperGPT</h2>", unsafe_allow_html=True)
    
    # 💰 WALLET
    st.markdown(f'''
        <div class="wallet-card">
            <p style="margin:0; font-size:11px; color:#eab308; font-weight:bold; letter-spacing:1px;">AVAILABLE CREDITS</p>
            <h1 style="margin:5px 0; color:white; font-size:42px; font-weight:900;">{st.session_state.user_data["credits"]} 🔥</h1>
        </div>
    ''', unsafe_allow_html=True)

    # 🎁 REFER & EARN
    st.markdown("<p style='font-weight:bold; color:#4CAF50; font-size:14px; margin-top:20px;'>🎁 REFER & EARN FREE CREDITS</p>", unsafe_allow_html=True)
    with st.container():
        st.markdown(f'''
            <div style="background: rgba(76, 175, 80, 0.08); border: 2px dashed #4CAF50; padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 10px;">
                <p style="color: #c9d1d9; font-size: 13px; margin-bottom: 5px;">Share code. Both get <b>+5 Credits</b>!</p>
                <div style="background: #0d1117; padding: 10px; border-radius: 8px; border: 1px solid #30363d;">
                    <code style="color: #4CAF50; font-size: 18px; font-weight: bold;">{st.session_state.user_data['referral_code']}</code>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        if not st.session_state.user_data.get('ref_claimed', False):
            claim_input = st.text_input("Friend's Code?", placeholder="Enter TOPXXXX", key="ref_v201")
            if st.button("Claim My Bonus (+5)", use_container_width=True):
                clean_claim = claim_input.strip().upper()
                if clean_claim and clean_claim != st.session_state.user_data['referral_code']:
                    st.session_state.user_data['credits'] += 5
                    st.session_state.user_data['ref_claimed'] = True
                    st.balloons(); st.rerun()

    st.markdown("---")
    
    # 💎 RAZORPAY REFILL PACKS
    st.markdown("<p style='font-weight:bold; color:#4CAF50; font-size:14px; margin-bottom:15px;'>💎 REFILL YOUR CREDITS</p>", unsafe_allow_html=True)
    
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
                        <span style="color:white; font-weight:bold; font-size:14px;">{pack['name']}</span>
                        <span class="price-tag">{pack['price']}</span>
                    </div>
                    <p style="margin:5px 0 0 0; font-size:11px; color:#4CAF50; font-weight:bold;">
                        ✅ Get {pack['credits']} Instantly
                    </p>
                </div>
            </a>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔓 Exit Lab Mode", use_container_width=True):
        st.session_state.user_data = None; st.rerun()

# --- 💎 THE SLIM WELCOME BANNER ---
if st.session_state.get("user_data"):
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            padding: 10px 20px; border-radius: 10px; border: 1px solid #4CAF50;
            text-align: center; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
            display: flex; justify-content: space-between; align-items: center;
        ">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">🎓</span>
                <span style="color: white; font-weight: bold; font-size: 15px;">Welcome, <span style="color: #4CAF50;">{st.session_state.user_data.get('name', 'Topper')}!</span></span>
            </div>
            <div style="background: rgba(76, 175, 80, 0.1); padding: 5px 15px; border-radius: 20px; border: 1px solid #4CAF50;">
                <span style="color: white; font-weight: 800; font-size: 16px;">
                    {st.session_state.user_data['credits']} Credits
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 5. MAIN TABS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "💬 Chat PDF", "📊 AI EXAM WAR ROOM", "📝 Answer Eval", "🧠 MindMap", 
    "🃏 Flashcards", "❓ Engg PYQs", "🔍 Search", "🤝 Topper Connect", "⚖️ Legal"
])
## --- TAB 1: SMART NOTE ANALYSIS (STABLE VISION ENGINE) ---
# --- TAB 1: STABLE TEXT-BASED MENTOR (MOBILE OPTIMIZED) ---
with tab1:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>📚 Smart PDF Mentor (Stable)</h2>", unsafe_allow_html=True)
    
    # ✅ ADDED: Professional Warning for Users
    st.warning("⚠️ Note: Only Text-based PDFs are supported. Scanned images or handwritten PDFs will not work.")

    # 1. CLEAN PERSISTENT STATE
    if "master_docs" not in st.session_state: st.session_state.master_docs = {} 
    if "active_doc_key" not in st.session_state: st.session_state.active_doc_key = None

    # --- 🌍 LANGUAGE LOCK ---
    t_lang = st.radio("Response Language:", ["Mix (Hinglish)", "English", "Marathi-English"], horizontal=True, key="lang_v156")

    # --- 🔄 TOP SESSION SWITCHER (MOBILE FRIENDLY) ---
    if st.session_state.master_docs:
        st.markdown("### 📑 Switch PDF Session:")
        nav_cols = st.columns(len(st.session_state.master_docs) + 1)
        for i, d_name in enumerate(st.session_state.master_docs.keys()):
            with nav_cols[i]:
                b_type = "primary" if d_name == st.session_state.active_doc_key else "secondary"
                if st.button(f"📄 {d_name[:8]}..", key=f"nav_{d_name}", type=b_type, use_container_width=True):
                    st.session_state.active_doc_key = d_name
                    st.rerun()
        with nav_cols[-1]:
            if st.button("🗑️ Reset", type="primary", use_container_width=True):
                st.session_state.master_docs = {}; st.session_state.active_doc_key = None; st.rerun()
        st.markdown("---")

    # --- 📤 PDF ONLY UPLOADER ---
    u_file = st.file_uploader("Upload Exam PDF", type=["pdf"], key="pdf_only_v156")

    if u_file and u_file.name not in st.session_state.master_docs:
        with st.spinner(f"Reading {u_file.name}..."):
            import fitz
            doc = fitz.open(stream=u_file.read(), filetype="pdf")
            content = "".join([f"\n[Page {i+1}]\n{p.get_text()}" for i, p in enumerate(doc)])
            
            st.session_state.master_docs[u_file.name] = {"data": content, "history": []}
            st.session_state.active_doc_key = u_file.name
            st.rerun()

    # --- 💬 STABLE TEXT ENGINE (GROQ) ---
    if st.session_state.active_doc_key:
        active_key = st.session_state.active_doc_key
        session = st.session_state.master_docs[active_key]
        st.success(f"🎯 Currently Studying: **{active_key}**")
        
        for idx, m in enumerate(session["history"]):
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
                if m["role"] == "assistant":
                    if st.button(f"🔊 Listen", key=f"pod_{active_key}_{idx}"):
                        from gtts import gTTS
                        import io
                        a_lang = 'hi' if "Mix" in t_lang else ('mr' if "Marathi" in t_lang else 'en')
                        tts = gTTS(text=m["content"][:400], lang=a_lang)
                        b = io.BytesIO(); tts.write_to_fp(b); st.audio(b)

        if p := st.chat_input(f"Ask anything about {active_key}..."):
            if use_credits(1):
                session["history"].append({"role": "user", "content": p})
                with st.chat_message("user"): st.markdown(p)

                with st.chat_message("assistant"):
                    try:
                        from groq import Groq
                        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                        sys_msg = f"Tu Expert Professor hai. {t_lang} mein jawab de. Context: {session['data'][:30000]}"
                        chat_res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": p}]
                        )
                        ans = chat_res.choices[0].message.content
                        st.markdown(ans)
                        session["history"].append({"role": "assistant", "content": ans})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Backend Busy. Please try again in 5 seconds.")
    else:
        st.info("Pehle koi PDF upload karo taaki hum padhai shuru kar sakein!")
# ==========================================
# --- TAB 2: AI EXAM WAR ROOM (STABLE V35) ---
# ==========================================
with tab2:
    # --- HELPER FUNCTIONS ---
    def get_readiness_label(r):
        if r < 40: return "🔴 CRITICAL"
        if r < 75: return "🟡 MODERATE"
        return "🟢 BATTLE READY"

    # --- 1. CLOUD SYNC & VAULT ---
    if 'war_room_vault' not in st.session_state:
        st.session_state.war_room_vault = st.session_state.user_data.get('war_room_data', {}) if st.session_state.user_data else {}

    top_h1, top_h2 = st.columns([0.7, 0.3])
    # Subject Switching Logic
    active_station = top_h1.selectbox("📂 Select Battle Station:", ["+ Deploy New Strategy"] + list(st.session_state.war_room_vault.keys()))
    
    if top_h2.button("💾 Master Sync", use_container_width=True):
        try:
            supabase.table("profiles").update({"war_room_data": st.session_state.war_room_vault}).eq("email", st.session_state.user_data['email']).execute()
            st.toast("Strategy Locked to Cloud! ☁️")
        except: st.error("Sync Failed.")

    st.divider()

    # --- 2. DASHBOARD ENGINE ---
    if active_station != "+ Deploy New Strategy":
        wr = st.session_state.war_room_vault.get(active_station, {})
        
        # Readiness Tracking Logic
        topics_data = wr.get('topics', [])
        total_m = sum(t.get('marks', 10) for t in topics_data) if topics_data else 100
        done_m = sum(t.get('marks', 10) for t in topics_data if t.get('done')) if topics_data else 0
        readiness = int((done_m / total_m) * 100) if total_m > 0 else 0

        # UI: HEADER
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 25px; border-radius: 20px; border: 1px solid #ef4444; margin-bottom: 25px;">
                <h2 style="color: #ef4444; margin: 0; font-size: 28px;">BATTLE PLAN: {active_station.upper()}</h2>
                <p style="color: #94a3b8; margin: 0;">Ready to Slay {wr.get('subject')} | Readiness: {readiness}%</p>
            </div>
        """, unsafe_allow_html=True)

        # GRID: STATS & MATRIX
        c_g, c_mx = st.columns([0.45, 0.55])
        with c_g:
            g_color = "#ef4444" if readiness < 40 else "#f59e0b" if readiness < 75 else "#10b981"
            st.markdown(f"""
                <div style="background: #1e293b; padding: 25px; border-radius: 20px; border: 1px solid #334155; text-align: center; height: 350px;">
                    <p style="color: #94a3b8; font-weight: bold;">PASS PROBABILITY</p>
                    <svg width="150" height="150" viewBox="0 0 160 160">
                        <circle cx="80" cy="80" r="70" fill="none" stroke="#0f172a" stroke-width="12" />
                        <circle cx="80" cy="80" r="70" fill="none" stroke="{g_color}" stroke-width="12" 
                            stroke-dasharray="440" stroke-dashoffset="{440 - (440 * readiness) / 100}" 
                            stroke-linecap="round" />
                    </svg>
                    <div style="margin-top: -100px;">
                        <div style="color: white; font-size: 35px; font-weight: 900;">{readiness}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c_mx:
            mx = wr.get('matrix', {})
            st.markdown(f"""
                <div style="background: #1e293b; padding: 25px; border-radius: 20px; border: 1px solid #334155; height: 350px;">
                    <p style="color: #4f46e5; font-weight: bold;">📊 STRATEGY MATRIX</p>
                    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                        <b style="color: #10b981;">🚀 QUICK WINS:</b> <span style="color:white;">{mx.get('quick_wins', 'Wait...')}</span>
                    </div>
                    <div style="background: rgba(79, 70, 229, 0.1); border: 1px solid #4f46e5; border-radius: 10px; padding: 12px;">
                        <b style="color: #4f46e5;">💎 BIG ROCKS:</b> <span style="color:white;">{mx.get('big_rocks', 'Wait...')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # --- ROADMAP & MISSIONS (Restore logic) ---
        st.markdown("<br>### ⚔️ Detailed Battle Roadmap", unsafe_allow_html=True)
        for phase in wr.get('phases', []):
            with st.expander(f"📍 {phase['name']} ({phase.get('days_range')})", expanded=True):
                st.write(phase.get('desc'))
                for t in phase.get('topics', []): st.markdown(f"🔹 {t}")

        # --- MISSION CHECKLIST (MCQ SYSTEM) ---
        st.markdown("<br>### 🎯 Mission Checklist (+2 Credits)", unsafe_allow_html=True)
        for idx, m in enumerate(wr.get('missions', [])):
            with st.container():
                cols = st.columns([0.05, 0.8, 0.15])
                cols[0].markdown("✅" if m.get('done') else f"### {idx+1}")
                strike = "text-decoration: line-through; color: #475569;" if m.get('done') else ""
                cols[1].markdown(f"<div style='{strike}'><b style='font-size: 18px;'>{m['task']}</b><br><small>Marks: {m.get('marks')}</small></div>", unsafe_allow_html=True)
                
                if not m.get('done'):
                    if cols[2].button("Quiz", key=f"q_final_{idx}"):
                        with st.spinner("Analyzing PYQ..."):
                            try:
                                q_p = f"Technical MCQ on {m['task']}. JSON ONLY: {{\"question\": \"...\", \"options\": [\"A: x\", \"B: y\", \"C: z\", \"D: w\"], \"answer\": \"A\"}}"
                                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": q_p}], response_format={"type": "json_object"})
                                st.session_state.active_mcq = json.loads(res.choices[0].message.content)
                                st.session_state.active_mcq_meta = {"sub": active_station, "idx": idx}
                                st.rerun()
                            except: st.error("AI Busy. Try again.")

    else:
        # --- NEW MISSION DEPLOYMENT (ANTI-SCAM LOGIC) ---
        st.markdown("### Deploy AI Exam Strategist")
        st.info("💡 Strategy costs 5 Credits. **No charge on Error!**")
        c1, c2, c3 = st.columns(3)
        u_sel = c1.selectbox("University", ["Mumbai University", "SPPU", "GTU", "AKTU", "Other"])
        branch = c2.selectbox("Branch", ["Computer", "IT", "Mechanical", "Civil", "Extc", "AI/DS"])
        s_name = c3.text_input("Subject")
        days = st.number_input("Days", 1, 30, 10)

        if st.button("🔥 GENERATE BRAHMASTRA PLAN"):
            if st.session_state.user_data['credits'] >= 5:
                with st.spinner("Gemini drafting strategy (Verifying Stability)..."):
                    try:
                        # 1. AI GENERATION PHASE (BEFORE DEDUCTION)
                        g_p = f"Uni: {u_sel}, Branch: {branch}, Subject: {s_name}, Days: {days}. Analyze 5y PYQs. Return ONLY JSON: {{\"matrix\": {{\"quick_wins\": \"...\", \"big_rocks\": \"...\"}}, \"phases\": [{{ \"name\": \"P1\", \"days_range\": \"1-3\", \"desc\": \"info\", \"topics\": [\"T1\"] }}], \"topics\": [{{\"name\": \"T1\", \"marks\": 10}}], \"missions\": [{{\"task\": \"T1\", \"marks\": \"10M\"}}]}}"
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(g_p)
                        
                        # Clean JSON strings
                        clean_json = response.text.replace('```json', '').replace('```', '').strip()
                        strategy = json.loads(clean_json)

                        # 2. VERIFICATION & DEDUCTION PHASE (Only if AI is successful)
                        st.session_state.user_data['credits'] -= 5
                        supabase.table("profiles").update({"credits": st.session_state.user_data['credits']}).eq("email", st.session_state.user_data['email']).execute()
                        
                        # 3. SAVE TO SESSION
                        st.session_state.war_room_vault[s_name] = {
                            "university": u_sel, "branch": branch, "subject": s_name, "days_left": days,
                            "matrix": strategy.get('matrix', {}), "phases": strategy.get('phases', []),
                            "topics": [{**t, "done": False} for t in strategy.get('topics', [])],
                            "missions": [{**m, "done": False} for m in strategy.get('missions', [])]
                        }
                        st.balloons(); st.rerun()
                    except Exception as e:
                        # NO CREDITS DEDUCTED ON FAILURE
                        st.error(f"AI Error: Drafting Failed. No credits were charged. Try clicking Generate once more!")
            else:
                st.error("Insufficient Credits!")
    # --- TAB 3: ANSWER EVALUATOR ---
# --- TAB 3: CINEMATIC BOARD MODERATOR (ZERO-ERROR TEXT ENGINE) ---
# --- TAB 3: ENTERPRISE EVALUATOR (GOOGLE CLOUD VISION) ---
with tab3:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🖋️ TopperGPT: Official Moderator</h2>", unsafe_allow_html=True)
    
    eval_cost = 5
    if "extracted_text" not in st.session_state: st.session_state.extracted_text = None
    if "eval_result" not in st.session_state: st.session_state.eval_result = None

    ans_file = st.file_uploader("Upload Answer Sheet Photo", type=["jpg", "png", "jpeg"], key="gcv_final_fix")
    
    if ans_file:
        img_raw = Image.open(ans_file).convert("RGB")
        st.image(img_raw, caption="Answer Sheet Detected", width=350)

        if not st.session_state.extracted_text:
            if st.button(f"🔍 Scan Handwriting ({eval_cost} Credits)"):
                if use_credits(eval_cost):
                    placeholder = st.empty()
                    placeholder.info("🚀 Connecting to Google Enterprise Servers...")
                    
                    try:
                        # ✅ KEY LOGIC
                        api_key_vision = st.secrets.get("VISION_ENTERPRISE_KEY") or st.secrets.get("GEMINI_API_KEY")
                        
                        if not api_key_vision:
                            raise Exception("API Key missing! Check Streamlit Secrets.")

                        img_byte_arr = io.BytesIO()
                        img_raw.save(img_byte_arr, format='JPEG', quality=90)
                        content = img_byte_arr.getvalue()

                        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key_vision}"
                        payload = {
                            "requests": [{
                                "image": {"content": base64.b64encode(content).decode('utf-8')},
                                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
                            }]
                        }
                        
                        response = requests.post(url, json=payload, timeout=20)
                        data = response.json()
                        
                        if 'error' in data:
                            msg = data['error'].get('message', '')
                            if "billing" in msg.lower():
                                raise Exception("Billing account not linked. Enable it in Google Console.")
                            raise Exception(msg)

                        texts = data['responses'][0].get('fullTextAnnotation', {}).get('text', "")
                        
                        if texts:
                            st.session_state.extracted_text = texts
                            placeholder.success("✅ Enterprise Scan Successful!")
                            st.rerun()
                        else:
                            raise Exception("Google Vision text nahi padh paa raha. Photo clear khicho!")

                    except Exception as e:
                        st.session_state.user_data['credits'] += eval_cost # Refund
                        st.error(f"❌ Scan Failed: {str(e)}")
                else:
                    st.error("Bhai credits khatam!")

    # --- BRAIN SECTION (MARKING LOGIC) ---
    if st.session_state.extracted_text and not st.session_state.eval_result:
        st.markdown("### 📝 Scanned Content")
        edited_text = st.text_area("Final Review:", value=st.session_state.extracted_text, height=200)
        
        if st.button("📝 Finalize & Grade"):
            with st.spinner("AI Professor is marking..."):
                try:
                    marking_prompt = f"""Evaluate this answer (Out of 10). Return JSON with 'marks' and 'feedback'.
                    Answer: {edited_text}"""
                    
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": marking_prompt}],
                        response_format={"type": "json_object"}
                    )
                    st.session_state.eval_result = json.loads(res.choices[0].message.content)
                    st.rerun()
                except Exception:
                    st.error("Marking Engine busy.")

    # --- SCORECARD ---
    if st.session_state.eval_result:
        res = st.session_state.eval_result
        st.success(f"### SCORE: {res.get('marks', 0)}/10")
        st.info(f"**Feedback:** {res.get('feedback', '')}")
        if st.button("🔄 New Scan"):
            st.session_state.extracted_text = None
            st.session_state.eval_result = None
            st.rerun()
# --- TAB 4: CONCEPT MINDMAP ARCHITECT (REVENUE SYNCED) ---
# --- TAB 4: CONCEPT MINDMAP (V156 - WATERMARK EDITION) ---
with tab4:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🎨 Deep Concept Architect (Topper Edition)</h2>", unsafe_allow_html=True)

    incoming_topic = st.session_state.get('active_topic', "")
    col_in, col_opt = st.columns([0.7, 0.3])

    with col_in:
        mm_input = st.text_input("Concept Name:", value=incoming_topic, key="mm_v139", placeholder="e.g. PN Junction Diode")
    with col_opt:
        use_pdf = st.checkbox("Deep PDF Scan", value=True if st.session_state.get('current_index') else False)

    mm_cost = 2

    if st.button(f"🚀 Generate Deep Technical Map ({mm_cost} Credits)"):
        if len(mm_input.strip()) < 3:
            st.error("❌ Topic bohot chota hai. Please ek valid engineering topic dalo.")
        else:
            if use_credits(mm_cost):
                with st.spinner("Decoding technical depths for full marks..."):
                    try:
                        context = ""
                        if use_pdf and st.session_state.get('current_index'):
                            qe = st.session_state.current_index.as_query_engine(similarity_top_k=5)
                            context_res = qe.query(f"Explain {mm_input} like a textbook: working physics, internal mechanisms, and core components.")
                            context = f"PDF Context: {context_res.response}"

                        # ✅ MASTER PROMPT: Strictly forcing EXPLAINED TECHNICAL CONTENT & VALIDATION
                        prompt = f"""
                        Act as an Engineering Professor. Task: Create a Mermaid flowchart for: '{mm_input}'. 
                        
                        VALIDATION: If '{mm_input}' is nonsense, a single letter, or non-educational, return ONLY 'INVALID_TOPIC'.
                        
                        Rules for "Bible" Quality:
                        1. Start with 'graph LR'.
                        2. ROOT is 'ROOT(({mm_input}))'.
                        3. Branches: 'DEF["Definition"]', 'WORK["Working Mechanism"]', 'COMP["Key Components"]', 'APP["Applications"]'.
                        4. Each sub-node MUST connect deeply and EXPLAIN the term.
                        5. IMPORTANT: All labels MUST be inside double quotes "". Example: NODE["Term: 1-line explanation"].
                        6. Connect sub-nodes in levels: DEF --> D1["..."], WORK --> W1["..."] --> W2["..."].
                        7. Context: {context}
                        8. Output ONLY code or 'INVALID_TOPIC'. No markdown backticks.
                        """

                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}]
                        )

                        raw_output = res.choices[0].message.content.strip()
                        
                        if "INVALID_TOPIC" in raw_output.upper():
                            st.session_state.user_data['credits'] += mm_cost
                            st.error(f"❌ '{mm_input}' koi valid engineering topic nahi lag raha. Credits Refunded.")
                        else:
                            clean_code = raw_output.replace("```mermaid", "").replace("```", "").strip()
                            if not clean_code.startswith("graph"): clean_code = "graph LR\n" + clean_code

                            vibrant_styles = """
                            classDef default fill:#1c2128,stroke:#4CAF50,color:#fff;
                            classDef defStyle fill:#1e3c72,stroke:#fff,color:#fff,stroke-width:2px;
                            classDef workStyle fill:#2a5298,stroke:#eab308,color:#fff,stroke-width:2px;
                            classDef compStyle fill:#4CAF50,stroke:#fff,color:#fff,stroke-width:2px;
                            classDef appStyle fill:#eab308,stroke:#1c2128,color:#1c2128,font-weight:bold;
                            class DEF,Definition defStyle; class WORK,Working workStyle; class COMP,Components compStyle; class APP,Applications appStyle;
                            """
                            st.session_state.last_mm_code = clean_code + "\n" + vibrant_styles
                            st.rerun()

                    except Exception as e:
                        st.session_state.user_data['credits'] += mm_cost
                        st.error(f"Logic Error: {e}")

    # --- 🎭 THE RENDERER: AUTO-FIT & ZOOM VERSION (WITH WATERMARK) ---
    if "last_mm_code" in st.session_state:
        st.markdown("---")
        st.info("📸 **Topper Tip:** Background mein watermark added hai. Download button poora diagram capture karega.")
        
        import streamlit.components.v1 as components
        
        # Updated HTML with Watermark Overlay
        html_code = f"""
        <div id="wrapper" style="position: relative; background:#0d1117; border-radius:15px; border:2px solid #4CAF50; width:100%; height:600px; overflow: hidden;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); 
                        font-size: 80px; color: rgba(255, 255, 255, 0.05); font-weight: 900; pointer-events: none; white-space: nowrap; z-index: 0;">
                TOPPERGPT • TOPPERGPT • TOPPERGPT
            </div>
            
            <div id="graphDiv" style="position: relative; cursor: grab; width:100%; height:100%; z-index: 1;">
                </div>
        </div>
        <br>
        <button id="downloadBtn" style="background:#4CAF50; color:white; border:none; padding:12px 20px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%; font-size:16px;">
            📥 Download Full HD MindMap (SVG)
        </button>

        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            
            mermaid.initialize({{ 
                startOnLoad: false, 
                theme: 'dark', 
                securityLevel: 'loose', 
                flowchart: {{ useMaxWidth: true, htmlLabels: true, curve: 'basis' }}
            }});
            
            const graphDefinition = `{st.session_state.last_mm_code}`;
            const graphDiv = document.getElementById('graphDiv');

            try {{
                const {{ svg }} = await mermaid.render('mermaid-svg-v2', graphDefinition);
                graphDiv.innerHTML = svg;
                
                const svgElement = graphDiv.querySelector('svg');
                svgElement.style.width = '100%';
                svgElement.style.height = '100%';
                svgElement.setAttribute('preserveAspectRatio', 'xMidYMid meet');
            }} catch (e) {{
                graphDiv.innerHTML = "<p style='color:red; padding:20px;'>Render Error. Try a simpler topic.</p>";
            }}

            document.getElementById('downloadBtn').addEventListener('click', () => {{
                const svgData = graphDiv.innerHTML;
                const blob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'TopperGPT_Watermarked_Map.svg';
                link.click();
                URL.revokeObjectURL(url);
            }});
        </script>
        """
        components.html(html_code, height=700, scrolling=False)
    # --- TAB 5: FLASHCARDS (STRICT TOPIC LOCK) ---
# --- TAB 5: TOPPERGPT CINEMATIC CARDS (STRICT SYLLABUS MODE) ---
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
                    # ✅ UPDATED: Added Strict Engineering Professor Context
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a strict Engineering Professor. Create 10 precise flashcards based ONLY on university syllabus and standard engineering textbooks. Ensure technical accuracy for exam scoring. Format: TITLE | One line technical definition. Max 15 words. NO bold stars."},
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
                    st.download_button(f"📥 Download HD {i+1}", card_img, f"TopperCard_{i+1}.png", "image/png", use_container_width=True, key=f"dl_{i}")
                with c2:
                    wa_url = f"https://wa.me/?text=Bhai ye dekh {title} ka revision card! Pehle download kar fir status par laga le."
                    st.markdown(f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><div style="background:#25D366; color:white; text-align:center; padding:10px; border-radius:10px; font-weight:bold; font-size: 0.9rem;">📲 Share on WA</div></a>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)

            except: continue

        if st.button("🗑️ Clear Deck"):
            st.session_state.flash_cards_list = None
            st.rerun()
    # --- TAB 6: UNIVERSITY VERIFIED PYQS (RESTORED) ---
# --- TAB 6: UNIVERSITY VERIFIED PYQS (STRICT EXAM MODE) ---
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

    subj_name = st.text_input("Enter Subject Name:", key="pyq_sub_v2", placeholder="e.g. Applied Mathematics-II")

    # 💰 Cost for University Research
    pyq_cost = 1

    if st.button(f"🔍 Fetch Important PYQs ({pyq_cost} Credit)"):
        if subj_name:
            # --- START REVENUE LOOP ---
            if use_credits(pyq_cost):
                with st.spinner(f"Analyzing {univ} Exam Patterns..."):
                    # ✅ UPDATED PROMPT: Based on Credibility & Pattern Analysis
                    prompt = f"""
                    You are a Senior Academic Moderator for {univ}. 
                    Subject: {subj_name} for {branch} Engineering, {semester}.
                    
                    STRICT INSTRUCTIONS:
                    1. List 5 High-Priority Topics that have appeared MOST FREQUENTLY in the last 10 years.
                    2. Identify 5 specific recurring questions with their Year/Marks reference.
                    3. Provide 3 'High Probability' topics for practice based on historical weightage trends.
                    4. Format: [Topic/Question] - (Pattern Frequency: X times, Average Marks: Y).
                    
                    IMPORTANT: Do NOT use words like 'Sure-Shot', 'Guaranteed', or 'Exact Prediction'. 
                    Focus on 'Historical Patterns' and 'High Probability'.
                    """
                    
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
        st.success(f"Exam Pattern Analysis for {st.session_state.pyq_subject_last}")
        
        # Displaying with a nice clean box + DISCLAIMER
        st.markdown(f"""
        <div style="background: #1c2128; border: 1px solid #4CAF50; padding: 25px; border-radius: 12px; line-height: 1.6;">
            {st.session_state.pyq_result}
            <br><br>
            <hr style="border-color: #30363d;">
            <p style="font-size: 11px; color: #8b949e; font-style: italic; margin-top: 10px;">
                ⚠️ <b>Disclaimer:</b> This analysis is based on historical exam patterns and trends. 
                TopperGPT does not guarantee that these exact questions will appear in the upcoming exam. 
                Students are strongly advised to study the entire syllabus.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Download Pattern Analysis (TXT)",
            data=st.session_state.pyq_result,
            file_name=f"{st.session_state.pyq_subject_last}_Analysis.txt",
            use_container_width=True
        )
        
        if st.button("🗑️ Clear Results"):
            st.session_state.pyq_result = None
            st.rerun()
    # --- TAB 7: ADVANCED TOPIC SEARCH (FINAL COLLEGE FIX) ---
# --- TAB 7: TOPIC SEARCH (THE ULTIMATE BULLETPROOF VERSION) ---
# --- TAB 7: TOPIC RESEARCH (STRICT PROFESSOR MODE - V161 FIX) ---
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
    from datetime import datetime
    exam_date = col_d.date_input("Target Exam Date", key="roadmap_date_v1")
    
    if st.button("Deep Research", key="btn_absolute_v1") and query:
        if st.session_state.user_data['credits'] >= search_cost:
            with st.spinner(f"PhD Mentor is analyzing '{query}'..."):
                # ✅ MASTER PROMPT FIX: Strictly forcing double quotes for Graphviz labels to prevent Syntax Errors
                prompt = f"""
                Act as a PhD Engineering Professor. Provide an academically accurate report for: '{query}'.
                Use these markers exactly:
                [1_DEF] technical definition (University Standard).
                [2_KEY] 7-10 essential technical keywords.
                [3_CXP] detailed technical working with step-by-step logic.
                [4_SMP] simple conceptual summary.
                [5_DOT] ONLY Graphviz DOT code (digraph G {{...}}). 
                STRICT RULE FOR [5_DOT]: Every node label MUST be inside double quotes like [label="My Label"]. 
                Do NOT use special characters outside quotes.
                [6_PYQ] at least 15 ACTUAL exam questions from MU, SPPU, and GTU archives.
                """
                try:
                    # Revenue deduction happens before call, but we wrap in try-except for safety
                    if use_credits(search_cost):
                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile", 
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.session_state.research_data = res.choices[0].message.content
                        st.session_state.research_query = query
                        st.rerun()
                except Exception as e: 
                    # Refund logic in case of API failure
                    st.session_state.user_data['credits'] += search_cost
                    st.error(f"System Busy. Error: {e}")
        else:
            st.error("Bhai credits khatam! Sidebar se recharge karle.")

    if st.session_state.research_data:
        out = st.session_state.research_data
        q_name = st.session_state.research_query

        def get_sec(m1, m2=None):
            try:
                parts = out.split(m1)
                if len(parts) < 2: return "Data missing."
                content = parts[1]
                if m2 and m2 in content: content = content.split(m2)[0]
                # Cleaning common AI code block kachra
                return content.strip().replace("```dot", "").replace("```", "").replace("```gv", "")
            except: return "Section error."

        st.markdown(f"## 📘 Technical Report: {q_name}")
        st.info(f"**1. University Standard Definition:**\n\n{get_sec('[1_DEF]', '[2_KEY]')}")
        
        c1, c2 = st.columns(2)
        with c1: st.write(f"**2. Essential Keywords (Exam Scoring):**\n\n{get_sec('[2_KEY]', '[3_CXP]')}")
        with c2: st.success(f"**4. Simple Concept Summary:**\n\n{get_sec('[4_SMP]', '[5_DOT]')}")
        
        st.warning(f"**3. Technical Breakdown & Working:**\n\n{get_sec('[3_CXP]', '[4_SMP]')}")

        # --- HD GRAPHVIZ FLOWCHART (SYNTAX ERROR PROTECTED) ---
        st.markdown("---")
        st.markdown("### 📊 5. Architecture Flowchart (Graphviz HD)")
        dot_code = get_sec('[5_DOT]', '[6_PYQ]')
        if "digraph" in dot_code:
            try:
                st.graphviz_chart(dot_code, use_container_width=True)
            except Exception:
                st.error("Visualization syntax error. Try clicking Research again.")
        else:
            st.info("Generating architecture visuals...")
        
        st.markdown("---")
        st.markdown("### ❓ 6. Expected Exam Questions (15+ Verified PYQs)")
        st.write(get_sec('[6_PYQ]'))

        # --- PREMIUM ROADMAP VIEW ---
        st.markdown("---")
        st.markdown("### 📅 Personalized 360° Study Roadmap")
        days_left = (exam_date - datetime.now().date()).days
        
        if st.button(f"Generate Plan for {days_left} Days ({roadmap_cost} Credits)"):
            if st.session_state.user_data['credits'] >= roadmap_cost:
                if use_credits(roadmap_cost):
                    with st.spinner("AI Mentor is creating your battle plan..."):
                        rm_prompt = f"Create a strict day-by-day engineering study schedule for: {q_name}. Total days available: {days_left}. Focus on high-weightage areas. Use 'Day X:' format."
                        rm_res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": rm_prompt}]
                        )
                        st.success("Custom Study Plan Ready!")
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
            else: st.error("Credits low hain! Top-up karlo.")

        if st.button("🗑️ Clear Research"):
            st.session_state.research_data = None
            st.rerun()
# --- TAB 8: TOPPER CONNECT (WORKING LOGIC) ---
with tab8:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🤝 Toppers Connect (Live)</h2>", unsafe_allow_html=True)
    st.markdown("<i>Real-time networking & resource sharing for MU students.</i>", unsafe_allow_html=True)

    # 🔥 STEP 1: FIREBASE URL
    FB_URL = "https://topper-connect-default-rtdb.asia-southeast1.firebasedatabase.app/"

    # --- 📊 LIVE METRICS SECTION ---
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Online Now", "142")
    m_col2.metric("Doubts Solved", "1.3K")
    
    # ✅ DYNAMIC XP DISPLAY: Ab session state se real XP uthayega
    current_user_xp = st.session_state.user_data.get('xp', 0) if st.session_state.user_data else 0
    m_col3.metric("Community Karma", f"{current_user_xp} XP") 
    st.divider()

    # --- 🎯 SQUAD SELECTION ---
    squad_options = ["🌐 General", "🔢 Maths Squad", "💻 Coding Masters", "📜 MU Updates", "🎁 Resource Swap"]
    selected_group = st.radio("Select Your Squad:", squad_options, horizontal=True, key="live_squad_v3.1")
    
    clean_name = selected_group.split(" ")[1].lower() if " " in selected_group else "general"
    db_path = f"{clean_name}_squad"

    # --- 📂 RESOURCE SWAP SPECIAL FEATURE ---
    if "Resource" in selected_group:
        st.info("📤 **Resource Swap:** Yahan apne notes ya PDF share karo!")
        uploaded_file = st.file_uploader("Upload Notes (PDF/Img)", type=['pdf', 'png', 'jpg', 'jpeg'])
        if uploaded_file:
            if st.button("🚀 Share to Community"):
                file_msg = f"📂 Shared a Resource: {uploaded_file.name} (Ready to download)"
                requests.post(f"{FB_URL}/chats/{db_path}.json", data=json.dumps({"user": "You", "msg": file_msg}))
                st.success("File shared successfully!")
                st.rerun()

    # --- 💬 CHAT ENGINE ---
    chat_container = st.container(height=450, border=True)
    
    with chat_container:
        try:
            response = requests.get(f"{FB_URL}/chats/{db_path}.json")
            messages = response.json() if response.json() else {}
            
            if not messages:
                st.info(f"Welcome to {selected_group}! Be the first to start. 🚀")
            else:
                for m_id, m_data in messages.items():
                    role = "assistant" if m_data['user'] == "TopperGPT" else "user"
                    avatar = "🦁" if role == "assistant" else "👨‍🎓"
                    with st.chat_message(role, avatar=avatar):
                        st.markdown(f"**{m_data['user']}**: {m_data['msg']}")
        except:
            st.warning("Connecting to community server...")

    # --- ⌨️ INPUT & AI AUTO-MODERATOR (WITH REWARD LOOP) ---
    st.markdown("---")
    if u_input := st.chat_input(f"Message in {selected_group}..."):
        # 1. Post User Message
        requests.post(f"{FB_URL}/chats/{db_path}.json", data=json.dumps({"user": "You", "msg": u_input}))
        
        # 🌟 NEW: Karma (XP) Reward Logic
        if st.session_state.user_data:
            email_clean = st.session_state.user_data['email'].replace(".", "_")
            old_xp = st.session_state.user_data.get('xp', 0)
            new_xp = old_xp + 2 # +2 XP per message
            
            # Update Firebase & Session State
            try:
                requests.patch(f"{FB_URL}/users/{email_clean}.json", data=json.dumps({"xp": new_xp}))
                st.session_state.user_data['xp'] = new_xp
                
                # 🎁 Milestone Gift: Har 100 XP pe +5 Credits
                if new_xp > 0 and new_xp % 100 == 0:
                    old_credits = st.session_state.user_data.get('credits', 0)
                    new_credits = old_credits + 5
                    requests.patch(f"{FB_URL}/users/{email_clean}.json", data=json.dumps({"credits": new_credits}))
                    st.session_state.user_data['credits'] = new_credits
                    st.toast("🎁 Mastery Reward: +5 Free Credits for helping the community!", icon="🔥")
            except:
                pass

        # 2. Trigger AI
        trigger_words = ["?", "how", "what", "explain", "kya", "kaise", "batao"]
        if any(word in u_input.lower() for word in trigger_words):
            with st.spinner("TopperGPT is typing..."):
                try:
                    ai_prompt = f"Act as a Mumbai University Topper. Answer this student's doubt concisely: {u_input}"
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": ai_prompt}]
                    )
                    ai_reply = res.choices[0].message.content
                    requests.post(f"{FB_URL}/chats/{db_path}.json", data=json.dumps({"user": "TopperGPT", "msg": ai_reply}))
                except:
                    pass
        st.rerun()

    # --- 🏆 GAMIFICATION WIDGET ---
    with st.expander("🎖️ Top Contributors"):
        st.caption("Help others to earn Karma (Contribution Credits)!")
        st.write("1. 🥇 **Rahul.MU** - 540 XP")
        st.write("2. 🥈 **Sneha_IT** - 420 XP")
        # Yahan tera real XP dikhega
        st.write(f"3. 🥉 **You** - {current_user_xp} XP")
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