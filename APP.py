import streamlit as st
import requests
import json
import time 
import hashlib
from supabase import create_client, Client

# --- 1. CONFIGURATION & BROWSER TAB ---
st.set_page_config(
    page_title="TopperGPT Intelligence",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

# --- 2. THEME INJECTION (MATCHING LANDING PAGE DESIGN) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* Background with Subtle Tech Grid */
.stApp {
    background-color: #08090a !important;
    background-image: 
        linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px) !important;
    background-size: 38px 38px !important;
    color: #f3f4f6 !important;
}

/* Sidebar Dark Glass */
[data-testid="stSidebar"] {
    background-color: #0b0d10 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Top App Header Removal */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Glowing Badges & Labels */
.badge-pill {
    display: inline-block;
    padding: 4px 12px;
    background: rgba(78, 237, 216, 0.1);
    border: 1px solid #4eedd8;
    color: #4eedd8;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-radius: 9999px;
    margin-bottom: 12px;
    box-shadow: 0 0 12px rgba(78, 237, 216, 0.2);
}

/* Card Boxes */
.topper-card {
    background: #0e1217;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
}

/* Input Fields Styling */
.stTextInput > div > div > input {
    background-color: #12171f !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
    transition: all 0.2s ease;
}
.stTextInput > div > div > input:focus {
    border-color: #4eedd8 !important;
    box-shadow: 0 0 14px rgba(78, 237, 216, 0.3) !important;
}

/* Custom Action Buttons */
.stButton > button {
    background: linear-gradient(135deg, #4eedd8 0%, #22c55e 100%) !important;
    color: #050608 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    letter-spacing: 0.02em !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 24px !important;
    box-shadow: 0 0 18px rgba(78, 237, 216, 0.3) !important;
    transition: all 0.25s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 26px rgba(78, 237, 216, 0.5) !important;
}

/* Tab Navigation Styling */
.stTabs [data-baseweb="tab-list"] {
    background: #0e1217;
    padding: 6px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    color: #9ca3af !important;
    font-weight: 600;
    padding: 10px 20px;
}
.stTabs [aria-selected="true"] {
    background-color: #161c24 !important;
    color: #4eedd8 !important;
    border: 1px solid rgba(78, 237, 216, 0.3) !important;
}

/* Trial Profile Widget */
.profile-stat-box {
    background: linear-gradient(135deg, #0e1217 0%, #161e27 100%);
    border: 1px solid rgba(78, 237, 216, 0.4);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 0 20px rgba(78, 237, 216, 0.1);
}
</style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE INITIALIZATION ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"].strip()
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

# --- 4. BACKEND AI ENGINE (AUTODISCOVERY + FALLBACK) ---
def generate_ai_response(prompt_text):
    errors = []

    # Tier 1: Groq Dynamic Active Models
    groq_key = st.secrets.get("GROQ_API_KEY", "").strip()
    if groq_key:
        try:
            m_res = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {groq_key}"},
                timeout=4
            )
            if m_res.status_code == 200:
                available_models = [m["id"] for m in m_res.json().get("data", [])]
                chat_models = [
                    m for m in available_models 
                    if not any(x in m for x in ["whisper", "guard", "vision", "embed"])
                ]
                for live_model in chat_models[:2]:
                    try:
                        res = requests.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {groq_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": live_model,
                                "messages": [{"role": "user", "content": prompt_text}],
                                "temperature": 0.4,
                                "max_tokens": 1200
                            },
                            timeout=12
                        )
                        if res.status_code == 200:
                            return res.json()["choices"][0]["message"]["content"].strip()
                    except Exception:
                        continue
        except Exception as e:
            errors.append(f"Groq: {str(e)}")

    # Tier 2: OpenRouter Direct Fallback
    openrouter_key = st.secrets.get("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        for or_m in ["meta-llama/llama-3.1-8b-instruct:free", "google/gemma-2-9b-it:free"]:
            try:
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://toppergpt-live.streamlit.app",
                        "X-Title": "TopperGPT"
                    },
                    json={
                        "model": or_m,
                        "messages": [{"role": "user", "content": prompt_text}],
                        "max_tokens": 1200
                    },
                    timeout=12
                )
                if res.status_code == 200:
                    resp_data = res.json()
                    if "choices" in resp_data and len(resp_data["choices"]) > 0:
                        return resp_data["choices"][0]["message"]["content"].strip()
            except Exception:
                continue

    raise Exception("Network slow hai bhai, ek baar dubara generate click karo.")

