import streamlit as st
import requests
import json
import time
import os
from supabase import create_client, Client
from landing_page import render_landing_page

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
    page_title="TopperGPT - AI Academic Workspace",
    layout="wide",
    page_icon="🎓"
)

# Route & Query Parameter Handler (Safe extraction)
try:
    qp_page = str(st.query_params.get("page") or "").strip().lower()
except Exception:
    qp_page = ""

try:
    qp_query = str(st.query_params.get("query") or "").strip()
except Exception:
    qp_query = ""

try:
    qp_feature = str(st.query_params.get("feature") or "").strip().lower()
except Exception:
    qp_feature = ""

if qp_query and "pending_query" not in st.session_state:
    st.session_state.pending_query = qp_query

if qp_feature and "pending_feature" not in st.session_state:
    st.session_state.pending_feature = qp_feature

# Default: If not logged in and not requesting login page, render landing page
if st.session_state.get("user_data") is None and qp_page != "login":
    render_landing_page()
    st.stop()

# --- 2. CSS STYLING MATCHING EXACT DASHBOARD LAYOUT ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700;800&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', 'Plus Jakarta Sans', -apple-system, sans-serif !important;
}

/* Background grid styling matching cyber-cyan landing page */
.stApp {
    background-color: #030303 !important;
    background-image: 
        radial-gradient(circle at 50% 8%, rgba(88, 193, 200, 0.12) 0%, transparent 60%),
        linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px) !important;
    background-size: 100% 100%, 36px 36px, 36px 36px !important;
    color: #f3f4f6 !important;
}

/* Sidebar Customization */
[data-testid="stSidebar"] {
    background-color: #060709 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
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
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
    margin-bottom: 4px !important;
    cursor: pointer !important;
    transition: all 0.2s ease-in-out !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(88, 193, 200, 0.06) !important;
    border-color: rgba(88, 193, 200, 0.35) !important;
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
    background: rgba(88, 193, 200, 0.09) !important;
    border: 1px solid #58c1c8 !important;
    box-shadow: 0 0 16px rgba(88, 193, 200, 0.25) !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] div p {
    color: #58c1c8 !important;
    font-weight: 700 !important;
}

/* --- STATUS WIDGET --- */
.status-card {
    background: #08090d;
    border: 1px solid rgba(88, 193, 200, 0.3);
    border-radius: 14px;
    padding: 16px 14px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    margin-top: 20px;
}

/* Top Streak Badge */
.streak-badge {
    background: rgba(88, 193, 200, 0.12);
    border: 1px solid rgba(88, 193, 200, 0.4);
    color: #58c1c8;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    float: right;
    box-shadow: 0 0 12px rgba(88, 193, 200, 0.2);
}

/* Prompt Starter Quick Pills */
.starter-chip {
    display: inline-block;
    background: #08090d;
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 9999px;
    margin-right: 8px;
    margin-bottom: 12px;
    transition: all 0.2s ease;
}
.starter-chip:hover {
    border-color: #58c1c8;
    color: #58c1c8;
    box-shadow: 0 0 12px rgba(88, 193, 200, 0.25);
}

