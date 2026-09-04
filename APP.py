import streamlit as st
import requests
import json
import time
import os
from supabase import create_client, Client

# Safe Secret Helper for Render & Streamlit Environments
def get_env_secret(key, default=""):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)

# --- 1. CONFIGURATION & PAGE SETUP ---
st.set_page_config(
    page_title="TopperGPT Intelligence",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

# --- 2. CSS STYLING MATCHING EXACT DASHBOARD LAYOUT ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* Background grid styling */
.stApp {
    background-color: #0c0d12 !important;
    background-image: 
        linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px) !important;
    background-size: 36px 36px !important;
    color: #f3f4f6 !important;
}

/* Sidebar Customization */
[data-testid="stSidebar"] {
    background-color: #0e0f15 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    padding-top: 15px !important;
}

header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* --- SIDEBAR NAVIGATION UPGRADE --- */
div[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 8px !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
    margin-bottom: 4px !important;
    cursor: pointer !important;
    transition: all 0.2s ease-in-out !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(245, 158, 11, 0.08) !important;
    border-color: rgba(245, 158, 11, 0.3) !important;
    transform: translateX(3px);
}

div[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
    display: none !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label div p {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #cbd5e1 !important;
    letter-spacing: 0.2px !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
    background: #1a1610 !important;
    border: 1px solid #f59e0b !important;
    box-shadow: 0 0 14px rgba(245, 158, 11, 0.2) !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] div p {
    color: #f59e0b !important;
    font-weight: 700 !important;
}

/* --- STATUS WIDGET --- */
.status-card {
    background: linear-gradient(180deg, #161822 0%, #10121a 100%);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 14px;
    padding: 16px 14px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    margin-top: 20px;
}

/* Top Streak Badge */
.streak-badge {
    background: rgba(251, 146, 60, 0.12);
    border: 1px solid rgba(251, 146, 60, 0.4);
    color: #fb923c;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    float: right;
}

/* Prompt Starter Quick Pills */
.starter-chip {
    display: inline-block;
    background: #151722;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 9999px;
    margin-right: 8px;
    margin-bottom: 12px;
}

/* Glassmorphic Dark Cards */
.topper-card {
    background: #13151f;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

/* Chat Bubble Customization */
[data-testid="stChatMessage"] {
    background-color: #13151f !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 12px !important;
    margin-bottom: 12px !important;
}

/* Text Inputs */
.stTextInput > div > div > input {
    background-color: #151722 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #f59e0b !important;
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.2) !important;
}

/* Accent Buttons */
.stButton > button {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
    color: #000000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 16px rgba(245, 158, 11, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CLIENT ---
@st.cache_resource
def init_supabase():
    url = get_env_secret("SUPABASE_URL").strip()
    key = get_env_secret("SUPABASE_KEY").strip()
    return create_client(url, key)

supabase = init_supabase()

# --- 4. BACKEND AI ENGINE (GROQ + GEMINI + OPENROUTER) ---
def generate_ai_response(prompt_text, max_toks=1200):
    groq_key = get_env_secret("GROQ_API_KEY").strip()
    if groq_key:
        try:
            m_res = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {groq_key}"},
                timeout=3
            )
            if m_res.status_code == 200:
                available = [m["id"] for m in m_res.json().get("data", [])]
                chat_models = [m for m in available if not any(x in m for x in ["whisper", "guard", "vision", "embed"])]
                for live_m in chat_models[:2]:
                    try:
                        res = requests.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                            json={
                                "model": live_m,
                                "messages": [{"role": "user", "content": prompt_text}],
                                "temperature": 0.3,
                                "max_tokens": max_toks
                            },
                            timeout=14
                        )
                        if res.status_code == 200:
                            return res.json()["choices"][0]["message"]["content"].strip()
                    except Exception:
                        continue
        except Exception:
            pass

    gemini_key = (get_env_secret("GEMINI_API_KEY") or get_env_secret("GOOGLE_API_KEY", "")).strip()
    if gemini_key:
        for g_model in ["gemini-1.5-flash", "gemini-pro"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={gemini_key}"
                res = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt_text}]}]},
                    timeout=14
                )
                if res.status_code == 200:
                    return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            except Exception:
                continue

    openrouter_key = get_env_secret("OPENROUTER_API_KEY").strip()
    if openrouter_key:
        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                json={
                    "model": "meta-llama/llama-3.1-8b-instruct:free",
                    "messages": [{"role": "user", "content": prompt_text}],
                    "max_tokens": max_toks
                },
                timeout=14
            )
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    raise Exception("Connection timeout. Please retry your request.")