# --- 5. AUTHENTICATION ---
def clean_email_auth():
    if "user_data" not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        st.markdown("""
            <div style="text-align:center; padding: 40px 0 20px 0;">
                <span class="badge-pill">AI-POWERED LEARNING PLATFORM</span>
                <h1 style="color:#ffffff; font-size: 3.2rem; font-weight:800; margin: 10px 0;">
                    Study Smarter with <span style="color:#4eedd8;">TopperGPT</span>
                </h1>
                <p style="color:#8b949e; font-size:16px; margin-top:0;">
                    The AI intelligence engine built specifically for Mumbai University Engineering students.
                </p>
            </div>
        """, unsafe_allow_html=True)

        _, center_col, _ = st.columns([1, 1.8, 1])
        with center_col:
            auth_tab = st.tabs(["🔑 Quick Access", "📝 New Registration"])
            
            with auth_tab[0]:
                with st.form("quick_login"):
                    l_email = st.text_input("Registered Email Address", placeholder="name@domain.com", key="l_email_quick").strip().lower()
                    if st.form_submit_button("ENTER WORKSPACE 🚀", use_container_width=True):
                        if l_email:
                            try:
                                prof = supabase.table("profiles").select("*").eq("email", l_email).execute()
                                if prof.data:
                                    st.session_state.user_data = prof.data[0]
                                    st.rerun()
                                else:
                                    st.error("Account nahi mila. New Registration tab use karo.")
                            except Exception as e:
                                st.error(f"Database error: {e}")
                        else:
                            st.warning("Email required!")

            with auth_tab[1]:
                with st.form("reg_form_quick"):
                    st.caption("✨ Create your account to receive 10 complimentary intelligence trials.")
                    s_name = st.text_input("Full Name", placeholder="Krishna", key="reg_name_quick")
                    s_email = st.text_input("Email Address", placeholder="krishna@example.com", key="reg_email_quick").strip().lower()
                    
                    if st.form_submit_button("CREATE FREE ACCOUNT 🔥", use_container_width=True):
                        if s_name and s_email:
                            try:
                                check = supabase.table("profiles").select("*").eq("email", s_email).execute()
                                if check.data:
                                    st.warning("Account already exists! Use Quick Access.")
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
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Server error: {str(e)}")
                        else:
                            st.warning("Fill in all details.")
        st.stop()

# --- 6. ACCESS CHECK ---
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
    st.markdown("""
    <div style="background: #0e1217; border: 1px solid #ef4444; border-radius: 16px; padding: 25px; text-align: center; margin: 20px 0;">
        <h3 style="color:#ef4444; margin-top:0;">🚨 Free Trials Exhausted</h3>
        <p style="color:#9ca3af; font-size:14px;">Upgrade to unlock unlimited high-speed predictions, cheat sheets, and step-by-step solutions.</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="topper-card" style="border: 2px solid #4eedd8; text-align:center;">
            <span class="badge-pill">MONTHLY PASS</span>
            <h1 style="color:#ffffff; font-size:36px; margin: 10px 0;">₹49</h1>
            <p style="color:#8b949e; font-size:13px;">30 Days Unlimited Access Across All Modules</p>
            <a href="https://rzp.io/rzp/AWiyLxEi" target="_blank" style="background:#4eedd8; color:#050608; padding:12px 24px; border-radius:10px; text-decoration:none; display:inline-block; font-weight:bold; margin-top:10px;">Activate Monthly</a>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="topper-card" style="border: 2px solid #22c55e; text-align:center;">
            <span class="badge-pill" style="border-color:#22c55e; color:#22c55e;">SEMESTER PASS</span>
            <h1 style="color:#ffffff; font-size:36px; margin: 10px 0;">₹199</h1>
            <p style="color:#8b949e; font-size:13px;">Full Semester Coverage + Priority Paper Review</p>
            <a href="https://rzp.io/rzp/hXcR54E" target="_blank" style="background:#22c55e; color:#050608; padding:12px 24px; border-radius:10px; text-decoration:none; display:inline-block; font-weight:bold; margin-top:10px;">Activate Semester</a>
        </div>
        """, unsafe_allow_html=True)

