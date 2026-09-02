import streamlit as st
import requests
import json
import time 
import hashlib
from supabase import create_client, Client
from groq import Groq

# Knowledge base import
try:
    from knowledge_base import PYQ_DATA, PYQ_DATA_SEM2
    ALL_SUBJECTS = {**PYQ_DATA, **PYQ_DATA_SEM2}
except Exception:
    ALL_SUBJECTS = {}

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="TopperGPT Dashboard", layout="wide", page_icon="🎓")

# --- 2. SUPABASE INITIALIZATION ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

# --- 3. DYNAMIC AUTODETECT AI ENGINE ---
def generate_ai_response(prompt_text):
    errors = []

    # 1. Google Gemini Dynamic Discovery (Calls ModelService.ListModels first)
    gemini_key = (st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")).strip()
    if gemini_key:
        try:
            # Fetch all supported models for this specific API key
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
            list_res = requests.get(list_url, timeout=10)
            if list_res.status_code == 200:
                available = list_res.json().get("models", [])
                valid_models = [
                    m["name"] for m in available 
                    if "generateContent" in m.get("supportedGenerationMethods", [])
                ]
                
                # Pick any supported text model
                for target_model in valid_models:
                    post_url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={gemini_key}"
                    headers = {"Content-Type": "application/json"}
                    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
                    res = requests.post(post_url, headers=headers, json=payload, timeout=25)
                    if res.status_code == 200:
                        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            else:
                errors.append(f"Gemini ListModels Failed: {list_res.text}")
        except Exception as e:
            errors.append(f"Gemini AutoDetect Error: {str(e)}")

    # 2. Groq Legacy Models
    groq_key = st.secrets.get("GROQ_API_KEY", "").strip()
    if groq_key:
        for grq_model in ["llama3-70b-8192", "mixtral-8x7b-32768"]:
            try:
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": grq_model,
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.4
                }
                res = requests.post(url, headers=headers, json=payload, timeout=20)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"].strip()
                else:
                    errors.append(f"Groq[{grq_model}]: {res.status_code}")
            except Exception as e:
                errors.append(f"Groq[{grq_model}] Ex: {str(e)}")

    raise Exception(" | ".join(errors) if errors else "No valid API models found.")
# --- 4. AUTH ENGINE (10 FREE TRIALS + PRO SYSTEM) ---
def clean_email_auth():
    if "user_data" not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        st.markdown("""
            <div style="text-align:center; padding: 15px;">
                <div style="font-size: 70px; margin-bottom: 0;">🎓</div>
                <h1 style="color:#4CAF50; font-size: 3.2rem; margin-bottom:0;">TopperGPT</h1>
                <p style="color:#8b949e; margin-top:0; font-weight:bold;">Precision Engineering Intelligence Dashboard</p>
            </div>
        """, unsafe_allow_html=True)

        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            auth_tab = st.tabs(["🔑 Quick Login", "📝 New Account"])
            
            with auth_tab[0]:
                with st.form("quick_login"):
                    l_email = st.text_input("Enter Registered Email", key="l_email_quick").strip().lower()
                    if st.form_submit_button("ENTER DASHBOARD 🚀", use_container_width=True):
                        if l_email:
                            try:
                                prof = supabase.table("profiles").select("*").eq("email", l_email).execute()
                                if prof.data:
                                    st.session_state.user_data = prof.data[0]
                                    st.success("Welcome back! Loading dashboard...")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Email registered nahi hai. New Account tab use karo.")
                            except Exception as e:
                                st.error(f"Database error: {e}")
                        else:
                            st.warning("Email required!")

            with auth_tab[1]:
                with st.form("reg_form_quick"):
                    st.info("🎁 New account banao aur 10 Free Trials pao!")
                    s_name = st.text_input("Full Name", placeholder="Krishna", key="reg_name_quick")
                    s_email = st.text_input("Email ID", key="reg_email_quick").strip().lower()
                    
                    if st.form_submit_button("CREATE & ENTER 🔥", use_container_width=True):
                        if s_name and s_email:
                            try:
                                check = supabase.table("profiles").select("*").eq("email", s_email).execute()
                                if check.data:
                                    st.warning("Account already exists! Use Login tab.")
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
                                        st.success(f"Welcome {s_name}!")
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Server error: {str(e)}")
                        else:
                            st.warning("Details fill karo!")
        st.stop()

# --- 5. ACCESS MANAGEMENT ---
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
            pass

def show_paywall():
    st.error("🚨 Free Trials Finished! Upgrade to TopperGPT PRO.")
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

clean_email_auth()

