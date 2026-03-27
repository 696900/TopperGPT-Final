import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
from PIL import Image, ImageDraw, ImageFont
import io
import time 
import razorpay
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
from groq import Groq # Direct import for MindMap Fix

# --- 1. CONFIGURATION (STRICTLY FIRST) ---
st.set_page_config(page_title="TopperGPT Dashboard", layout="wide", page_icon="🚀")

# Initialize global variable for MindMap in session state to fix "groq_client not defined"
if "groq_client" not in st.session_state:
    st.session_state.groq_client = None

# --- 🛰️ SUPABASE CLOUD INITIALIZATION ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()
# --- 💳 ZERO-WEBHOOK AUTOMATIC SYNC MACHINE ---
def sync_topper_credits():
    # Only run if user is logged in
    if "user_data" not in st.session_state or st.session_state.user_data is None:
        return

    try:
        # Client setup using your secrets
        client = razorpay.Client(auth=(st.secrets["RAZORPAY_KEY_ID"], st.secrets["RAZORPAY_KEY_SECRET"]))
        u_email = st.session_state.user_data['email']

        # 1. Fetch last 10 successful payments from Razorpay
        payments = client.payment.all({'count': 10})

        for p in payments['items']:
            # Check if payment belongs to this user and is successful
            if p['email'] == u_email and p['status'] == 'captured':
                p_id = p['id']
                # Amount is in paise (e.g., 5900 = 59 INR)
                amount = p['amount'] / 100 

                # 2. Check Database: Kya ye payment ID pehle process ho chuki hai?
                check = supabase.table("payments").select("*").eq("payment_id", p_id).execute()

                if not check.data:
                    # 3. New Payment Found! Match with your Packs
                    credits_bonus = 0
                    if 55 <= amount <= 65: credits_bonus = 70    # Sureshot Pack (59)
                    elif 95 <= amount <= 105: credits_bonus = 150 # Jugaad Pack (99)
                    elif 145 <= amount <= 155: credits_bonus = 350 # Topper Pro (149)

                    if credits_bonus > 0:
                        # Update Profile Credits in Supabase
                        current_c = st.session_state.user_data.get('credits', 0)
                        new_total = current_c + credits_bonus
                        supabase.table("profiles").update({"credits": new_total}).eq("email", u_email).execute()

                        # Log payment so it's never reused (Security)
                        supabase.table("payments").insert({
                            "payment_id": p_id, 
                            "email": u_email, 
                            "amount": amount, 
                            "status": "processed"
                        }).execute()

                        # Update UI State
                        st.session_state.user_data['credits'] = new_total
                        st.toast(f"✅ Auto-Sync: {credits_bonus} Credits Added!", icon="🔥")
                        time.sleep(1)
                        st.rerun()
    except Exception as e:
        # Silent fail to keep app running smoothly
        pass
# --- 🛠️ SILENT AI SETUP (FIXED FOR NONETYPE ERROR) ---
@st.cache_resource
def initialize_all_ai():
    api_key_gemini = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    api_key_groq = st.secrets.get("GROQ_API_KEY")
    
    # 1. Gemini Configuration
    if api_key_gemini:
        genai.configure(api_key=api_key_gemini)
        Settings.embed_model = GeminiEmbedding(model_name="models/text-embedding-004", api_key=api_key_gemini)

    # 2. Groq Configuration (Llama Index Settings)
    if api_key_groq:
        Settings.llm = LlamaGroq(model="llama-3.3-70b-versatile", api_key=api_key_groq)
    
    return genai.GenerativeModel('gemini-1.5-flash') if api_key_gemini else None

# Run Initialization
model = initialize_all_ai()

# --- 🚀 CRITICAL FIX: Session State Sync ---
# Ye part ensure karega ki groq_client kabhi None na ho
if "groq_client" not in st.session_state or st.session_state.groq_client is None:
    api_key_groq = st.secrets.get("GROQ_API_KEY")
    if api_key_groq:
        from groq import Groq # Ensure import is there
        st.session_state.groq_client = Groq(api_key=api_key_groq)