# --- 5. AUTHENTICATION ---
def clean_email_auth():
    if "user_data" not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        st.markdown("""
            <div style="text-align:center; padding: 40px 0 20px 0;">
                <h1 style="color:#ffffff; font-size: 2.8rem; font-weight:800; margin: 10px 0;">
                    Topper<span style="color:#f59e0b;">GPT</span>
                </h1>
                <p style="color:#94a3b8; font-size:15px; margin-top:0;">
                    AI Academic Workspace for Mumbai University Engineering.
                </p>
            </div>
        """, unsafe_allow_html=True)

        _, center_col, _ = st.columns([1, 1.8, 1])
        with center_col:
            auth_tab = st.tabs(["🔑 Quick Access", "📝 New Registration"])
            
            with auth_tab[0]:
                with st.form("quick_login"):
                    l_email = st.text_input("Registered Email Address", placeholder="name@domain.com", key="l_email_quick").strip().lower()
                    if st.form_submit_button("ENTER DASHBOARD 🚀", use_container_width=True):
                        if l_email:
                            try:
                                prof = supabase.table("profiles").select("*").eq("email", l_email).execute()
                                if prof.data:
                                    st.session_state.user_data = prof.data[0]
                                    st.rerun()
                                else:
                                    st.error("Account not found. Please register using the New Registration tab.")
                            except Exception as e:
                                st.error(f"Database error: {e}")
                        else:
                            st.warning("Email is required.")

            with auth_tab[1]:
                with st.form("reg_form_quick"):
                    s_name = st.text_input("Full Name", placeholder="Enter your full name", key="reg_name_quick")
                    s_email = st.text_input("Email Address", placeholder="name@domain.com", key="reg_email_quick").strip().lower()
                    if st.form_submit_button("CREATE ACCOUNT 🔥", use_container_width=True):
                        if s_name and s_email:
                            try:
                                check = supabase.table("profiles").select("*").eq("email", s_email).execute()
                                if check.data:
                                    st.warning("Account already exists. Please log in.")
                                else:
                                    new_u = {"email": s_email, "full_name": s_name}
                                    try:
                                        new_u["is_pro"] = True
                                        ins = supabase.table("profiles").insert(new_u).execute()
                                    except Exception:
                                        new_u.pop("is_pro", None)
                                        ins = supabase.table("profiles").insert(new_u).execute()

                                    if ins.data:
                                        st.session_state.user_data = ins.data[0]
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Server error: {str(e)}")
                        else:
                            st.warning("Please provide all required fields.")
        st.stop()

# --- 6. UNLIMITED ACCESS OVERRIDE (CREDITS TEMPORARILY DISABLED) ---
def check_access():
    return True

def deduct_trial():
    pass

def show_paywall():
    pass

clean_email_auth()

# --- 7. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; padding: 5px 0 20px 4px;">
            <div style="width:12px; height:12px; background:#f59e0b; border-radius:50%; box-shadow: 0 0 10px #f59e0b;"></div>
            <h2 style="color:#ffffff; margin:0; font-size:24px; font-weight:800; letter-spacing:-0.5px;">TopperGPT</h2>
        </div>
    """, unsafe_allow_html=True)

    nav_selection = st.radio(
        "Navigation",
        [
            "💡 AI Tutor",
            "🎯 Predicted Qs",
            "📄 Short Notes",
            "🔍 Topic Research"
        ],
        label_visibility="collapsed"
    )

    st.markdown("""
        <div class="status-card">
            <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                <span style="display:inline-block; width:8px; height:8px; background:#22c55e; border-radius:50%;"></span>
                <span style="color:#22c55e; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px;">SYSTEM UNLOCKED</span>
            </div>
            <h4 style="color:#ffffff; margin:4px 0 2px 0; font-size:16px; font-weight:800;">Academic Access</h4>
            <p style="color:#94a3b8; font-size:12px; margin:0; line-height:1.4;">Unlimited access enabled for all university modules.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 8. TOP HEADER & STREAK BAR ---
student_name = st.session_state.user_data.get("full_name", "Student")
clean_title = nav_selection.split(" ", 1)[1]

col_head, col_badge = st.columns([3, 1])
with col_head:
    st.markdown(f"<h1 style='color:#ffffff; font-size:32px; font-weight:800; margin:0 0 15px 0;'>{clean_title}</h1>", unsafe_allow_html=True)
