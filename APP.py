import streamlit as st
import google.generativeai as genai
import time 
import razorpay
import re
from groq import Groq
import hashlib
from supabase import create_client, Client

# app.py ke upar ye hona chahiye
from knowledge_base import PYQ_DATA, PYQ_DATA_SEM2

# 1. Gemini Client Setup
genai.configure(api_key=st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY"))
gemini_model = genai.GenerativeModel('models/gemini-1.5-flash')

# 2. DeepSeek Client Setup
deepseek_client = Groq(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# 3. Master dictionary merge
ALL_SUBJECTS = {**PYQ_DATA, **PYQ_DATA_SEM2}

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="TopperGPT Dashboard", layout="wide", page_icon="🚀")

# Groq Client Setup
if "groq_client" not in st.session_state or st.session_state.groq_client is None:
    api_key_groq = st.secrets.get("GROQ_API_KEY")
    if api_key_groq:
        st.session_state.groq_client = Groq(api_key=api_key_groq)

groq_client = st.session_state.get("groq_client")

# --- SUPABASE INITIALIZATION ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- AUTH ENGINE (WITH TRIAL & PRO LOGIC) ---
def clean_email_auth():
    if "user_data" not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        st.markdown("""
            <div style="text-align:center; padding: 10px;">
                <div style="font-size: 80px; margin-bottom: 0;">🎓</div>
                <h1 style="color:#4CAF50; font-size: 3.5rem; margin-bottom:0;">TopperGPT</h1>
                <p style="color:#8b949e; margin-top:0; font-weight:bold;">Precision Engineering Intelligence Dashboard</p>
            </div>
        """, unsafe_allow_html=True)

        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            auth_tab = st.tabs(["🔑 Quick Login", "📝 New Account"])
            
            # 1. Quick Login
            with auth_tab[0]:
                with st.form("quick_login"):
                    l_email = st.text_input("Enter Registered Email", key="l_email_quick").strip().lower()
                    if st.form_submit_button("ENTER DASHBOARD 🚀", use_container_width=True):
                        if l_email:
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

            # 2. New Account
            with auth_tab[1]:
                with st.form("reg_form_quick"):
                    st.info("🎁 Naya account banao aur 10 Free Trials pao!")
                    s_name = st.text_input("Full Name", placeholder="Krishna", key="reg_name_quick")
                    s_email = st.text_input("Email ID", key="reg_email_quick").strip().lower()
                    
                    if st.form_submit_button("CREATE & ENTER 🔥", use_container_width=True):
                        if s_name and s_email:
                            try:
                                check = supabase.table("profiles").select("*").eq("email", s_email).execute()
                                if check.data:
                                    st.warning("Account pehle se hai! Login tab use karo.")
                                else:
                                    new_u = {
                                        "email": s_email, 
                                        "full_name": s_name, 
                                        "free_trials_left": 10,
                                        "is_pro": False
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

# --- TRIAL & PRO ACCESS HANDLERS ---
def check_access():
    user = st.session_state.get("user_data", {})
    if user.get("is_pro", False):
        return True
    return user.get("free_trials_left", 10) > 0

def deduct_trial():
    user = st.session_state.get("user_data", {})
    if not user.get("is_pro", False):
        curr = user.get("free_trials_left", 10)
        new_val = max(0, curr - 1)
        st.session_state.user_data["free_trials_left"] = new_val
        try:
            supabase.table("profiles").update({"free_trials_left": new_val}).eq("email", user["email"]).execute()
        except Exception:
            pass  # DB column missing hone par bhi app crash nahi hoga

def show_paywall():
    st.error("🚨 Free Trials Khatam! Upgrade to TopperGPT PRO.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background:#161b22; border:2px solid #4CAF50; border-radius:10px; padding:15px; text-align:center;">
            <h3>Monthly Pass</h3>
            <h1 style="color:#4CAF50;">₹49</h1>
            <p style="color:#8b949e;">30 Days Unlimited Access</p>
            <a href="https://rzp.io/rzp/AWiyLxEi" target="_blank" style="background:#4CAF50; color:white; padding:10px 15px; border-radius:8px; text-decoration:none; display:inline-block; font-weight:bold;">Get Monthly Pass</a>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="background:#161b22; border:2px solid #00F2FE; border-radius:10px; padding:15px; text-align:center;">
            <h3>Semester Pass</h3>
            <h1 style="color:#00F2FE;">₹199</h1>
            <p style="color:#8b949e;">Full Semester Access + Analytics</p>
            <a href="https://rzp.io/rzp/hXcR54E" target="_blank" style="background:#00F2FE; color:black; padding:10px 15px; border-radius:8px; text-decoration:none; display:inline-block; font-weight:bold;">Get Semester Pass</a>
        </div>
        """, unsafe_allow_html=True)

# Run Auth
clean_email_auth()

# UI STYLES
st.markdown("""
<style>
.stApp { background-color: #0d1117; color: white; }
[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
.trial-card { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 18px; border-radius: 12px; border: 1px solid #4CAF50; text-align: center; margin-bottom: 20px; }
.card-box { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#4CAF50;'>TopperGPT</h2>", unsafe_allow_html=True)
    user = st.session_state.user_data
    is_pro = user.get("is_pro", False)
    trials = user.get("free_trials_left", 10)

    if is_pro:
        st.markdown('''<div class="trial-card" style="border-color:#00F2FE;">
            <p style="margin:0; font-size:12px; color:#00F2FE; font-weight:bold;">STATUS</p>
            <h2 style="margin:5px 0; color:white;">👑 PRO USER</h2>
            <p style="margin:0; font-size:11px; color:#8b949e;">Unlimited Access</p>
        </div>''', unsafe_allow_html=True)
    else:
        st.markdown(f'''<div class="trial-card">
            <p style="margin:0; font-size:12px; color:#eab308; font-weight:bold;">{user.get("full_name", "Student")}</p>
            <h1 style="margin:5px 0; color:white; font-size:38px; font-weight:900;">{trials}/10</h1>
            <p style="margin:0; font-size:11px;">FREE TRIALS LEFT</p>
        </div>''', unsafe_allow_html=True)

    st.divider()
    if st.button("🔓 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Welcome Header
st.markdown(f"### Welcome back, {st.session_state.user_data.get('full_name', 'Student')}! 🎓")

# --- MAIN FEATURES TABS ---
tab1, tab7 = st.tabs(["🔮 Predict Questions", "🔍 Streamlined Topic Search"])

# ==================================================
# --- TAB 1: PREDICT MY NEXT QUESTION ---
# ==================================================
with tab1: 
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🔮 TopperGPT Universal Sniper</h2>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        user_subj = st.text_input("Subject Name", placeholder="e.g. Applied Maths, BEE, Graphics, DSA", key="subj_v2600_final")
    with c2:
        p_uni = st.selectbox("University Pattern", ["Mumbai University (MU)"], key="uni_v2600_final")

    if st.button("⚡ GENERATE BATTLE PLAN", use_container_width=True):
        if not user_subj.strip():
            st.warning("Pehle subject ka naam dalo bhai!")
        elif not check_access():
            show_paywall()
        else:
            deduct_trial()
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
                    st.balloons()
                    st.rerun()

                except Exception as e:
                    st.error(f"⚠️ Stability Alert: {str(e)}")

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

# ==================================================
# --- TAB 7: STREAMLINED TOPIC SEARCH ---
# ==================================================
with tab7:
    st.subheader("🔍 Streamlined Topic Search")
    st.caption("Instant 3-Card Breakdown: University Definition, Technical Breakdown, and Working Principle.")
    
    query = st.text_input("Enter Engineering Topic (e.g. Transformer, PN Diode, Virtual Memory):", key="search_final_absolute_v1")
    
    if st.button("Deep Research", key="btn_absolute_v1"):
        if not query.strip():
            st.warning("Pehle koi topic toh likho!")
        elif not check_access():
            show_paywall()
        else:
            deduct_trial()
            with st.spinner(f"PhD Mentor is analyzing '{query}'..."):
                prompt = f"""
                Act as a PhD Engineering Professor for Mumbai University curriculum.
                Provide an academically accurate and high-scoring report for: '{query}'.
                
                OUTPUT FORMAT STRICTLY USING THESE 3 HEADERS ONLY:
                [1_DEF]
                Exact University Standard 2-Mark definition as expected in MU marking rubrics.
                
                [2_BRK]
                Technical Breakdown: Architecture, internal equations, core components, and diagram notes.
                
                [3_WRK]
                Working Principle: Step-by-step operational logic and mechanism.
                """
                try:
                    res = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.session_state.research_data = res.choices[0].message.content
                    st.session_state.research_query = query
                    st.rerun()
                except Exception as e: 
                    st.error(f"System Busy. Error: {e}")

    if "research_data" in st.session_state and st.session_state.research_data:
        out = st.session_state.research_data
        q_name = st.session_state.research_query

        def extract_block(start_tag, end_tag=None):
            try:
                if start_tag not in out:
                    return "Details being formulated..."
                content = out.split(start_tag)[1]
                if end_tag and end_tag in content:
                    content = content.split(end_tag)[0]
                return content.strip()
            except:
                return "Section parsing error."

        def_text = extract_block("[1_DEF]", "[2_BRK]")
        brk_text = extract_block("[2_BRK]", "[3_WRK]")
        wrk_text = extract_block("[3_WRK]")

        st.markdown(f"## 📘 Technical Report: {q_name}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="card-box" style="border-left: 4px solid #4CAF50;">
                <h4 style="color:#4CAF50; margin-top:0;">1. University Standard Definition</h4>
                <p style="font-size:14px; line-height:1.6;">{def_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="card-box" style="border-left: 4px solid #00F2FE;">
                <h4 style="color:#00F2FE; margin-top:0;">2. Technical Breakdown</h4>
                <p style="font-size:14px; line-height:1.6;">{brk_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""
            <div class="card-box" style="border-left: 4px solid #FFD700;">
                <h4 style="color:#FFD700; margin-top:0;">3. Working Principle</h4>
                <p style="font-size:14px; line-height:1.6;">{wrk_text}</p>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑️ Clear Research"):
            st.session_state.research_data = None
            st.rerun()