# Global variable for all tabs
groq_client = st.session_state.get("groq_client")

# --- 🔐 THE "NO-PASSWORD" SUPER FAST AUTH ENGINE ---
def clean_email_auth():
    if "user_data" not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        st.markdown(f"""
            <div style="text-align:center; padding: 10px;">
                <div style="font-size: 80px; margin-bottom: 0;">🎓</div>
                <h1 style="color:#4CAF50; font-size: 3.5rem; margin-bottom:0;">TopperGPT</h1>
                <p style="color:#8b949e; margin-top:0; font-weight:bold;">Precision Engineering Intelligence Dashboard</p>
            </div>
        """, unsafe_allow_html=True)

        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            auth_tab = st.tabs(["🔑 Quick Login", "📝 New Account"])
            
            # --- 1. QUICK LOGIN (Sirf Email Se) ---
            with auth_tab[0]:
                with st.form("quick_login"):
                    l_email = st.text_input("Enter Registered Email", key="l_email_quick").strip().lower()
                    if st.form_submit_button("ENTER DASHBOARD 🚀", use_container_width=True):
                        if l_email:
                            # Database mein check karo user hai ya nahi
                            prof = supabase.table("profiles").select("*").eq("email", l_email).execute()
                            if prof.data:
                                st.session_state.user_data = prof.data[0]
                                st.success("Pehchan liya bhai! Khul raha hai dashboard...")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Ye email registered nahi hai. New Account tab pe jao.")
                        else:
                            st.warning("Email toh dalo!")

            # --- 2. NEW ACCOUNT (Direct Entry) ---
            with auth_tab[1]:
                with st.form("reg_form_quick"):
                    st.info("🎁 Naya account banao aur 10 Credits free pao!")
                    s_name = st.text_input("Full Name", placeholder="Krishna", key="reg_name_quick")
                    s_email = st.text_input("Email ID", key="reg_email_quick").strip().lower()
                    
                    if st.form_submit_button("CREATE & ENTER 🔥", use_container_width=True):
                        if s_name and s_email:
                            try:
                                # Check if email already exists
                                check = supabase.table("profiles").select("*").eq("email", s_email).execute()
                                if check.data:
                                    st.warning("Account pehle se hai! Login tab use karo.")
                                else:
                                    u_hash = hashlib.md5(s_email.encode()).hexdigest()[:5].upper()
                                    new_u = {
                                        "email": s_email, 
                                        "full_name": s_name, 
                                        "credits": 10, 
                                        "referral_code": f"TOP{u_hash}", 
                                        "ref_claimed": False
                                    }
                                    ins = supabase.table("profiles").insert(new_u).execute()
                                    if ins.data:
                                        st.session_state.user_data = ins.data[0]
                                        st.success(f"Welcome {s_name}! Setup complete.")
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Server Busy: {str(e)}")
                        else:
                            st.warning("Bhai, details toh bharo!")
        st.stop()
# --- 🎁 PROMO LOGIC (STRICT SYNC) ---
def claim_reward_logic(claim_code):
    user = st.session_state.user_data
    code = claim_code.strip().upper()
    if user.get('ref_claimed', False):
        st.warning("Limit: Ek baar hi claim hota hai!")
        return
    
    if code == "EARLY25":
        try:
            # Check 100 limit in DB
            count_res = supabase.table("profiles").select("email", count="exact").eq("ref_claimed", True).execute()
            if count_res.count >= 100:
                st.error("Expired: Pehle 100 toppers ne ise use kar liya hai.")
                return

            new_credits = user['credits'] + 25
            # Update DB
            update = supabase.table("profiles").update({"credits": new_credits, "ref_claimed": True}).eq("email", user['email']).execute()
            
            if update.data:
                st.session_state.user_data['credits'] = new_credits
                st.session_state.user_data['ref_claimed'] = True
                st.balloons()
                st.success("25 Credits Added!")
                st.rerun()
        except: st.error("Database sync failed. Refresh karke try karo.")
    else: st.error("Galat Code!")