clean_email_auth()

# --- 7. SIDEBAR DASHBOARD ---
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 20px 0;">
            <h2 style="color:#ffffff; margin:0; font-weight:800; letter-spacing:-0.5px;">
                Topper<span style="color:#4eedd8;">GPT</span>
            </h2>
            <p style="color:#8b949e; font-size:12px; margin:2px 0 0 0;">Precision Academic Intelligence</p>
        </div>
    """, unsafe_allow_html=True)

    user = st.session_state.user_data
    is_pro = user.get("is_pro", False)
    trials = user.get("free_trials_left", 10)

    if is_pro:
        st.markdown("""
            <div class="profile-stat-box" style="border-color:#4eedd8;">
                <span class="badge-pill">ACCOUNT STATUS</span>
                <h3 style="margin:8px 0; color:#ffffff;">👑 PRO UNLIMITED</h3>
                <p style="margin:0; font-size:12px; color:#8b949e;">Full University Engine Unlocked</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="profile-stat-box">
                <span class="badge-pill">STUDENT ACCESS</span>
                <h1 style="margin:5px 0; color:#ffffff; font-size:42px; font-weight:800;">{trials}<span style="font-size:20px; color:#8b949e;">/10</span></h1>
                <p style="margin:0; font-size:12px; color:#8b949e;">Free Intelligence Credits Remaining</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔓 End Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 8. HERO GREETING ---
student_name = st.session_state.user_data.get("full_name", "Student")
st.markdown(f"""
    <div style="padding: 15px 0 25px 0;">
        <span class="badge-pill">DASHBOARD ACTIVE</span>
        <h1 style="color:#ffffff; font-size: 2.4rem; font-weight:800; margin: 4px 0;">
            Hello, {student_name} 👋
        </h1>
        <p style="color:#8b949e; font-size:15px; margin:0;">
            Ready to analyze Mumbai University patterns and generate exam-grade notes?
        </p>
    </div>
""", unsafe_allow_html=True)

# --- 9. CORE APPLICATION SUITE ---
main_tab1, main_tab2, main_tab3 = st.tabs([
    "🎯 Predicted Questions", 
    "📝 Chapter Short-Notes", 
    "🔍 Topic Breakdown"
])

