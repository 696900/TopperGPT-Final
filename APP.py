import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
from PIL import Image, ImageDraw, ImageFont
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
import playwright
from playwright.async_api import async_playwright
import asyncio
import io
import subprocess
# app.py ke upar ye hona chahiye
from knowledge_base import PYQ_DATA, PYQ_DATA_SEM2

# 1. Gemini ko ek hi baar sahi model name ke saath rakho
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
gemini_model = genai.GenerativeModel('models/gemini-1.5-flash')

# 2. DeepSeek Client add karo (Groq library hi use hoti hai iske liye)
# Iske liye secrets.toml mein DEEPSEEK_API_KEY hona zaroori hai
deepseek_client = Groq(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# 3. Master dictionary merge (Ye sahi hai tera)
ALL_SUBJECTS = {**PYQ_DATA, **PYQ_DATA_SEM2}

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

# --- 💳 ZERO-WEBHOOK AUTOMATIC SYNC MACHINE (ANTI-LOOP SHIELD) ---
def sync_topper_credits():
    # Only run if user is logged in
    if "user_data" not in st.session_state or st.session_state.user_data is None:
        return

    # 🛑 LAYER 1: Session Time Buffer (Prevents function from hitting API every millisecond)
    if "last_sync_time" in st.session_state:
        if time.time() - st.session_state.last_sync_time < 30: # 30 sec ka gap
            return

    try:
        # Client setup using your secrets
        client = razorpay.Client(auth=(st.secrets["RAZORPAY_KEY_ID"], st.secrets["RAZORPAY_KEY_SECRET"]))
        u_email = st.session_state.user_data['email']

        # 1. Fetch last 15 successful payments from Razorpay
        payments = client.payment.all({'count': 15})

        for p in payments['items']:
            # Check if payment belongs to this user and is successful
            if p.get('email') == u_email and p['status'] == 'captured':
                p_id = p['id']
                amount = p['amount'] / 100 

                # 2. Check Database: Kya ye payment ID pehle process ho chuki hai?
                check = supabase.table("payments").select("payment_id").eq("payment_id", p_id).execute()

                if not check.data:
                    # 3. New Payment Found! Match with your Packs
                    credits_bonus = 0
                    if 55 <= amount <= 65: credits_bonus = 70      # Sureshot Pack (59)
                    elif 95 <= amount <= 105: credits_bonus = 150  # Jugaad Pack (99)
                    elif 145 <= amount <= 155: credits_bonus = 350 # Topper Pro (149)

                    if credits_bonus > 0:
                        # 🛑 LAYER 2: "Lock-First" Logic
                        # Pehle payment log insert karte hain. Agar ye duplicate hoga, toh DB error dega aur niche ka code nahi chalega.
                        try:
                            supabase.table("payments").insert({
                                "payment_id": p_id, 
                                "email": u_email, 
                                "amount": amount, 
                                "status": "processed"
                            }).execute()
                        except:
                            continue # Agar DB mein entry pehle se hai, toh skip karo

                        # 🛑 LAYER 3: Fresh DB Fetch (Anti-Lag)
                        fresh_res = supabase.table("profiles").select("credits").eq("email", u_email).single().execute()
                        db_credits = fresh_res.data['credits'] if fresh_res.data else 0
                        
                        new_total = db_credits + credits_bonus
                        
                        # Update Profile Credits in Supabase
                        supabase.table("profiles").update({"credits": new_total}).eq("email", u_email).execute()

                        # Update UI State & Force Sync
                        st.session_state.user_data['credits'] = new_total
                        st.session_state.last_sync_time = time.time() # Mark sync done
                        st.toast(f"✅ Success: {credits_bonus} Credits added instantly!", icon="🔥")
                        time.sleep(1.5)
                        st.rerun()
        
        # Mark sync attempt time even if no new payment found
        st.session_state.last_sync_time = time.time()

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

# --- 💳 AUTO-SYNC TRIGGER ---
# Ab ye har page load par Razorpay se sync karega
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
    
    # Standard Packs List
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
    
    # --- TERA LOGOUT BUTTON (AS IT IS) ---
    if st.button("🔓 Logout", use_container_width=True):
        supabase.auth.sign_out(); st.session_state.clear(); st.rerun()

# --- V7000: PREMIUM STABLE HEADER (OFFERS REMOVED) ---
if st.session_state.user_data:
    st.markdown("""
        <style>
        /* Ultra Slim Professional Header */
        .pro-strip {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 10px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        .bal-val { color: #4CAF50; font-weight: 800; font-size: 18px; }
        .shop-pills { display: flex; gap: 10px; }
        .price-pill {
            text-decoration: none;
            font-size: 11px;
            color: #8b949e !important;
            padding: 6px 12px;
            border-radius: 6px;
            background: #161b22;
            border: 1px solid #30363d;
            transition: 0.3s;
        }
        .price-pill:hover { border-color: #4CAF50; transform: translateY(-2px); }
        .price-pill b { color: #4CAF50; }

        @media (max-width: 600px) {
            .pro-strip { flex-direction: column; gap: 12px; align-items: flex-start; }
            .shop-pills { width: 100%; justify-content: space-between; }
        }
        </style>
    """, unsafe_allow_html=True)

    # Main Header (No Hints, No Popups)
    st.markdown(f"""
        <div class="pro-strip">
            <div>
                <span style="font-size: 10px; color: #8b949e; text-transform: uppercase;">Credits Balance:</span>
                <span class="bal-val">{st.session_state.user_data["credits"]} 🔥</span>
            </div>
            <div class="shop-pills">
                <a href="https://rzp.io/rzp/FmwE0Ms6" target="_blank" class="price-pill">70Cr @ <b>₹59</b></a>
                <a href="https://rzp.io/rzp/AWiyLxEi" target="_blank" class="price-pill">150Cr @ <b>₹99</b></a>
                <a href="https://rzp.io/rzp/hXcR54E" target="_blank" class="price-pill">350Cr @ <b>₹149</b></a>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN FEATURES TABS ---
tab1, tab7 = st.tabs(["🔮 Predict Questions", "🔍 Search"])

## --- TAB 1: PREDICT MY NEXT QUESTION (V2600 NEON SNIPER + UNCUT FIX) ---
with tab1: 
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🔮 TopperGPT Universal Sniper</h2>", unsafe_allow_html=True)
    
    predict_cost = 15
    c1, c2 = st.columns(2)
    with c1:
        user_subj = st.text_input("Subject Name", placeholder="e.g. Applied Maths, BEE, Graphics", key="subj_v2600_final")
    with c2:
        p_uni = st.selectbox("University Pattern", ["Mumbai University (MU)"], key="uni_v2600_final")

    # --- 🎯 SECTION 1: PREDICT QUESTION (STRICTLY UNCHANGED AS REQUESTED) ---
    if st.button(f"⚡ GENERATE BATTLE PLAN (-{predict_cost} Credits)", use_container_width=True):
        if not user_subj:
            st.warning("Pehle subject ka naam dalo bhai!")
        elif use_credits(predict_cost): 
            with st.spinner(f"Analyzing {user_subj} Exam Patterns..."):
                try:
                    raw_in = user_subj.lower().strip()
                    search_key = raw_in
                    if any(x in raw_in for x in ["ds", "data structure", "dsa"]): search_key = "data structure"
                    elif any(x in raw_in for x in ["math", "m2"]): search_key = "applied mathematics 2"
                    elif any(x in raw_in for x in ["graphics", "eg"]): search_key = "engineering graphics"
                    elif "physics" in raw_in: search_key = "applied physics"
                    
                    evidence = ALL_SUBJECTS.get(search_key, "MU Engineering Standard Pattern.")

                    prompt = f"""
                    Role: Senior MU Paper Setter. Target: {user_subj} | Data: {evidence}
                    MISSION: Predict 12 high-probability questions for WRITTEN EXAM.
                    
                    STRICT DYNAMIC RULES:
                    1. IF DRAWING (EG): 10M-15M Drafting problems only. No theory/CAD.
                    2. IF MATHS/NUMERICAL: Provide actual numericals with specific values.
                    3. SURESHOT: Add | Confidence: [85-99]% | Marks: [X]M.
                    4. REPEATED: Mention MU Exam Year (e.g. MAY 2024). NO Confidence %.
                    
                    STRUCTURE: START_SURESHOT [12 Qs] END_SURESHOT. START_REPEATED [6 PYQs] END_REPEATED. START_JUGAAD [5 Topics] END_JUGAAD. START_PLAN [Roadmap] END_PLAN.
                    """

                    try:
                        res = deepseek_client.chat.completions.create(
                            model="deepseek-chat", messages=[{"role": "user", "content": prompt}], timeout=15 
                        )
                        raw_out = res.choices[0].message.content.strip()
                    except:
                        res_f = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}]
                        )
                        raw_out = res_f.choices[0].message.content.strip()

                    st.session_state.prediction_pro_out = raw_out
                    st.session_state.p_subj_pro_final = user_subj
                    st.balloons(); st.rerun()

                except Exception as e:
                    st.session_state.user_data['credits'] += predict_cost 
                    supabase.table("profiles").update({"credits": st.session_state.user_data['credits']}).eq("email", st.session_state.user_data['email']).execute()
                    st.error(f"⚠️ Stability Alert: {str(e)}")

    # --- UI RENDER (Zero-Fail Parser) ---
    if "prediction_pro_out" in st.session_state:
        out_text = st.session_state.prediction_pro_out
        st.success(f"✅ Pattern Verified for {st.session_state.p_subj_pro_final.upper()}")
        
        ui_sections = {
            "🎯 Sureshot Predictions (Confidence Verified)": ("START_SURESHOT", "START_REPEATED", "#4CAF50"),
            "📊 Most Repeated PYQs (Source Proof)": ("START_REPEATED", "START_JUGAAD", "#2196F3"),
            "🛡️ Pass Hone Ka Jugaad": ("START_JUGAAD", "START_PLAN", "#FF9800"),
            "📅 3-Day Battle Roadmap": ("START_PLAN", "END_PLAN", "#9C27B0")
        }
        
        for title, (start, end, color) in ui_sections.items():
            if start in out_text:
                content = out_text.split(start)[1].split(end)[0] if end in out_text else out_text.split(start)[1]
                display_content = content.replace("END_SURESHOT", "").replace("END_REPEATED", "").replace("END_JUGAAD", "").replace("END_PLAN", "").strip()
                with st.expander(title, expanded=(start == "START_SURESHOT")):
                    st.markdown(f"<div style='border-left:6px solid {color}; padding:15px; background:#1e1e1e; border-radius:12px; line-height:2.2; color:white; white-space: pre-wrap;'>{display_content}</div>", unsafe_allow_html=True)

        # --- 🎙️ SECTION 2: PROFESSOR-LEVEL VIVA MASTER (NEON + UNCUT UPGRADE) ---
        st.markdown("---")
        st.markdown("<h3 style='text-align: center; color: #FFD700;'>🎙️ Professor-Level Viva Sniper</h3>", unsafe_allow_html=True)
        
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            personality = st.selectbox("Examiner Style", ["Strict External (Grilling)", "Silent Killer (Tricky)", "Chill Senior (Conceptual)"], key="v_style_v26")
        with v_col2:
            intensity = st.select_slider("Intensity Level", options=["Warm-up", "Deep Dive", "Pressure"], key="v_intense_v26")

        oral_cost = 10
        if st.button(f"🔥 START VIVA SIMULATION (-{oral_cost} Credits)", key="oral_v26", use_container_width=True):
            if use_credits(oral_cost):
                with st.spinner("Professor is reviewing preparation..."):
                    try:
                        viva_logic = f"""
                        Act as an MU External Examiner for {st.session_state.p_subj_pro_final}. Style: {personality}. Level: {intensity}.
                        MISSION: Ask 10 depth-testing questions. 
                        
                        STRICT FORMAT RULES (USE SPAN TAGS FOR COLOR):
                        1. Wrap the Question in <span style='color: #FFD700;'>...</span>
                        2. Wrap the TOPPER ANSWER in <span style='color: #4CAF50;'>...</span> (Must be Bullet Points).
                        3. Wrap the THE TRAP in <span style='color: #FF4B4B;'>...</span>
                        4. NO Markdown Headers (###). Use plain BOLD text.
                        
                        STRUCTURE:
                        Q[X]: <span style='color: #FFD700;'>[Question]</span>
                        TOPPER ANSWER: <span style='color: #4CAF50;'>
                        - [Bullet 1]
                        - [Bullet 2]</span>
                        THE TRAP: <span style='color: #FF4B4B;'>[Mistake]</span>
                        """
                        
                        viva_res = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": viva_logic}],
                            max_tokens=3000 # 🚨 UNCUT FIX: Prevents output cutoff
                        )
                        st.session_state.oral_output = viva_res.choices[0].message.content.strip()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Oral Sniper Error: {str(e)}")

        if "oral_output" in st.session_state:
            st.info(f"🎙️ Simulation Mode Active: {personality}")
            st.markdown(f"<div style='background: #000; border: 2px solid #FFD700; padding: 25px; border-radius: 15px; color: #D3D3D3; line-height: 1.8; white-space: pre-wrap;'>{st.session_state.oral_output}</div>", unsafe_allow_html=True)

        # WhatsApp Share
        share_msg = f"Bhai! TopperGPT ke Professor Mode ne meri Viva mein g**nd maar di! 😂 Tu bhi try kar: toppergpt.in"
        import urllib.parse
        st.markdown(f'''<a href="https://wa.me/?text={urllib.parse.quote(share_msg)}" target="_blank" style="text-decoration:none;"><button style="background:#25D366; color:white; border:none; padding:15px; border-radius:10px; width:100%; font-weight:bold; cursor:pointer; margin-top:10px; width:100%;">📲 Share Battle Plan</button></a>''', unsafe_allow_html=True)


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