# --- 💎 REVENUE LOGIC ---
def use_credits(amount):
    if st.session_state.user_data:
        email = st.session_state.user_data['email']
        current = st.session_state.user_data.get('credits', 0)
        if current >= amount:
            new_total = current - amount
            supabase.table("profiles").update({"credits": new_total}).eq("email", email).execute()
            st.session_state.user_data['credits'] = new_total
            return True
    return False

# 🛡️ RUN AUTH ENGINE
clean_email_auth()

# --- 💳 AUTO-SYNC TRIGGER (Ise yaha daalo) ---
if st.session_state.user_data:
    sync_topper_credits()

# Professional Welcome Header with User Name
st.markdown(f"### Welcome back, {st.session_state.user_data['full_name']}! 🎓")

# --- 🎨 UI STYLES ---
st.markdown("""
<style>
.stApp { background-color: #0d1117; color: white; }
[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
.wallet-card { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 15px; border: 1px solid #4CAF50; text-align: center; margin-bottom: 20px; }
.pay-card { background: #1c2128; border: 1px solid #30363d; padding: 12px; border-radius: 10px; margin-bottom: 10px; text-decoration: none; display: block; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#4CAF50;'>TopperGPT</h2>", unsafe_allow_html=True)
    if st.session_state.user_data:
        st.markdown(f'''<div class="wallet-card">
            <p style="margin:0; font-size:12px; color:#eab308; font-weight:bold;">{st.session_state.user_data["full_name"]}</p>
            <h1 style="margin:5px 0; color:white; font-size:45px; font-weight:900;">{st.session_state.user_data["credits"]} 🔥</h1>
            <p style="margin:0; font-size:11px;">CREDITS AVAILABLE</p>
        </div>''', unsafe_allow_html=True)

    # Promo Box: Only shows if user hasn't claimed anything yet
    if st.session_state.user_data and not st.session_state.user_data.get('ref_claimed', False):
        promo = st.text_input("Enter Reward Code:", placeholder="Limited offer...", key="promo_box")
        if st.button("Claim Rewards 🚀", use_container_width=True): claim_reward_logic(promo)

# --- 📜 TRANSACTION HISTORY SECTION ---
    st.divider()
    with st.expander("🕒 Transaction History"):
        if st.session_state.user_data:
            hist = supabase.table("payments").select("*").eq("email", st.session_state.user_data['email']).order("created_at", desc=True).limit(5).execute()
            if hist.data:
                for item in hist.data:
                    st.markdown(f'''<div style="font-size: 11px; padding: 5px; border-bottom: 1px solid #30363d; color: #8b949e;">
                        ID: {item['payment_id'][:12]}... <br>
                        Amt: ₹{item['amount']} | Status: {item['status']}
                    </div>''', unsafe_allow_html=True)
            else:
                st.caption("No recent payments found.")        
    
    st.divider()
    st.markdown("### 💎 Refill Credits")
    packs = [
        {"n": "Sureshot Pack", "c": "70", "p": "₹59", "u": "https://rzp.io/rzp/FmwE0Ms6"},
        {"n": "Jugaad Pack", "c": "150", "p": "₹99", "u": "https://rzp.io/rzp/AWiyLxEi"},
        {"n": "Topper Pro", "c": "350", "p": "₹149", "u": "https://rzp.io/rzp/hXcR54E"}
    ]
    for pack in packs:
        st.markdown(f'''<a href="{pack['u']}" target="_blank" class="pay-card">
            <div style="display:flex; justify-content:space-between;"><b>{pack['n']}</b> <span>{pack['p']}</span></div>
            <p style="margin:5px 0 0 0; font-size:11px; color:#4CAF50;">+ {pack['c']} Credits</p>
        </a>''', unsafe_allow_html=True)
    
    if st.button("🔓 Logout", use_container_width=True):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

# --- 5. MAIN FEATURES TABS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "💬 Chat PDF", "🧪 FORMULA ARCHITECT", "🔮 Predict Questions", "🧠 MindMap", 
    "🃏 Flashcards", "❓ Engg PYQs", "🔍 Search", "📊 MU SGPA Battle Planner", "⚖️ Legal"
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
# --- TAB 2: FORMULA & DERIVATION ARCHITECT (V48) ---
# ==========================================
with tab2:
    st.markdown("<h2 style='text-align: center; color: #ef4444;'>🧪 Formula & Derivation Miner</h2>", unsafe_allow_html=True)

    col_in, col_uni = st.columns([0.6, 0.4])
    with col_in:
        formula_input = st.text_input("Subject/Topic Name:", key="f_input_v48", placeholder="e.g. Applied Physics 2")
    with col_uni:
        u_name = st.selectbox("Select University:", ["Mumbai University", "SPPU", "GTU", "AKTU", "Other"], key="f_uni_v48")

    f_cost = 3

    # --- ACTION BUTTONS ---
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        generate_triggered = st.button(f"🔥 Mine Technical Cheat Sheet ({f_cost} Credits)", use_container_width=True)
    with c_btn2:
        if "last_formula_data" in st.session_state:
            st.button("🔄 Refresh Rendering", on_click=lambda: st.rerun(), use_container_width=True)

    if generate_triggered:
        if len(formula_input.strip()) < 3:
            st.error("❌ Valid engineering subject dalo.")
        else:
            if use_credits(f_cost):
                with st.spinner("Mining official syllabus formulas..."):
                    try:
                        # MASTER PROMPT: Strictly forcing standard LaTeX for complex math
                        prompt = f"""
                        Act as an Engineering Professor. Topic: '{formula_input}' ({u_name}).
                        Output exactly in this style:
                        
                        ### CORE FORMULAS:
                        1. [MATH] Formula [/MATH] (Description)
                        2. [MATH] Formula [/MATH] (Description)
                        ...
                        
                        ### KEY DERIVATIONS:
                        - List 5 derivations clearly.
                        
                        CRITICAL: Use proper LaTeX syntax inside [MATH] tags for complex symbols like Nabla, Divergence, Curl, Integrals, and Fractions.
                        """

                        res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}]
                        )

                        raw_output = res.choices[0].message.content.strip()
                        
                        # Clean and store
                        clean_data = raw_output.replace('"', "'").replace("\n", "<br>")
                        st.session_state.last_formula_data = clean_data
                        st.session_state.current_f_subject = formula_input.upper()
                        st.rerun()

                    except Exception as e:
                        st.session_state.user_data['credits'] += f_cost
                        st.error(f"Logic Error: {e}")

    # --- THE RENDERER: HD Image + MathJax + TOPPERGPT Watermark ---
    if "last_formula_data" in st.session_state:
        st.markdown("---")
        
        # DOWNLOAD BUTTON PLACED ABOVE TO PREVENT CUTTING
        st.info("💡 Niche wale Card ka HD Image download karne ke liye niche button dabayein.")
        
        import streamlit.components.v1 as components
        raw_data = st.session_state.last_formula_data
        f_title = st.session_state.get('current_f_subject', "CHEAT SHEET")

        html_code = f"""
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

        <button id="downloadBtn" style="
            background: #ef4444; color: white; border: none; padding: 15px; 
            border-radius: 10px; cursor: pointer; font-weight: bold; width: 100%; font-size: 18px;
            margin-bottom: 20px; box-shadow: 0 4px 15px rgba(239,68,68,0.4);
        ">
            📥 Download High-Res Cheat Sheet (PNG Image)
        </button>

        <div id="capture-area" style="
            position: relative; 
            background: #0d1117; 
            padding: 45px; 
            border-radius: 15px; 
            border: 3px solid #ef4444; 
            color: white; 
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 600px;
        ">
            <div style="
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-35deg); 
                font-size: 70px; color: rgba(255, 255, 255, 0.04); font-weight: 900; pointer-events: none; 
                white-space: nowrap; z-index: 0; text-transform: uppercase; letter-spacing: 10px;
            ">
                TOPPERGPT • TOPPERGPT • TOPPERGPT
            </div>

            <div style="position: relative; z-index: 1;">
                <h1 style="color: #ef4444; border-bottom: 2px solid #ef4444; padding-bottom: 15px; margin-top: 0; font-size: 32px;">
                    {f_title}
                </h1>
                <p style="color: #94a3b8; font-size: 16px; margin-top: 10px;">
                    <b>University:</b> {u_name} | <b>Exam Support:</b> TopperGPT V1.0
                </p>
                
                <div id="content-body" style="font-size: 18px; line-height: 1.6; color: #e2e8f0; margin-top: 25px;">
                    {raw_data}
                </div>
            </div>
        </div>

        <script>
            // Convert [MATH] tags to MathJax syntax
            function renderMath() {{
                const body = document.getElementById('content-body');
                body.innerHTML = body.innerHTML.replace(/\[MATH\](.*?)\[\/MATH\]/g, (match, tex) => {{
                    return '\\\\[ ' + tex + ' \\\\]';
                }});
                if (window.MathJax) {{
                    MathJax.typesetPromise();
                }}
            }}

            window.onload = renderMath;

            // HD Screenshot Capture
            document.getElementById('downloadBtn').addEventListener('click', () => {{
                const area = document.getElementById('capture-area');
                const btn = document.getElementById('downloadBtn');
                btn.innerText = "Generating HD Render... Please wait";
                
                html2canvas(area, {{ 
                    backgroundColor: "#0d1117", 
                    scale: 3, // High Resolution
                    logging: false,
                    useCORS: true 
                }}).then(canvas => {{
                    const link = document.createElement('a');
                    link.download = 'TopperGPT_{f_title.replace(" ", "_")}.png';
                    link.href = canvas.toDataURL("image/png");
                    link.click();
                    btn.innerText = "📥 Download High-Res Cheat Sheet (PNG Image)";
                }});
            }});
        </script>
        """
        components.html(html_code, height=900, scrolling=True)
# ==================================================
# --- TAB 3: AI EXAM PREDICTOR (V69 - REALISM SYNC) ---
# ==================================================
with tab3:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🔮 Predict My Next Question</h2>", unsafe_allow_html=True)
    
    predict_cost = 5
    
    c1, c2 = st.columns(2)
    with c1:
        user_subj = st.text_input("Subject Name", placeholder="e.g. Applied Physics or Maths 1", key="p_subj_v68")
    with c2:
        p_uni = st.selectbox("University Pattern", ["Mumbai University (MU)", "SPPU (Pune)", "GTU", "AKTU", "Other"], key="p_uni_v68")

    syllabus_file = st.file_uploader("📂 Upload Syllabus PDF", type=["pdf"], key="p_pdf_v68")
    p_topics_manual = st.text_area("Or Paste Topics (Highly Recommended):", placeholder="e.g. Unit 1: Lasers, Unit 2: Quantum... OR Unit 1: Matrices, Unit 2: Calculus...", key="p_manual_v68")

    if st.button(f"⚡ PREDICT MY NEXT QUESTION (-{predict_cost} Credits)", use_container_width=True):
        if not user_subj:
            st.warning("Bhai, subject ka naam toh dalo!")
        elif use_credits(predict_cost): 
            with st.spinner(f"AI Sniper is aligning with {user_subj} syllabus..."):
                try:
                    final_context = ""
                    
                    if syllabus_file:
                        import pdfplumber
                        with pdfplumber.open(syllabus_file) as pdf:
                            all_text = [p.extract_text() for p in pdf.pages if p.extract_text()]
                            full_pdf_text = "\n".join(all_text)
                            
                            # 🎯 DYNAMIC SEARCH
                            if user_subj.lower() in full_pdf_text.lower():
                                start_idx = full_pdf_text.lower().find(user_subj.lower())
                                final_context = full_pdf_text[start_idx : start_idx + 10000]

                    # 📄 MANUAL TOPICS OVERRIDE
                    if p_topics_manual.strip():
                        final_context = f"PRIMARY TOPICS TO COVER:\n{p_topics_manual.strip()}\n\n" + final_context

                    if len(final_context.strip()) < 15:
                        raise Exception(f"Syllabus mein '{user_subj}' ka exact section nahi mila. Topics manually paste karo.")

                    # ✅ UPDATED MASTER PROMPT (FOR NATURAL QUESTIONS)
                    prompt = f"""
                    Act as a Senior University Professor and External Examiner for {p_uni}.
                    TARGET SUBJECT: {user_subj}.
                    CONTEXT DATA: {final_context}

                    STRICT GUIDELINES:
                    1. Predict 5 'Sureshot' questions based on the provided technical context.
                    2. DO NOT include the subject name '{user_subj}' or phrases like 'in applied physics' INSIDE the questions.
                    3. The questions must look like REAL exam questions (e.g., 'Explain Population Inversion' instead of 'Explain Population Inversion in Applied Physics').
                    4. Focus only on core technical concepts (derivations, explanations, numericals).
                    5. Format as JSON: {{"questions": [{{"question": "...", "marks": 10, "difficulty": "Hard", "probability": 95}}]}}
                    """

                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"}
                    )
                    
                    raw_data = json.loads(res.choices[0].message.content)
                    st.session_state.prediction_list = raw_data.get('questions', list(raw_data.values())[0])
                    st.session_state.p_subj_final = user_subj
                    st.balloons(); st.rerun()

                except Exception as e:
                    # ✅ REFUND LOGIC
                    st.session_state.user_data['credits'] += predict_cost
                    supabase.table("profiles").update({"credits": st.session_state.user_data['credits']}).eq("email", st.session_state.user_data['email']).execute()
                    st.error(f"Sniper Alert: {str(e)}")
        else:
            st.error("Bhai credits khatam!")

    # --- DISPLAY & SHARE ---
    if "prediction_list" in st.session_state:
        st.divider()
        st.subheader(f"🎯 Predictions for: {st.session_state.p_subj_final}")
        for q in st.session_state.prediction_list:
            prob = q.get('probability', 90)
            st.markdown(f'''<div style="background:#161b22; padding:15px; border-radius:10px; border-left:5px solid #4CAF50; margin-bottom:10px; border:1px solid #30363d;">
                <p style="color:#8b949e; font-size:10px;">PROBABILITY: {prob}%</p>
                <h4 style="color:white; margin:0;">{q.get('question')}</h4>
                <p style="color:#4CAF50; font-size:12px;">{q.get('marks', 10)}M | {q.get('difficulty', 'Medium')}</p>
            </div>''', unsafe_allow_html=True)
        
        # WhatsApp Share logic intact
        share_text = f"TopperGPT Predicted these Sureshot Questions for {st.session_state.p_subj_final}! 🔥\n\nCheck them out: toppergpt.in"
        import urllib.parse
        st.markdown(f'''<a href="https://wa.me/?text={urllib.parse.quote(share_text)}" target="_blank" style="text-decoration:none;"><button style="background:#25D366; color:white; border:none; padding:12px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer;">📲 Share Sureshot Questions on WhatsApp</button></a>''', unsafe_allow_html=True)
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
# ==================================================
# --- TAB 8: MU SGPA BATTLE PLANNER (REVENUE V65) ---
# ==================================================
with tab8:
    st.markdown("<h2 style='text-align: center; color: #FFD700;'>📊 MU SGPA Battle Planner</h2>", unsafe_allow_html=True)
    
    # Revenue Config
    sgpa_cost = 2  # 2 credits for strategy/prediction

    sgpa_mode = st.segmented_control(
        "Select Mission:", 
        options=["🎯 Target Pointer", "📈 Predict My Result"],
        default="🎯 Target Pointer",
        key="mu_mode_v65"
    )

    st.markdown("---")

    # --- INPUTS ---
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        num_subs = st.number_input("Total Theory Subjects?", 1, 8, 5)
    with c_top2:
        if sgpa_mode == "🎯 Target Pointer":
            target_val = st.slider("Target SGPA", 4.0, 10.0, 8.5, 0.1)
        else:
            st.markdown(f"<p style='margin-top:35px; color:#8b949e;'>Cost: {sgpa_cost} Credits</p>", unsafe_allow_html=True)

    # --- SUBJECT GRID ---
    subjects_data = []
    st.markdown("#### 📝 Subject-wise Weightage")
    
    # MU Simplified: Most students have 4-credit main subjects and 3-credit allied
    for i in range(num_subs):
        with st.expander(f"Subject {i+1}", expanded=True):
            col_a, col_b, col_c = st.columns([1, 1.2, 1.2])
            with col_a:
                # 💡 EXPLAINER: High credits = High weightage on SGPA
                cred = st.selectbox(f"Credits (Weight)", [4, 3, 2], index=0, key=f"v65_c_{i}", help="High credits impact your pointer more!")
            
            if sgpa_mode == "📈 Predict My Result":
                with col_b:
                    internal = st.number_input(f"Internal (20M)", 0, 20, 18, key=f"v65_i_{i}")
                with col_c:
                    theory = st.number_input(f"Theory (80M)", 0, 80, 40, key=f"v65_t_{i}")
                total = internal + theory
                # MU Grading Math
                if total >= 80: gp = 10
                elif total >= 75: gp = 9
                elif total >= 70: gp = 8
                elif total >= 60: gp = 7
                elif total >= 50: gp = 6
                elif total >= 45: gp = 5
                elif total >= 40: gp = 4
                else: gp = 0
            else:
                total, gp = 0, 0
            
            subjects_data.append({"credits": cred, "gp": gp})

    st.markdown("---")

    # --- THE REVENUE TRIGGER ---
    if st.button(f"⚡ GENERATE BATTLE REPORT (-{sgpa_cost} Credits)", use_container_width=True):
        if use_credits(sgpa_cost): # ✅ DEDUCTS FROM SUPABASE
            total_creds = sum(s['credits'] for s in subjects_data)
            
            if sgpa_mode == "🎯 Target Pointer":
                # REVERSE MATH: SGPA * Total Credits = Points Needed
                req_points = target_val * total_creds
                avg_gp = req_points / total_creds
                
                st.markdown(f"""
                    <div style="background: #1e2128; padding: 25px; border-radius: 15px; border: 2px solid #FFD700; text-align: center;">
                        <h2 style="color: #FFD700; margin:0;">MISSION: {target_val} POINTER</h2>
                        <hr style="border-color: #30363d;">
                        <h4 style="color: white;">Average Marks Needed: ~{int(avg_gp*10)-5} to {int(avg_gp*10)+5}</h4>
                        <p style="color: #8b949e;">Don't worry! Use Tab 3 to get Sureshot Questions for these marks.</p>
                    </div>
                """, unsafe_allow_html=True)

            else:
                # SGPA FORMULA: Sum(GP * Credits) / Total Credits
                total_gp_earned = sum(s['gp'] * s['credits'] for s in subjects_data)
                final_sgpa = total_gp_earned / total_creds
                
                color = "#4CAF50" if final_sgpa >= 7.5 else "#ef4444"
                st.markdown(f"""
                    <div style="background: #1e2128; padding: 25px; border-radius: 15px; border: 2px solid {color}; text-align: center;">
                        <p style="color: #8b949e; margin:0;">ESTIMATED SGPA</p>
                        <h1 style="color: {color}; font-size: 60px; margin: 10px 0;">{final_sgpa:.2f}</h1>
                    </div>
                """, unsafe_allow_html=True)
                
                if final_sgpa < 7.0:
                    st.error("🚨 Danger! Ye pointer kam hai. Physics/Maths ke high-credit subjects par focus karo!")
            
            st.balloons()
        else:
            st.error("Bhai credits khatam! Rewards section mein jao ya refer karo.")

    # --- VIRAL FLEX ---
    st.divider()
    share_text = f"TopperGPT predicted my MU SGPA Strategy! 🎯 Goal: {target_val if 'target_val' in locals() else '9.0'} Pointer. Get yours: toppergpt.in"
    st.markdown(f'''<a href="https://wa.me/?text={requests.utils.quote(share_text)}" target="_blank"><button style="background:#25D366; color:white; border:none; padding:12px; border-radius:10px; width:100%; cursor:pointer; font-weight:bold;">📤 Share Strategy with Friends</button></a>''', unsafe_allow_html=True)
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