# ==================================================
# --- TAB 1: PREDICTED QUESTIONS ENGINE ---
# ==================================================
with main_tab1:
    st.markdown("""
        <div class="topper-card">
            <h3 style="margin-top:0; color:#4eedd8;">🎯 MU Exam Sniper: High-Probability Questions</h3>
            <p style="color:#8b949e; font-size:14px;">Instant prediction of top recurring questions, examiner marking rubrics, and historical variations.</p>
        </div>
    """, unsafe_allow_html=True)

    p_topic = st.text_input(
        "Enter Topic / Module / Concept:", 
        placeholder="e.g. Runge-Kutta 4th Order, Trees & Graphs, PN Junction, Complex Integration", 
        key="p_topic_sniper"
    )

    if st.button("⚡ EXTRACT EXAM BLUEPRINT", use_container_width=True):
        if not p_topic.strip():
            st.warning("Pehle koi topic enter karo!")
        elif not check_access():
            show_paywall()
        else:
            deduct_trial()
            with st.spinner(f"Extracting MU patterns for '{p_topic}'..."):
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

    if "p_clean_out" in st.session_state and st.session_state.p_clean_out:
        st.markdown("---")
        st.markdown(f"### 📘 Exam Target Sheet: **{st.session_state.get('p_clean_topic', '').upper()}**")
        st.markdown(st.session_state.p_clean_out)

        # Pro Upsell Banner Matching Landing Page Neon Style
        st.markdown("""
            <div class="topper-card" style="border: 2px solid #4eedd8; text-align: center; margin-top: 30px;">
                <h3 style="color: #4eedd8; margin-top: 0;">💡 Need Step-by-Step Model Solved Answers?</h3>
                <p style="color: #9ca3af; font-size: 14px;">
                    Unlock Mumbai University standard solutions, step-by-step mathematical proofs, and solved numerical steps with TopperGPT PRO.
                </p>
                <a href="https://rzp.io/rzp/AWiyLxEi" target="_blank" style="background: #4eedd8; color: #050608; padding: 10px 24px; border-radius: 10px; text-decoration: none; font-weight: 700; display: inline-block; margin-top: 8px;">
                    🔓 Unlock Complete Solutions (₹49)
                </a>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Search Another Topic"):
            del st.session_state.p_clean_out
            st.rerun()

# ==================================================
# --- TAB 2: CHAPTER SHORT-NOTES GENERATOR ---
# ==================================================
with main_tab2:
    st.markdown("""
        <div class="topper-card">
            <h3 style="margin-top:0; color:#00F2FE;">📝 1-Page Exam Cheat Sheet</h3>
            <p style="color:#8b949e; font-size:14px;">Generate clean mathematical equations with units, scoring priorities, and rapid keywords.</p>
        </div>
    """, unsafe_allow_html=True)

    sn_chapter = st.text_input(
        "Enter Chapter / Module Name:", 
        placeholder="e.g. Semiconductor Physics, AC Circuits, Interpolation, Trees", 
        key="sn_chap_input_styled"
    )

    if st.button("📑 GENERATE REVISION SHEET", use_container_width=True):
        if not sn_chapter.strip():
            st.warning("Chapter ka naam enter karo!")
        elif not check_access():
            show_paywall()
        else:
            deduct_trial()
            with st.spinner(f"Synthesizing revision sheet for '{sn_chapter}'..."):
                sn_prompt = f"""
                Act as a Principal Mumbai University (MU) Engineering Professor.
                Target Chapter/Module: {sn_chapter}
                
                Generate an ultra-clean, high-yield 1-page revision sheet for last-minute exam preparation.
                
                CRITICAL FORMATTING INSTRUCTIONS:
                - DO NOT use markdown tables for formulas because LaTeX breaks inside table cells.
                - Use clear standalone bullets and clean display equations using $$...$$ or $...$.
                - Ensure all equations render cleanly without raw LaTeX source tags showing.
                
                OUTPUT STRUCTURE:
                
                ### 1. 🧮 Core Exam Formulas & Calculation Traps
                Provide the top 5 to 7 most critical numerical formulas for this chapter.
                Format each formula as:
                * **[Formula Name / Purpose]**
                  $$[Formula in clean LaTeX]$$
                  - **Variables & Units:** Parameter names with standard SI units.
                  - **Where to apply:** 1 line stating the exact problem type where this formula is required.
                
                ---
                
                ### 2. 🎯 High-Weightage Exam Topics (Scoring Priority)
                List the top 4 must-prepare core topics for this module:
                * **[Topic Name]** ([Marks]M - e.g., 6M Derivation or 10M Numerical)
                  - **Expected Question Type:** (e.g. Derive expression with neat diagram, Numerical calculation).
                  - **Mandatory Keywords:** Words and laws the examiner looks for.
                
                ---
                
                ### 3. ⚡ 5-Minute Rapid Revision Keywords
                Provide 5 concise, high-impact technical summary points with textbook-standard terms highlighted in bold.
                """
                try:
                    sn_res = generate_ai_response(sn_prompt)
                    st.session_state.sn_output_data = sn_res
                    st.session_state.sn_current_chap = sn_chapter
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation error: {e}")

    if "sn_output_data" in st.session_state and st.session_state.sn_output_data:
        st.markdown("---")
        st.markdown(f"### 📘 High-Yield Revision Sheet: **{st.session_state.get('sn_current_chap', '').upper()}**")
        st.markdown(st.session_state.sn_output_data)

        st.markdown("""
            <div class="topper-card" style="border: 2px solid #22c55e; text-align: center; margin-top: 30px;">
                <h3 style="color: #22c55e; margin-top: 0;">📚 Need Full Handwritten-Style Solved Proofs?</h3>
                <p style="color: #9ca3af; font-size: 14px;">
                    Get access to complete solved derivations and formula proofs formatted for full examiner credit.
                </p>
                <a href="https://rzp.io/rzp/AWiyLxEi" target="_blank" style="background: #22c55e; color: #050608; padding: 10px 24px; border-radius: 10px; text-decoration: none; font-weight: 700; display: inline-block; margin-top: 8px;">
                    🔓 Unlock Complete Exam Pack (₹49)
                </a>
            </div>
        """, unsafe_allow_html=True)

        c_sn1, c_sn2 = st.columns(2)
        with c_sn1:
            if st.button("🗑️ Clear Revision Sheet", use_container_width=True):
                del st.session_state.sn_output_data
                st.rerun()
        with c_sn2:
            st.download_button(
                label="📥 Download Markdown Sheet",
                data=st.session_state.sn_output_data,
                file_name=f"{st.session_state.get('sn_current_chap', 'Sheet')}_MU_Revision.md",
                mime="text/markdown",
                use_container_width=True
            )

# ==================================================
# --- TAB 3: STREAMLINED TOPIC BREAKDOWN ---
# ==================================================
with main_tab3:
    st.markdown("""
        <div class="topper-card">
            <h3 style="margin-top:0; color:#facc15;">🔍 Streamlined 3-Card Concept Breakdown</h3>
            <p style="color:#8b949e; font-size:14px;">Instant precision report covering definition, technical breakdown, and operational principle.</p>
        </div>
    """, unsafe_allow_html=True)

    query = st.text_input("Enter Concept to Research:", placeholder="e.g. Transformer on No Load, Virtual Memory, BJT Biasing", key="topic_search_styled")

    if st.button("⚡ EXECUTE DEEP RESEARCH", use_container_width=True):
        if not query.strip():
            st.warning("Pehle koi topic likho!")
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
                Exact University Standard 2-Mark definition as expected by MU checkers.
                [2_BRK]
                Technical Breakdown: Core equations, architecture parameters, and diagram requirements.
                [3_WRK]
                Working Principle: Step-by-step operational mechanics.
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

        st.markdown(f"### 📘 Technical Report: **{q_name.upper()}**")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="topper-card" style="border-left: 4px solid #4eedd8;">
                <h4 style="color:#4eedd8; margin-top:0;">1. University Standard Definition</h4>
                <p style="font-size:14px; line-height:1.6; color:#d1d5db;">{def_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="topper-card" style="border-left: 4px solid #00F2FE;">
                <h4 style="color:#00F2FE; margin-top:0;">2. Technical Breakdown</h4>
                <p style="font-size:14px; line-height:1.6; color:#d1d5db;">{brk_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""
            <div class="topper-card" style="border-left: 4px solid #facc15;">
                <h4 style="color:#facc15; margin-top:0;">3. Working Principle</h4>
                <p style="font-size:14px; line-height:1.6; color:#d1d5db;">{wrk_text}</p>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑️ Clear Research"):
            del st.session_state.research_data
            st.rerun()