# --- 6. UI STYLING ---
st.markdown("""
<style>
.stApp { background-color: #0d1117; color: white; }
[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
.trial-card { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 18px; border-radius: 12px; border: 1px solid #4CAF50; text-align: center; margin-bottom: 20px; }
.blueprint-card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 18px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#4CAF50;'>TopperGPT</h2>", unsafe_allow_html=True)
    user = st.session_state.user_data
    is_pro = user.get("is_pro", False)
    trials = user.get("free_trials_left", 10)

    if is_pro:
        st.markdown('''<div class="trial-card" style="border-color:#00F2FE;">
            <p style="margin:0; font-size:12px; color:#00F2FE; font-weight:bold;">STATUS</p>
            <h2 style="margin:5px 0; color:white;">👑 PRO USER</h2>
            <p style="margin:0; font-size:11px; color:#8b949e;">Unlimited Access Unlocked</p>
        </div>''', unsafe_allow_html=True)
    else:
        st.markdown(f'''<div class="trial-card">
            <p style="margin:0; font-size:12px; color:#eab308; font-weight:bold;">{user.get("full_name", "Student")}</p>
            <h1 style="margin:5px 0; color:white; font-size:38px; font-weight:900;">{trials}/10</h1>
            <p style="margin:0; font-size:11px;">FREE TRIALS REMAINING</p>
        </div>''', unsafe_allow_html=True)

    st.divider()
    if st.button("🔓 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown(f"### Welcome back, {st.session_state.user_data.get('full_name', 'Student')}! 🎓")

# --- 8. MAIN FEATURES TABS ---
tab1, tab2, tab3 = st.tabs([
    "🎯 Predicted Questions", 
    "📝 Chapter Short-Notes", 
    "🔍 Streamlined Topic Search"
])

# ==================================================
# --- TAB 1: PREDICTED QUESTIONS ENGINE (FAST & CLEAN) ---
# ==================================================
with tab1:
    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>🎯 MU Exam Sniper: Predicted Questions</h2>", unsafe_allow_html=True)
    st.caption("Enter any topic to get high-frequency MU questions and historical exam trends.")
    
    p_topic = st.text_input("Enter Topic or Module Name:", placeholder="e.g. Runge-Kutta, Newton-Raphson, Diode, Trees, Complex Integration", key="p_topic_only_v1")

    if st.button("⚡ EXTRACT EXAM QUESTIONS", use_container_width=True):
        if not p_topic.strip():
            st.warning("Pehle topic ka naam toh likho bhai!")
        else:
            with st.spinner(f"Extracting high-probability MU questions for '{p_topic}'..."):
                fast_prompt = f"""
                You are a Senior Mumbai University (MU) Engineering Paper Setter.
                Target Topic: {p_topic}

                Generate a crisp, high-speed examination blueprint. Do not output conversational filler.
                Strictly format as:

                ### SECTION 1: 🎯 Top 5 Most Repeated Exam Questions
                List 5 high-probability questions (combination of [2M], [6M], and [10M]).
                For each question use this exact clean format:
                **Q[Number] ([Marks]M) | [Expected Probability %]**
                - **Question:** [Exact exam question statement]
                - **Marking Rubric:** [1-line marks breakup, e.g., Formula: 2M, Calculation: 3M, Final Ans: 1M]
                - **Examiner Trap:** [1-line common mistake students make]

                ---

                ### SECTION 2: 📚 Complete PYQ Archive for this Topic
                Group all other previous years variations into:
                - **2-Mark Short Questions & Definitions** (List 3-4 questions)
                - **6-Mark Analytical & Derivations** (List 2-3 questions)
                - **10-Mark Full Numericals / Long Problems** (List 2-3 questions with given values)
                """
                try:
                    res_text = generate_ai_response(fast_prompt)
                    st.session_state.p_clean_out = res_text
                    st.session_state.p_clean_topic = p_topic
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation error: {e}")

    # Display Clean Output with Pro Solution Locks
    if "p_clean_out" in st.session_state and st.session_state.p_clean_out:
        st.markdown("---")
        st.markdown(f"### 📘 Exam Target Sheet: **{st.session_state.get('p_clean_topic', '').upper()}**")
        
        # Split into main sections for display
        raw_output = st.session_state.p_clean_out
        st.markdown(raw_output)

        st.markdown("---")
        # --- PRO MONETIZATION TRIGGER ---
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1f2937 0%, #111827 100%); border: 2px solid #00F2FE; border-radius: 12px; padding: 20px; text-align: center; margin-top: 25px;">
            <h3 style="color: #00F2FE; margin-top: 0;">💡 In Questions Ke Step-by-Step Solved Answers Chahiye?</h3>
            <p style="color: #9ca3af; font-size: 14px;">Topper Answer Sheet format, step-by-step derivations, aur solved numericals unlock karein TopperGPT PRO ke saath.</p>
            <a href="https://rzp.io/rzp/AWiyLxEi" target="_blank" style="background: #00F2FE; color: black; padding: 10px 22px; border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 8px;">🔓 Unlock Complete Solutions (₹49)</a>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Search Another Topic"):
            del st.session_state.p_clean_out
            st.rerun()
# ==================================================
# --- TAB 2: CHAPTER SHORT-NOTES GENERATOR ---
# ==================================================
with tab2:
    st.subheader("📝 Chapter Short-Notes Generator")
    st.caption("1-Click 3-Block Revision Sheet: Formulas & Units, High Weightage Topics, and Quick Summary.")
    
    col_sn1, col_sn2 = st.columns(2)
    with col_sn1:
        sn_subject = st.text_input("Subject Name", placeholder="e.g. Applied Mathematics IV, DSA, BEE, Physics", key="sn_subj_input")
    with col_sn2:
        sn_chapter = st.text_input("Chapter / Module Name", placeholder="e.g. Complex Integration, Trees, Semiconductor", key="sn_chap_input")
        
    if st.button("📑 Generate 3-Block Short Notes", use_container_width=True):
        if not sn_subject.strip() or not sn_chapter.strip():
            st.warning("Subject aur Chapter dono ka naam dalo!")
        elif not check_access():
            show_paywall()
        else:
            deduct_trial()
            with st.spinner(f"Generating revision sheet for {sn_chapter}..."):
                sn_prompt = f"""
                Act as a Principal Mumbai University (MU) Engineering Professor.
                Target Subject: {sn_subject}
                Target Chapter/Module: {sn_chapter}
                
                Generate a precision 1-page revision sheet divided strictly into:
                ### 1. 🧮 Important Formulas, Constants & Units
                - List all critical formulas with standard SI units.
                ### 2. 🎯 High-Weightage Core Topics (Exam Priority)
                - List top 5 high-yield exam topics with expected marks (2M, 6M, 10M).
                ### 3. ⚡ 10-Minute Rapid Revision Summary
                - Point-to-point technical explanation using standard textbook keywords.
                """
                try:
                    sn_res = generate_ai_response(sn_prompt)
                    st.session_state.sn_output_data = sn_res
                    st.session_state.sn_current_chap = sn_chapter
                    st.session_state.sn_current_subj = sn_subject
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation error: {e}")

    if "sn_output_data" in st.session_state and st.session_state.sn_output_data:
        st.markdown("---")
        st.markdown(f"### 📘 Revision Sheet: **{st.session_state.get('sn_current_subj', '').upper()}** — *{st.session_state.get('sn_current_chap', '')}*")
        st.markdown(st.session_state.sn_output_data)
        
        if st.button("🗑️ Clear Short Notes"):
            del st.session_state.sn_output_data
            st.rerun()

# ==================================================
# --- TAB 3: STREAMLINED TOPIC SEARCH ---
# ==================================================
with tab3:
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
            with st.spinner(f"Analyzing '{query}'..."):
                prompt = f"""
                Act as an Engineering Professor for Mumbai University curriculum.
                Provide an academically accurate breakdown for: '{query}'.
                
                Use these 3 exact tags:
                [1_DEF]
                Exact University Standard 2-Mark definition.
                [2_BRK]
                Technical Breakdown: Architecture, internal equations, core components, and diagram notes.
                [3_WRK]
                Working Principle: Step-by-step operational logic and mechanism.
                """
                try:
                    ts_res = generate_ai_response(prompt)
                    st.session_state.research_data = ts_res
                    st.session_state.research_query = query
                    st.rerun()
                except Exception as e: 
                    st.error(f"Error: {e}")

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
            except Exception:
                return "Section parsing error."

        def_text = extract_block("[1_DEF]", "[2_BRK]")
        brk_text = extract_block("[2_BRK]", "[3_WRK]")
        wrk_text = extract_block("[3_WRK]")

        st.markdown(f"## 📘 Technical Report: {q_name}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="blueprint-card" style="border-left: 4px solid #4CAF50;">
                <h4 style="color:#4CAF50; margin-top:0;">1. University Standard Definition</h4>
                <p style="font-size:14px; line-height:1.6;">{def_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="blueprint-card" style="border-left: 4px solid #00F2FE;">
                <h4 style="color:#00F2FE; margin-top:0;">2. Technical Breakdown</h4>
                <p style="font-size:14px; line-height:1.6;">{brk_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""
            <div class="blueprint-card" style="border-left: 4px solid #FFD700;">
                <h4 style="color:#FFD700; margin-top:0;">3. Working Principle</h4>
                <p style="font-size:14px; line-height:1.6;">{wrk_text}</p>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑️ Clear Research"):
            del st.session_state.research_data
            st.rerun()