/* Glassmorphic Dark Cards */
.topper-card {
    background: #08090d;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

/* Chat Bubble Customization */
[data-testid="stChatMessage"] {
    background-color: #08090d !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    margin-bottom: 12px !important;
}

/* Text Inputs */
.stTextInput > div > div > input {
    background-color: #08090d !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #58c1c8 !important;
    box-shadow: 0 0 14px rgba(88, 193, 200, 0.25) !important;
}

/* Chat Input */
[data-testid="stChatInput"] textarea {
    background-color: #08090d !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #58c1c8 !important;
    box-shadow: 0 0 14px rgba(88, 193, 200, 0.25) !important;
}

/* Cyber-Cyan Accent Buttons */
.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, rgb(88, 193, 200) 0%, rgb(40, 155, 165) 100%) !important;
    color: #000000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 18px rgba(88, 193, 200, 0.45) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #08090d;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.stTabs [data-baseweb="tab"] {
    color: #94a3b8;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    color: #58c1c8 !important;
    border-bottom-color: #58c1c8 !important;
}
</style>
""", unsafe_allow_html=True)

# --- 3. SUPABASE CLIENT ---
@st.cache_resource
def init_supabase():
    url = get_env_secret("SUPABASE_URL").strip()
    key = get_env_secret("SUPABASE_KEY").strip()
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"Notice: Supabase init skipped or credentials not configured: {e}")
        return None

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
        for g_model in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]:
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
        or_models = [
            "openrouter/auto",
            "google/gemma-4-26b-a4b-it:free",
            "liquid/lfm-2.5-2.6b:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mistral-7b-instruct:free"
        ]
        for or_m in or_models:
            try:
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://toppergpt.in",
                        "X-Title": "TopperGPT Academic Workspace"
                    },
                    json={
                        "model": or_m,
                        "messages": [{"role": "user", "content": prompt_text}],
                        "max_tokens": max_toks
                    },
                    timeout=14
                )
                if res.status_code == 200:
                    choices = res.json().get("choices", [])
                    if choices and "message" in choices[0] and choices[0]["message"].get("content"):
                        return choices[0]["message"]["content"].strip()
            except Exception:
                continue

    # Graceful fallback to knowledge base if remote AI providers are unavailable
    try:
        from knowledge_base import PYQ_DATA
        low_p = prompt_text.lower()
        matched = []
        for subj, notes in PYQ_DATA.items():
            if any(term in low_p for term in subj.split()):
                matched.append(f"### 📘 Authentic MU Exam Knowledge: {subj.upper()}\n{notes.strip()}")
        if matched:
            return "\n\n".join(matched[:2])
    except Exception:
        pass

    return "### 📌 Core Concept\nWe are currently analyzing this syllabus question with high-yield university exam patterns. Please refresh or retry in a moment."

# --- 5. AUTHENTICATION ---
def clean_email_auth():
    if "user_data" not in st.session_state:
        st.session_state.user_data = None

    if st.session_state.user_data is None:
        col_back, _ = st.columns([1, 5])
        with col_back:
            if st.button("← Back to Home"):
                st.query_params.clear()
                st.rerun()

        st.markdown("""
            <div style="text-align:center; padding: 20px 0 10px 0;">
                <h1 style="color:#ffffff; font-size: 2.8rem; font-weight:800; margin: 10px 0;">
                    Topper<span style="color:#58c1c8;">GPT</span>
                </h1>
                <p style="color:#94a3b8; font-size:15px; margin-top:0;">
                    AI Academic Workspace for Mumbai University Engineering.
                </p>
            </div>
        """, unsafe_allow_html=True)

        if "pending_query" in st.session_state and st.session_state.pending_query:
            st.markdown(f"""
                <div style="background: rgba(88, 193, 200, 0.1); border: 1px solid rgba(88, 193, 200, 0.35); border-radius: 12px; padding: 12px 18px; margin: 0 auto 20px auto; max-width: 580px; text-align: center;">
                    <span style="color: #58c1c8; font-weight: 700; font-size: 13px;">✦ QUESTION CAPTURED:</span>
                    <span style="color: #ffffff; font-weight: 600;"> "{st.session_state.pending_query}"</span>
                    <p style="font-size: 12px; color: #94a3b8; margin: 4px 0 0 0;">Enter your email to unlock your verified solution in TopperGPT!</p>
                </div>
            """, unsafe_allow_html=True)

        _, center_col, _ = st.columns([1, 1.8, 1])
        with center_col:
            st.markdown("""
                <div style="background: rgba(88, 193, 200, 0.06); border: 1px solid rgba(88, 193, 200, 0.25); border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; text-align: center;">
                    <span style="color: #58c1c8; font-weight: 700; font-size: 13px;">✦ INSTANT ACADEMIC ACCESS</span>
                    <p style="color: #94a3b8; font-size: 12px; margin: 4px 0 0 0;">Enter your academic email below or continue as Guest Student.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 CONTINUE AS GUEST STUDENT", use_container_width=True):
                st.session_state.user_data = {"email": "student@toppergpt.in", "full_name": "Student", "is_pro": True}
                st.rerun()

            st.markdown("<div style='text-align: center; margin: 12px 0; color: #64748b; font-size: 12px;'>─── OR SIGN IN WITH EMAIL ───</div>", unsafe_allow_html=True)

            auth_tab = st.tabs(["🔑 Quick Access", "📝 New Registration"])
            
            with auth_tab[0]:
                with st.form("quick_login"):
                    l_email = st.text_input("Registered Email Address", placeholder="name@domain.com", key="l_email_quick").strip().lower()
                    if st.form_submit_button("ENTER DASHBOARD 🚀", use_container_width=True):
                        active_email = l_email if l_email else "student@toppergpt.in"
                        if supabase:
                            try:
                                prof = supabase.table("profiles").select("*").eq("email", active_email).execute()
                                if prof.data:
                                    st.session_state.user_data = prof.data[0]
                                    st.rerun()
                                else:
                                    st.session_state.user_data = {"email": active_email, "full_name": active_email.split('@')[0].capitalize(), "is_pro": True}
                                    st.rerun()
                            except Exception as e:
                                st.session_state.user_data = {"email": active_email, "full_name": active_email.split('@')[0].capitalize(), "is_pro": True}
                                st.rerun()
                        else:
                            st.session_state.user_data = {"email": active_email, "full_name": active_email.split('@')[0].capitalize(), "is_pro": True}
                            st.rerun()

            with auth_tab[1]:
                with st.form("reg_form_quick"):
                    s_name = st.text_input("Full Name", placeholder="Enter your full name", key="reg_name_quick")
                    s_email = st.text_input("Email Address", placeholder="name@domain.com", key="reg_email_quick").strip().lower()
                    if st.form_submit_button("CREATE ACCOUNT 🔥", use_container_width=True):
                        if s_name and s_email:
                            if supabase:
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
                                st.session_state.user_data = {"email": s_email, "full_name": s_name, "is_pro": True}
                                st.rerun()
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
            <div style="width:12px; height:12px; background:#58c1c8; border-radius:50%; box-shadow: 0 0 12px #58c1c8;"></div>
            <h2 style="color:#ffffff; margin:0; font-size:24px; font-weight:800; letter-spacing:-0.5px;">Topper<span style="color:#58c1c8;">GPT</span></h2>
        </div>
    """, unsafe_allow_html=True)

    nav_options = [
        "💡 AI Tutor",
        "🎯 Predicted Qs",
        "📄 Short Notes",
        "🔍 Topic Research"
    ]

    default_nav_idx = 0
    if "pending_feature" in st.session_state:
        feat = st.session_state.pop("pending_feature")
        if "predict" in feat:
            default_nav_idx = 1
        elif "note" in feat:
            default_nav_idx = 2
        elif any(k in feat for k in ["solver", "research", "analytics", "flashcard"]):
            default_nav_idx = 3

    nav_selection = st.radio(
        "Navigation",
        nav_options,
        index=default_nav_idx,
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

    with st.expander(f"👤 {(st.session_state.user_data or {}).get('full_name', 'Student')}", expanded=False):
        curr_email = (st.session_state.user_data or {}).get("email", "student@toppergpt.in")
        curr_name = (st.session_state.user_data or {}).get("full_name", "Student")
        st.caption(f"Active Account: {curr_email}")
        with st.form("edit_profile_sidebar"):
            new_name = st.text_input("Name", value=curr_name)
            new_email = st.text_input("Email", value=curr_email)
            if st.form_submit_button("Save Profile"):
                if "user_data" not in st.session_state or not st.session_state.user_data:
                    st.session_state.user_data = {}
                st.session_state.user_data["full_name"] = new_name
                st.session_state.user_data["email"] = new_email
                st.success("Profile saved!")
                st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

# --- 8. TOP HEADER & STREAK BAR ---
student_name = (st.session_state.user_data or {}).get("full_name", "Student")
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

    # Auto-process pending query from Landing Page search
    if "pending_query" in st.session_state and st.session_state.pending_query:
        init_q = st.session_state.pop("pending_query")
        st.session_state.tutor_messages.append({"role": "user", "content": init_q, "hinglish": None})
        with st.spinner("Analyzing syllabus and generating exam-focused solution..."):
            tutor_prompt = f"""
            You are TopperGPT's Senior Academic Evaluator for Mumbai University Engineering (C-Scheme).
            Respond exclusively in professional, clear, exam-oriented English.

            Student Query: "{init_q}"

            1. If conversational (greetings, general chat): Reply politely and concisely in 1-2 sentences.
            2. If academic: Use the strict 3-block structure:
               ### 📌 1. University Standard Definition (2-Mark Standard)
               Accurate textbook definition and mandatory examiner keywords.

               ### ⚡ 2. Step-by-Step Technical Execution & Derivation
               Logically organized steps, formulas with Markdown LaTeX ($...$ or $$...$$), and specific 'Exam Diagram Requirement' if applicable.

               ### ⚠️ 3. Examiner Trap Alert
               Precise calculation error, unit conversion, or assumption where students frequently lose marks.
            """
            try:
                ai_reply = generate_ai_response(tutor_prompt)
                st.session_state.tutor_messages.append({"role": "assistant", "content": ai_reply, "hinglish": None})
            except Exception as e:
                st.session_state.tutor_messages.append({"role": "assistant", "content": f"Error: {e}", "hinglish": None})
        st.rerun()

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
            <h3 style="margin-top:0; color:#58c1c8;">Target High-Probability Examination Questions</h3>
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
            <h3 style="margin-top:0; color:#58c1c8;">1-Page Exam Cheat Sheet</h3>
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
            <h3 style="margin-top:0; color:#58c1c8;">Streamlined Concept Breakdown</h3>
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
                st.markdown("<h4 style='color:#58c1c8; margin-top:0;'>1. Official Definition</h4>", unsafe_allow_html=True)
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