with col_badge:
    st.markdown("<div class='streak-badge'>🔥 6-day study streak</div>", unsafe_allow_html=True)

# Helper function for Instant Hinglish Translation
def translate_to_hinglish(text_content):
    prompt = f"""Translate and simplify the following engineering explanation into clear, friendly Hinglish (Hindi written in English alphabets) so that an Indian student can understand it effortlessly. Keep all equations and mathematical variables intact.\n\nText:\n{text_content}"""
    return generate_ai_response(prompt, max_toks=1000)

# ==================================================
# --- 1. FEATURE: AI ACADEMIC TUTOR ---
# ==================================================
if nav_selection == "💡 AI Tutor":
    st.markdown("""
        <div>
            <span class="starter-chip">💡 Explain a concept</span>
            <span class="starter-chip">📄 Summarize a chapter</span>
            <span class="starter-chip">🎯 Practice questions</span>
        </div>
    """, unsafe_allow_html=True)

    if "tutor_messages" not in st.session_state:
        st.session_state.tutor_messages = [
            {
                "role": "assistant",
                "content": f"Hello {student_name} 👋 What are we studying today? Ask me anything from your syllabus.",
                "hinglish": None
            }
        ]

    for idx, msg in enumerate(st.session_state.tutor_messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and idx > 0:
                if msg.get("hinglish"):
                    with st.expander("🗣️ View Hinglish Explanation"):
                        st.markdown(msg["hinglish"])
                else:
                    if st.button("🗣️ Explain in Hinglish", key=f"tr_{idx}"):
                        with st.spinner("Translating to simple Hinglish..."):
                            h_res = translate_to_hinglish(msg["content"])
                            st.session_state.tutor_messages[idx]["hinglish"] = h_res
                            st.rerun()

    user_query = st.chat_input("Ask a doubt, request notes, or get PYQs...")

    if user_query:
        st.session_state.tutor_messages.append({"role": "user", "content": user_query, "hinglish": None})
        with st.chat_message("user"):
            st.markdown(user_query)

        tutor_prompt = f"""
        You are TopperGPT's Senior Academic Evaluator for Mumbai University Engineering (C-Scheme).
        Respond exclusively in professional, clear, exam-oriented English.

        Student Query: "{user_query}"

        1. If conversational (greetings, general chat): Reply politely and concisely in 1-2 sentences.
        2. If academic: Use the strict 3-block structure:
           ### 📌 1. University Standard Definition (2-Mark Standard)
           Accurate textbook definition and mandatory examiner keywords.

           ### ⚡ 2. Step-by-Step Technical Execution & Derivation
           Logically organized steps, formulas with Markdown LaTeX ($...$ or $$...$$), and specific 'Exam Diagram Requirement' if applicable.

           ### ⚠️ 3. Examiner Trap Alert
           Precise calculation error, unit conversion, or assumption where students frequently lose marks.
        """

        with st.chat_message("assistant"):
            with st.spinner("Analyzing syllabus and evaluation rubrics..."):
                try:
                    ai_reply = generate_ai_response(tutor_prompt)
                    st.markdown(ai_reply)
                    st.session_state.tutor_messages.append({"role": "assistant", "content": ai_reply, "hinglish": None})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ==================================================
# --- 2. FEATURE: PREDICTED QUESTIONS ---
# ==================================================
elif nav_selection == "🎯 Predicted Qs":
    st.markdown("""
        <div class="topper-card">
            <h3 style="margin-top:0; color:#f59e0b;">Target High-Probability Examination Questions</h3>
            <p style="color:#94a3b8; font-size:14px; margin:0;">
                Predict recurring Mumbai University questions, examiner marking rubrics, and previous year variations.
            </p>
        </div>
    """, unsafe_allow_html=True)

    p_topic = st.text_input("Enter Topic or Module Name:", placeholder="e.g. Runge-Kutta 4th Order, Virtual Memory, BJT Biasing, Trees", key="pred_topic_input")

    if st.button("Generate Exam Blueprint ⚡", use_container_width=True):
        if not p_topic.strip():
            st.warning("Please enter a valid topic or chapter name.")
        else:
            with st.spinner(f"Extracting examination patterns for '{p_topic}'..."):
                pred_prompt = f"""
                You are a Senior Mumbai University Engineering Paper Setter.
                Target Topic: {p_topic}
                Language: Strictly Professional English.

                Produce:
                ### SECTION 1: 🎯 Top 5 Most Repeated Exam Questions
                List 5 high-probability questions ([2M], [6M], [10M]).
                Format each item as:
                **Q[Number] ([Marks]M) | [Expected Recurrence Probability]**
                - **Question:** [Authentic examination question statement]
                - **Marking Rubric:** [Specific score breakdown]
                - **Examiner Trap:** [Common calculation or conceptual mistake]

                ---

                ### SECTION 2: 📚 Historical PYQ Archive
                - **2-Mark Short Concepts & Definitions** (3 items)
                - **6-Mark Analytical & Derivations** (3 items)
                - **10-Mark Comprehensive Numericals** (2 items with full parameters)
                """
                try:
                    res_text = generate_ai_response(pred_prompt)
                    st.session_state.pred_result = res_text
                    st.session_state.pred_topic_name = p_topic
                    st.session_state.pred_hinglish = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    if "pred_result" in st.session_state and st.session_state.pred_result:
        st.markdown("---")
        st.markdown(f"### 📘 Exam Blueprint: **{st.session_state.get('pred_topic_name', '').upper()}**")
        st.markdown(st.session_state.pred_result)

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            if not st.session_state.get("pred_hinglish"):
                if st.button("🗣️ Translate to Hinglish", key="trans_pred"):
                    with st.spinner("Translating blueprint to Hinglish..."):
                        st.session_state.pred_hinglish = translate_to_hinglish(st.session_state.pred_result)
                        st.rerun()
        with col_act2:
            st.download_button(
                "📥 Download Blueprint",
                data=st.session_state.pred_result,
                file_name=f"{st.session_state.get('pred_topic_name', 'Topic')}_MU_Blueprint.md",
                mime="text/markdown",
                use_container_width=True
            )

        if st.session_state.get("pred_hinglish"):
            with st.expander("🗣️ View Hinglish Blueprint Translation", expanded=True):
                st.markdown(st.session_state.pred_hinglish)

# ==================================================
# --- 3. FEATURE: CHAPTER SHORT-NOTES ---
# ==================================================
elif nav_selection == "📄 Short Notes":
    st.markdown("""
        <div class="topper-card">
            <h3 style="margin-top:0; color:#f59e0b;">1-Page Exam Cheat Sheet</h3>
            <p style="color:#94a3b8; font-size:14px; margin:0;">
                Synthesize high-yield formulas with proper SI units, high-scoring modules, and rapid revision notes.
            </p>
        </div>
    """, unsafe_allow_html=True)

    sn_topic = st.text_input("Enter Chapter / Module Name:", placeholder="e.g. Semiconductor Physics, AC Circuits, Interpolation", key="sn_topic_input")

    if st.button("Generate Revision Sheet 📑", use_container_width=True):
        if not sn_topic.strip():
            st.warning("Please enter a chapter name.")
        else:
            with st.spinner(f"Compiling notes for '{sn_topic}'..."):
                sn_prompt = f"""
                Act as a Principal Mumbai University Engineering Professor.
                Target Chapter: {sn_topic}
                Language: Strictly Professional English.

                Do not use markdown tables for equations. Use clean Markdown LaTeX ($$ display blocks).

                OUTPUT:
                ### 1. 🧮 Core Numerical Formulas & Parameters
                List the 5-7 most essential formulas:
                * **[Formula Name]**
                  $$[Formula in LaTeX]$$
                  - **Variables & SI Units:** Descriptions with standard units.
                  - **Exam Application:** Where this formula is needed.

                ---

                ### 2. 🎯 High-Weightage Core Topics
                List top 4 must-prepare topics with expected marks ([6M] or [10M]) and key requirements.

                ---

                ### 3. ⚡ 5-Minute Rapid Revision Keywords
                5 concise high-yield points with examiner-targeted terminology in bold.
                """
                try:
                    sn_res = generate_ai_response(sn_prompt)
                    st.session_state.sn_data = sn_res
                    st.session_state.sn_name = sn_topic
                    st.session_state.sn_hinglish = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    if "sn_data" in st.session_state and st.session_state.sn_data:
        st.markdown("---")
        st.markdown(f"### 📘 Revision Sheet: **{st.session_state.get('sn_name', '').upper()}**")
        st.markdown(st.session_state.sn_data)

        col_sn1, col_sn2 = st.columns([1, 1])
        with col_sn1:
            if not st.session_state.get("sn_hinglish"):
                if st.button("🗣️ Translate to Hinglish", key="trans_sn"):
                    with st.spinner("Translating cheat sheet to Hinglish..."):
                        st.session_state.sn_hinglish = translate_to_hinglish(st.session_state.sn_data)
                        st.rerun()
        with col_sn2:
            st.download_button(
                "📥 Download Markdown Sheet",
                data=st.session_state.sn_data,
                file_name=f"{st.session_state.get('sn_name', 'Revision')}_CheatSheet.md",
                mime="text/markdown",
                use_container_width=True
            )

        if st.session_state.get("sn_hinglish"):
            with st.expander("🗣️ View Hinglish Cheat Sheet Translation", expanded=True):
                st.markdown(st.session_state.sn_hinglish)

# ==================================================
# --- 4. FEATURE: TOPIC RESEARCH (ZERO-FAIL JSON PARSING) ---
# ==================================================
elif nav_selection == "🔍 Topic Research":
    st.markdown("""
        <div class="topper-card">
            <h3 style="margin-top:0; color:#f59e0b;">Streamlined Concept Breakdown</h3>
            <p style="color:#94a3b8; font-size:14px; margin:0;">
                Get university-standard definitions, technical breakdowns, and working principles in 3 clean cards.
            </p>
        </div>
    """, unsafe_allow_html=True)

    topic_q = st.text_input("Enter Concept to Research:", placeholder="e.g. Transformer, BJT Biasing, Process Scheduling, Op-Amp", key="res_q_input")

    if st.button("Execute Deep Research ⚡", use_container_width=True):
        if not topic_q.strip():
            st.warning("Please enter a concept name.")
        else:
            with st.spinner(f"Analyzing '{topic_q}'..."):
                res_prompt = f"""
                You are a Senior Mumbai University Engineering Professor.
                Target Topic: "{topic_q}"
                Language: Strictly Professional English.

                Return ONLY a valid JSON object. Do NOT include any intro, draft thoughts, reasoning, or backticks around the json.
                JSON structure must be exactly:
                {{
                  "definition": "Official 2-mark university textbook definition with examiner keywords.",
                  "breakdown": "Technical breakdown covering architecture, circuit configurations, and key governing formulas written in clean LaTeX ($...$ or $$...$$).",
                  "working_principle": "Step-by-step physical or operational working principle with clear cause-and-effect flow."
                }}
                """
                try:
                    r_res = generate_ai_response(res_prompt, max_toks=1200)
                    
                    cleaned_json_str = r_res.strip()
                    if cleaned_json_str.startswith("```json"):
                        cleaned_json_str = cleaned_json_str[7:]
                    if cleaned_json_str.startswith("```"):
                        cleaned_json_str = cleaned_json_str[3:]
                    if cleaned_json_str.endswith("```"):
                        cleaned_json_str = cleaned_json_str[:-3]
                    cleaned_json_str = cleaned_json_str.strip()

                    parsed_data = json.loads(cleaned_json_str)
                    st.session_state.topic_res_json = parsed_data
                    st.session_state.topic_res_name = topic_q
                    st.rerun()
                except Exception:
                    st.session_state.topic_res_json = {
                        "definition": "Standard definition currently being processed. Please re-run once.",
                        "breakdown": r_res,
                        "working_principle": "Detailed breakdown displayed above."
                    }
                    st.session_state.topic_res_name = topic_q
                    st.rerun()

    if "topic_res_json" in st.session_state and st.session_state.topic_res_json:
        t_data = st.session_state.topic_res_json
        t_name = st.session_state.topic_res_name

        st.markdown(f"### 📘 Technical Report: **{t_name.upper()}**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.container(border=True):
                st.markdown("<h4 style='color:#f59e0b; margin-top:0;'>1. Official Definition</h4>", unsafe_allow_html=True)
                st.markdown(t_data.get("definition", "Details unavailable."))
                
        with col2:
            with st.container(border=True):
                st.markdown("<h4 style='color:#00F2FE; margin-top:0;'>2. Technical Breakdown</h4>", unsafe_allow_html=True)
                st.markdown(t_data.get("breakdown", "Details unavailable."))
                
        with col3:
            with st.container(border=True):
                st.markdown("<h4 style='color:#22c55e; margin-top:0;'>3. Working Principle</h4>", unsafe_allow_html=True)
                st.markdown(t_data.get("working_principle", "Details unavailable."))

        if st.button("🗑️ Clear Research"):
            del st.session_state.topic_res_json
            st.rerun()