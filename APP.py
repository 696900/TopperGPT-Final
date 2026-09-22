import streamlit as st
import requests
import json
import time
import os
import re
from datetime import datetime
try:
    from fpdf import FPDF
    from fpdf.fonts import FontFace
except ImportError:
    FPDF = None
    FontFace = None
from supabase import create_client, Client
from landing_page import render_landing_page

# Safe Secret Helper for Render & Streamlit Environments
def get_env_secret(key, default=""):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    val = os.environ.get(key)
    if val:
        return val
    try:
        sec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".streamlit", "secrets.toml")
        if os.path.exists(sec_path):
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            with open(sec_path, "rb") as f:
                sec_dict = tomllib.load(f)
                if key in sec_dict:
                    return sec_dict[key]
    except Exception:
        pass
    return default

def is_valid_email(email_str: str) -> bool:
    """Rigorous email validator ensuring proper RFC structure with '@' and valid domain extensions (e.g., .com, .in, .edu)."""
    if not email_str or not isinstance(email_str, str):
        return False
    email_clean = email_str.strip().lower()
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, email_clean):
        return False
    if ".." in email_clean:
        return False
    parts = email_clean.split("@")
    if len(parts) != 2:
        return False
    local_part, domain_part = parts
    if not local_part or not domain_part:
        return False
    domain_sections = domain_part.split(".")
    tld = domain_sections[-1]
    if len(tld) < 2 or not tld.isalpha():
        return False
    if local_part.startswith(".") or local_part.endswith("."):
        return False
    for sec in domain_sections:
        if not sec or sec.startswith("-") or sec.endswith("-"):
            return False
    return True

# --- 1. CONFIGURATION & PAGE SETUP ---
st.set_page_config(
    page_title="TopperGPT - AI Academic Workspace",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
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

# Universal Permanent Black (Dark) Theme Lock across all devices
st.session_state.theme_choice = "dark"
active_theme = "dark"

# --- 2. CSS STYLING OVERHAUL (PERMANENT DARK THEME & STREAMLIT TOOLBAR REMOVAL) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700;800&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

/* ================================================================ */
/* 0. STREAMLIT TOOLBAR, MENU, FOOTER & BRANDING REMOVAL            */
/* ================================================================ */
#MainMenu {
    visibility: hidden !important;
    display: none !important;
}
footer {
    visibility: hidden !important;
    display: none !important;
}
[data-testid="stToolbar"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    height: 0 !important;
    width: 0 !important;
}
div[data-testid="stDecoration"] {
    display: none !important;
    visibility: hidden !important;
}
div[data-testid="stStatusWidget"] {
    display: none !important;
    visibility: hidden !important;
}
.stDeployButton {
    display: none !important;
    visibility: hidden !important;
}
/* Toolbar and header action cleanup (sidebar toggle buttons are handled per-device in media queries) */
section[data-testid="stSidebar"] button[kind="header"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
}

/* ================================================================ */
/* 1. UNIVERSAL PERMANENT BLACK (DARK) THEME PALETTE                */
/* ================================================================ */
:root,
html,
body,
.stApp {
    --text-primary: #f8fafc !important;
    --text-secondary: #cbd5e1 !important;
    --text-muted: #94a3b8 !important;
    --text-dim: #64748b !important;
    --text-placeholder: #94a3b8 !important;
    --bg-primary: #030303 !important;
    --bg-surface: #08090d !important;
    --bg-sidebar: #060709 !important;
    --bg-input: #08090d !important;
    --bg-chat-bar: rgba(8, 9, 13, 0.94) !important;
    --bg-pinned-bar: linear-gradient(180deg, rgba(3, 3, 3, 0) 0%, rgba(3, 3, 3, 0.96) 30%, #030303 100%) !important;
    --bg-hover: rgba(88, 193, 200, 0.08) !important;
    --grid-line: rgba(255, 255, 255, 0.02) !important;
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    color: var(--text-primary) !important;
    -webkit-font-smoothing: antialiased;
}

/* Custom sleek scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: var(--bg-primary);
}
::-webkit-scrollbar-thumb {
    background: rgba(88, 193, 200, 0.25);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(88, 193, 200, 0.55);
}

::selection {
    background: rgba(88, 193, 200, 0.3) !important;
    color: var(--text-primary) !important;
}

/* Background grid styling matching cyber-cyan aesthetic */
.stApp {
    background-color: var(--bg-primary) !important;
    background-image: 
        radial-gradient(circle at 50% 8%, rgba(88, 193, 200, 0.12) 0%, transparent 60%),
        linear-gradient(to right, var(--grid-line) 1px, transparent 1px),
        linear-gradient(to bottom, var(--grid-line) 1px, transparent 1px) !important;
    background-size: 100% 100%, 36px 36px, 36px 36px !important;
    color: var(--text-primary) !important;
}

/* Header customization */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Typography & Headings */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
div[data-testid="stMarkdownContainer"] h1,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3,
div[data-testid="stMarkdownContainer"] h4 {
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
}

p, span, li, label,
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] li,
div[data-testid="stMarkdownContainer"] span {
    color: var(--text-primary);
}

div[data-testid="stMarkdownContainer"] strong, strong {
    color: var(--text-primary) !important;
    font-weight: 700;
}

div[data-testid="stMarkdownContainer"] code {
    color: #58C1C8 !important;
    background: rgba(88, 193, 200, 0.08) !important;
    border: 1px solid rgba(88, 193, 200, 0.25) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 0.88em !important;
}

/* ================================================================ */
/* 1. SIDEBAR & FEATURE NAVIGATION BASE STYLING                      */
/* ================================================================ */
[data-testid="stSidebar"],
section[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding-top: 15px !important;
}

/* Sidebar Feature Navigation Radio Container */
div[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 10px !important;
    display: flex !important;
    flex-direction: column !important;
    width: 100% !important;
}

/* Convert sidebar items into full-width, clean rounded action buttons/cards */
div[data-testid="stSidebar"] div[role="radiogroup"] label {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    box-sizing: border-box !important;
    background: var(--bg-surface) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    margin: 0 0 6px 0 !important;
    cursor: pointer !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: var(--bg-hover) !important;
    border-color: rgba(88, 193, 200, 0.4) !important;
    transform: translateY(-1px) translateX(3px) !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3), 0 0 12px rgba(88, 193, 200, 0.15) !important;
}

/* Completely Hide Streamlit default radio-button circles */
div[data-testid="stSidebar"] input[type="radio"],
div[role="radiogroup"] input[type="radio"],
div[data-baseweb="radio"] input,
div[data-testid="stSidebar"] [data-baseweb="radio"] input,
div[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child,
div[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-of-type,
div[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-of-type,
div[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child,
div[data-testid="stSidebar"] div[role="radiogroup"] label input + div,
div[data-testid="stSidebar"] div[data-baseweb="radio"] > div:first-of-type,
div[data-testid="stSidebar"] div[role="radiogroup"] [data-testid="stWidgetSelectionIndicator"],
div[data-testid="stSidebar"] div[role="radiogroup"] div[aria-hidden="true"],
div[data-testid="stSidebar"] div[role="radiogroup"] svg,
div[data-testid="stSidebar"] [class*="RadioMark"],
div[data-testid="stSidebar"] [class*="radioMark"],
div[data-testid="stSidebar"] [class*="SelectionIndicator"] {
    display: none !important;
    visibility: hidden !important;
    position: absolute !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
    min-width: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    pointer-events: none !important;
}

/* Sidebar Item Text */
div[data-testid="stSidebar"] div[role="radiogroup"] label div p,
div[data-testid="stSidebar"] div[role="radiogroup"] label p,
div[data-testid="stSidebar"] div[role="radiogroup"] label span {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.2px !important;
    line-height: 1.4 !important;
    margin: 0 !important;
    padding: 0 !important;
    transition: color 0.2s ease !important;
    width: 100% !important;
}

/* Active State: Glowing Accent Outline (#58C1C8) & Glassmorphism */
div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, rgba(88, 193, 200, 0.18) 0%, rgba(8, 9, 13, 0.88) 100%) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1.5px solid #58C1C8 !important;
    border-left: 4.5px solid #58C1C8 !important;
    box-shadow: 0 0 22px rgba(88, 193, 200, 0.35), inset 0 0 14px rgba(88, 193, 200, 0.12) !important;
    transform: translateX(3px) !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] div p,
div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] p,
div[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] span,
div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) div p,
div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p,
div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) span {
    color: #58C1C8 !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    text-shadow: 0 0 12px rgba(88, 193, 200, 0.5) !important;
}

/* Status Card in Sidebar */
.status-card {
    background: var(--bg-surface);
    border: 1px solid rgba(88, 193, 200, 0.3);
    border-radius: 14px;
    padding: 16px 14px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    margin-top: 20px;
    color: var(--text-primary);
}
.status-card h4 {
    color: var(--text-primary) !important;
}
.status-card p {
    color: var(--text-muted) !important;
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
    box-shadow: 0 0 12px rgba(88, 193, 200, 0.2);
    white-space: nowrap;
}

/* Prompt Starter Quick Pills */
.starter-chip-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    width: 100%;
    margin-bottom: 12px;
}

.starter-chip {
    display: inline-block;
    background: var(--bg-surface);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 9999px;
    margin-right: 8px;
    margin-bottom: 12px;
    transition: all 0.2s ease;
    cursor: pointer;
}
.starter-chip:hover {
    border-color: #58c1c8;
    color: #58c1c8;
    box-shadow: 0 0 12px rgba(88, 193, 200, 0.25);
}

/* Cards & Topic Research UI Cards */
.topper-card {
    background: var(--bg-surface);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    color: var(--text-primary);
}
.topper-card p {
    color: var(--text-muted) !important;
}

.research-card-tag {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 3px 8px;
    border-radius: 6px;
    display: inline-block;
}
.research-tag-def {
    background: rgba(88, 193, 200, 0.12);
    color: #58c1c8;
    border: 1px solid rgba(88, 193, 200, 0.3);
}
.research-tag-tech {
    background: rgba(0, 242, 254, 0.12);
    color: #00f2fe;
    border: 1px solid rgba(0, 242, 254, 0.3);
}
.research-tag-work {
    background: rgba(34, 197, 94, 0.12);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.3);
}

/* Chat Bubble Customization */
[data-testid="stChatMessage"] {
    background-color: var(--bg-surface) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    margin-bottom: 14px !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
    color: var(--text-primary) !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stChatMessage"]:hover {
    border-color: rgba(88, 193, 200, 0.2) !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: var(--text-primary) !important;
}

/* Standard Text Inputs and Text Areas */
.stTextInput > div,
div[data-baseweb="input"],
div[data-baseweb="base-input"] {
    background-color: #0c0d12 !important;
    border: 1px solid rgba(88, 193, 200, 0.2) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    outline: none !important;
}

div[data-baseweb="input"]:focus-within,
div[data-baseweb="base-input"]:focus-within {
    background-color: #13151f !important;
    border-color: rgba(88, 193, 200, 0.6) !important;
    box-shadow: 0 0 14px rgba(88, 193, 200, 0.25) !important;
    outline: none !important;
}

.stTextInput input,
.stTextInput > div > div > input,
div[data-baseweb="input"] input {
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    color: var(--text-primary) !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
}

.stTextInput input:focus,
.stTextInput > div > div > input:focus,
div[data-baseweb="input"] input:focus {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
}

.stTextInput input::placeholder,
input::placeholder,
textarea::placeholder,
div[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-placeholder) !important;
    -webkit-text-fill-color: var(--text-placeholder) !important;
    opacity: 1 !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
}

/* ================================================================ */
/* 2. CHAT INPUT BAR (NO WHITE BORDER / OUTLINE, DARK BACKDROP)     */
/* ================================================================ */
div[data-testid="stBottom"], .stBottom {
    background: transparent !important;
    background-color: transparent !important;
    border-top: none !important;
    border: none !important;
    box-shadow: none !important;
    z-index: 999 !important;
}

div[data-testid="stBottomBlockContainer"] {
    background: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    padding-bottom: 22px !important;
    padding-top: 8px !important;
}

div[data-testid="stChatInput"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    margin: 8px 0 12px 0 !important;
}

div[data-testid="stChatInput"] > div,
div[data-testid="stChatInput"] .stChatFloatingInputContainer {
    background: #13151f !important;
    background-color: #13151f !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.7) !important;
    outline: none !important;
    padding: 6px 12px !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stChatInput"] > div:focus-within,
div[data-testid="stChatInput"] .stChatFloatingInputContainer:focus-within {
    background: #13151f !important;
    background-color: #13151f !important;
    border-color: rgba(88, 193, 200, 0.5) !important;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.85), 0 0 10px rgba(88, 193, 200, 0.15) !important;
    outline: none !important;
    transform: translateY(-1px);
}

/* Strip all BaseWeb inner borders, outlines, and box-shadows */
div[data-testid="stChatInput"] div[data-baseweb="textarea"],
div[data-testid="stChatInput"] div[data-baseweb="base-input"],
div[data-testid="stChatInput"] div[data-baseweb="textarea"] > div,
div[data-testid="stChatInput"] div[data-baseweb="base-input"] > div,
div[data-testid="stChatInput"] [class*="StyledRoot"],
div[data-testid="stChatInput"] [class*="StyledInputContainer"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    -webkit-box-shadow: none !important;
}

div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] textarea:focus,
div[data-testid="stChatInput"] textarea:focus-visible,
div[data-testid="stChatInput"] textarea:active {
    background-color: transparent !important;
    background: transparent !important;
    color: var(--text-primary, #f8fafc) !important;
    font-family: inherit !important;
    font-size: 15px !important;
    line-height: 1.5 !important;
    border: none !important;
    box-shadow: none !important;
    -webkit-box-shadow: none !important;
    outline: none !important;
    padding: 8px 10px !important;
}

/* Send Button with Cyber-Cyan Accent */
div[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, rgb(88, 193, 200) 0%, rgb(40, 155, 165) 100%) !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 12px !important;
    width: 38px !important;
    height: 38px !important;
    min-width: 38px !important;
    min-height: 38px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: auto 2px !important;
    padding: 0 !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 0 14px rgba(88, 193, 200, 0.35) !important;
}

div[data-testid="stChatInput"] button:hover:not(:disabled) {
    transform: scale(1.06) translateY(-1px) !important;
    box-shadow: 0 0 22px rgba(88, 193, 200, 0.6) !important;
}

div[data-testid="stChatInput"] button:active:not(:disabled) {
    transform: scale(0.96) !important;
}

div[data-testid="stChatInput"] button:disabled {
    background: rgba(255, 255, 255, 0.06) !important;
    color: var(--text-dim) !important;
    opacity: 0.45 !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
}

div[data-testid="stChatInput"] button svg {
    fill: currentColor !important;
    width: 18px !important;
    height: 18px !important;
}

/* Cyber-Cyan Accent Buttons */
.stButton > button, div[data-testid="stFormSubmitButton"] > button, .stDownloadButton > button {
    background: linear-gradient(135deg, rgb(88, 193, 200) 0%, rgb(40, 155, 165) 100%) !important;
    color: #000000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 18px rgba(88, 193, 200, 0.45) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--bg-surface);
    border-radius: 10px;
    padding: 4px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted);
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    color: #58c1c8 !important;
    border-bottom-color: #58c1c8 !important;
}

/* Sleek Hamburger Drawer Button */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    color: #58c1c8 !important;
    background: #13151f !important;
    border: 1.5px solid rgba(88, 193, 200, 0.4) !important;
    border-radius: 10px !important;
    padding: 7px 9px !important;
    top: 12px !important;
    left: 12px !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4), 0 0 12px rgba(88, 193, 200, 0.25) !important;
    z-index: 999999 !important;
    transition: all 0.2s ease !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    border-color: #58C1C8 !important;
    box-shadow: 0 4px 22px rgba(0, 0, 0, 0.5), 0 0 18px rgba(88, 193, 200, 0.5) !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg {
    stroke: #58C1C8 !important;
    fill: #58C1C8 !important;
}

/* Table and Component Contrast Enhancements */
table, thead, tbody, tr, th, td {
    color: var(--text-primary) !important;
}
th {
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
}
[data-testid="stExpander"] {
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
}
[data-testid="stExpander"] summary span {
    color: var(--text-primary) !important;
}
[data-testid="stExpander"] svg {
    fill: var(--text-primary) !important;
}
div[data-baseweb="select"] > div,
div[data-baseweb="popover"],
div[data-baseweb="menu"],
ul[data-testid="stSelectboxVirtualDropdown"] {
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
}
div[data-baseweb="select"] span,
div[data-baseweb="menu"] li {
    color: var(--text-primary) !important;
}

/* ================================================================ */
/* 3. DESKTOP / LAPTOPS (@media min-width: 1025px)                  */
/* ================================================================ */
@media (min-width: 1025px) {
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"][aria-expanded="false"],
    section[data-testid="stSidebar"][aria-expanded="false"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        bottom: 0 !important;
        height: 100vh !important;
        min-width: 290px !important;
        width: 290px !important;
        max-width: 320px !important;
        transform: none !important;
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        margin-left: 0 !important;
        z-index: 100 !important;
    }

    /* Hide collapse controls on desktop */
    [data-testid="stSidebarCollapseButton"],
    button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    button[aria-label="Close sidebar"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
    }

    section.main,
    .stMain {
        margin-left: 290px !important;
        width: calc(100% - 290px) !important;
    }

    .main .block-container,
    div[data-testid="stMainBlockContainer"] {
        width: 85% !important;
        max-width: 1000px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 2rem !important;
        padding-bottom: 120px !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    div[data-testid="stBottomBlockContainer"] {
        width: 85% !important;
        max-width: 1000px !important;
        margin: 0 auto !important;
        padding-bottom: 22px !important;
        padding-top: 8px !important;
    }

    .page-main-title {
        font-size: 32px !important;
    }
}

/* ================================================================ */
/* 4. TABLETS (@media min-width: 769px and max-width: 1024px)       */
/* ================================================================ */
@media (min-width: 769px) and (max-width: 1024px) {
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"][aria-expanded="false"],
    section[data-testid="stSidebar"][aria-expanded="false"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        bottom: 0 !important;
        height: 100vh !important;
        min-width: 250px !important;
        width: 250px !important;
        max-width: 260px !important;
        transform: none !important;
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        margin-left: 0 !important;
        z-index: 100 !important;
    }

    /* Hide collapse controls on tablet */
    [data-testid="stSidebarCollapseButton"],
    button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    button[aria-label="Close sidebar"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
    }

    section.main,
    .stMain {
        margin-left: 250px !important;
        width: calc(100% - 250px) !important;
    }

    .main .block-container,
    div[data-testid="stMainBlockContainer"] {
        width: 94% !important;
        max-width: 100% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 2rem !important;
        padding-bottom: 125px !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    div[data-testid="stBottomBlockContainer"] {
        width: 94% !important;
        max-width: 100% !important;
        margin: 0 auto !important;
        padding-bottom: 18px !important;
        padding-top: 6px !important;
    }

    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 10px 12px !important;
    }

    div[data-testid="stSidebar"] div[role="radiogroup"] label div p,
    div[data-testid="stSidebar"] div[role="radiogroup"] label p,
    div[data-testid="stSidebar"] div[role="radiogroup"] label span {
        font-size: 0.98rem !important;
    }

    .page-main-title {
        font-size: 28px !important;
    }
}

/* ================================================================ */
/* 5. MOBILE PHONES & SMALL SCREENS (@media max-width: 768px)       */
/* ================================================================ */
@media (max-width: 768px) {
    /* Critical layout overflow fix: Prevent horizontal body scrolling */
    html, body, .stApp {
        overflow-x: hidden !important;
        width: 100vw !important;
        max-width: 100vw !important;
    }

    section.main,
    .stMain {
        margin-left: 0 !important;
        width: 100% !important;
        max-width: 100vw !important;
        padding-top: 6px !important;
        overflow-x: hidden !important;
    }

    .main .block-container,
    div[data-testid="stMainBlockContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        padding-top: 4.2rem !important; /* Adequate clearance so top title never collides with floating hamburger */
        padding-left: 14px !important;
        padding-right: 14px !important;
        padding-bottom: 140px !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }

    /* Mobile Sidebar Drawer Styling */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"] {
        background-color: #0c0d12 !important;
        border-right: 1px solid rgba(88, 193, 200, 0.25) !important;
        box-shadow: 4px 0 30px rgba(0, 0, 0, 0.85) !important;
        z-index: 99999 !important;
        width: 82vw !important;
        max-width: 320px !important;
    }

    /* Mobile Native Hamburger Menu Accessibility */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        position: fixed !important;
        top: 12px !important;
        left: 12px !important;
        z-index: 999999 !important;
        background: #13151f !important;
        border: 1.5px solid rgba(88, 193, 200, 0.6) !important;
        border-radius: 10px !important;
        width: 44px !important;
        height: 44px !important;
        min-width: 44px !important;
        min-height: 44px !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.8), 0 0 12px rgba(88, 193, 200, 0.3) !important;
        cursor: pointer !important;
        padding: 0 !important;
    }

    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button,
    [data-testid="stSidebarCollapsedControl"] button[data-testid="baseButton-headerNoPadding"],
    [data-testid="collapsedControl"] button[data-testid="baseButton-headerNoPadding"],
    [data-testid="stSidebarCollapsedControl"] button[aria-label="Open sidebar"],
    [data-testid="collapsedControl"] button[aria-label="Open sidebar"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        width: 100% !important;
        height: 100% !important;
        background: transparent !important;
        border: none !important;
        outline: none !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        color: #58c1c8 !important;
    }

    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg {
        display: block !important;
        width: 22px !important;
        height: 22px !important;
        fill: #58c1c8 !important;
        stroke: #58c1c8 !important;
    }

    [data-testid="stSidebarCollapseButton"],
    button[data-testid="stSidebarCollapseButton"],
    button[aria-label="Close sidebar"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        color: #58c1c8 !important;
    }

    /* Header & Streak Badge Layout on Mobile */
    div[data-testid="stHorizontalBlock"]:has(.streak-badge) {
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 2px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.streak-badge) > div {
        width: 100% !important;
        min-width: 100% !important;
    }

    .page-main-title {
        font-size: 24px !important;
        line-height: 1.25 !important;
        margin: 0 0 6px 0 !important;
        word-break: break-word !important;
    }

    .streak-badge {
        float: none !important;
        margin: 2px 0 12px 0 !important;
        font-size: 11.5px !important;
        padding: 4px 10px !important;
        display: inline-flex !important;
    }

    /* Starter Quick Chips */
    .starter-chip-container {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
        width: 100% !important;
        margin-bottom: 12px !important;
    }
    .starter-chip {
        font-size: 11px !important;
        padding: 6px 12px !important;
        margin-right: 0 !important;
        margin-bottom: 0 !important;
        flex-shrink: 0 !important;
    }

    /* Cards on Mobile */
    .topper-card {
        padding: 16px 14px !important;
        margin-bottom: 14px !important;
        border-radius: 14px !important;
        box-sizing: border-box !important;
        word-break: break-word !important;
        width: 100% !important;
    }
    .topper-card h3 {
        font-size: 17px !important;
        line-height: 1.35 !important;
        margin-top: 0 !important;
        margin-bottom: 6px !important;
    }
    .topper-card p {
        font-size: 13px !important;
        line-height: 1.5 !important;
    }

    /* Stack Multi-column Cards on Mobile */
    div[data-testid="stHorizontalBlock"]:has(.research-card-tag) {
        display: flex !important;
        flex-direction: column !important;
        gap: 10px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.research-card-tag) > div {
        width: 100% !important;
        min-width: 100% !important;
    }

    /* Prevent Button Clipping on Mobile */
    .stButton > button,
    div[data-testid="stFormSubmitButton"] > button,
    .stDownloadButton > button {
        font-size: 13px !important;
        padding: 10px 14px !important;
        width: 100% !important;
        min-height: 40px !important;
    }

    /* Inputs: 16px font-size prevents iOS Safari auto-zoom */
    .stTextInput {
        margin-bottom: 12px !important;
    }
    .stTextInput > div > div > input {
        font-size: 16px !important;
        padding: 10px 14px !important;
        border-radius: 10px !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }

    /* Chat message bubble scaling on mobile */
    div[data-testid="stChatMessage"] {
        padding: 12px 14px !important;
        margin-bottom: 10px !important;
        border-radius: 12px !important;
        max-width: 100% !important;
        word-break: break-word !important;
        box-sizing: border-box !important;
    }

    /* Mathematical Equations and Code Overflow on Mobile */
    .katex-display {
        overflow-x: auto !important;
        overflow-y: hidden !important;
        padding: 6px 0 !important;
        max-width: 100% !important;
        -webkit-overflow-scrolling: touch !important;
    }
    pre, code {
        max-width: 100% !important;
        white-space: pre-wrap !important;
        word-break: break-all !important;
    }

    /* Pinned Bottom Chat Bar Container for Mobile with Safe Area Inset */
    div[data-testid="stBottom"], .stBottom {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        max-width: 100vw !important;
        background: #0c0d12 !important;
        border-top: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-left: none !important;
        border-right: none !important;
        border-bottom: none !important;
        padding: 6px 10px max(14px, env(safe-area-inset-bottom, 14px)) 10px !important;
        z-index: 9999 !important;
        box-sizing: border-box !important;
    }

    div[data-testid="stBottomBlockContainer"] {
        padding: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stChatInput"] {
        width: 100% !important;
        margin: 2px 0 !important;
        background: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stChatInput"] > div,
    div[data-testid="stChatInput"] .stChatFloatingInputContainer {
        background: #13151f !important;
        background-color: #13151f !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 14px !important;
        padding: 4px 8px !important;
        outline: none !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6) !important;
    }

    div[data-testid="stChatInput"] > div:focus-within,
    div[data-testid="stChatInput"] .stChatFloatingInputContainer:focus-within {
        border-color: rgba(88, 193, 200, 0.5) !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.8), 0 0 8px rgba(88, 193, 200, 0.15) !important;
        outline: none !important;
    }

    /* Strip all BaseWeb inner borders, outlines, and box-shadows */
    div[data-testid="stChatInput"] div[data-baseweb="textarea"],
    div[data-testid="stChatInput"] div[data-baseweb="base-input"],
    div[data-testid="stChatInput"] div[data-baseweb="textarea"] > div,
    div[data-testid="stChatInput"] div[data-baseweb="base-input"] > div,
    div[data-testid="stChatInput"] [class*="StyledRoot"],
    div[data-testid="stChatInput"] [class*="StyledInputContainer"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        -webkit-box-shadow: none !important;
    }

    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInput"] textarea:focus,
    div[data-testid="stChatInput"] textarea:focus-visible,
    div[data-testid="stChatInput"] textarea:active {
        font-size: 16px !important;
        padding: 6px 8px !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        -webkit-box-shadow: none !important;
        color: #f8fafc !important;
        background: transparent !important;
    }

    div[data-testid="stChatInput"] button {
        width: 36px !important;
        height: 36px !important;
        min-width: 36px !important;
        min-height: 36px !important;
        border-radius: 10px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Default: If not logged in and not requesting login page, render landing page
if st.session_state.get("user_data") is None and qp_page != "login":
    render_landing_page(initial_theme=active_theme)
    st.stop()

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

@st.cache_data(ttl=86400, show_spinner=False)
def get_cached_profile(email_addr: str):
    """Bypasses database lookup delays for returning students by caching user profile data in memory."""
    if not supabase or not email_addr:
        return None
    try:
        prof = supabase.table("profiles").select("*").eq("email", email_addr.strip().lower()).execute()
        if prof.data:
            return prof.data[0]
    except Exception:
        pass
    return None

# --- 4. LATEX & MATHEMATICAL FORMULA SANITIZER ---
def clean_latex_math(text: str) -> str:
    """
    Standardizes and sanitizes LaTeX math equations for clean Streamlit KaTeX rendering.
    - Replaces double-escaped backslashes (\\\\frac -> \\frac)
    - Removes raw \\displaystyle and converts {\\displaystyle ...} to $$...$$
    - Converts \\[ ... \\] to $$ ... $$
    - Converts \\( ... \\) to $ ... $
    - Wraps raw unrendered expressions (like (R_{eq}), R_{eq}) in $...$
    - Wraps raw un-delimited LaTeX formulas (like \\frac{a}{b}) in $...$
    - Ensures proper dollar-sign boundaries for KaTeX parsing in Streamlit markdown
    """
    if not text or not isinstance(text, str):
        return text

    # 1. Normalize double-escaped backslashes before LaTeX commands:
    # e.g. \\frac -> \frac, \\sum -> \sum, \\sqrt -> \sqrt, etc.
    text = re.sub(r'\\\\([a-zA-Z]+)', r'\\\1', text)

    # 2. Convert {\displaystyle ...} blocks using balanced brace matching
    def replace_displaystyle_blocks(s):
        result = []
        i = 0
        n = len(s)
        while i < n:
            match = re.search(r'\{\s*\\displaystyle\b', s[i:])
            if not match:
                result.append(s[i:])
                break
            
            start_pos = i + match.start()
            result.append(s[i:start_pos])
            
            open_brace_idx = start_pos + s[start_pos:start_pos + match.end()].find('{')
            brace_count = 1
            j = open_brace_idx + 1
            while j < n:
                if s[j] == '{':
                    brace_count += 1
                elif s[j] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        break
                j += 1
            
            if j < n and brace_count == 0:
                inner_content = s[open_brace_idx + 1:j].strip()
                inner_content = re.sub(r'\\displaystyle\s*', '', inner_content).strip()
                result.append(f"\n$$\n{inner_content}\n$$\n")
                i = j + 1
            else:
                result.append(s[start_pos:])
                break
        return "".join(result)

    text = replace_displaystyle_blocks(text)

    # 3. Convert LaTeX display brackets \[ ... \] to $$ ... $$
    text = re.sub(r'\\\[\s*(.*?)\s*\\\]', r'\n$$\n\1\n$$\n', text, flags=re.DOTALL)

    # 4. Convert LaTeX inline parens \( ... \) to $ ... $
    text = re.sub(r'\\\(\s*(.*?)\s*\\\)', r' $\1$ ', text, flags=re.DOTALL)

    # 5. Clean any remaining raw \displaystyle inside existing equations
    text = re.sub(r'\\displaystyle\s*', '', text)

    # 6. Process text outside of math blocks ($...$ and $$...$$)
    math_pattern = r'(\$\$.*?\$\$|\$.*?\$)'
    parts = re.split(math_pattern, text, flags=re.DOTALL)
    cleaned_parts = []
    for part in parts:
        if part.startswith('$'):
            # Math block (either $$...$$ or $...$)
            # Ensure no nested dollar signs inside $$...$$
            if part.startswith('$$') and part.endswith('$$') and len(part) >= 4:
                inner = part[2:-2]
                inner = re.sub(r'(?<!\\)\$', '', inner)  # remove any rogue $ inside $$
                cleaned_parts.append(f"$${inner}$$")
            else:
                cleaned_parts.append(part)
        else:
            # Non-math text:
            p = part
            # Check for unwrapped \frac or \sqrt equations in non-math text
            frac_pattern = r'((?:[a-zA-Z0-9_]+\s*=\s*)?\\frac\{[^{}]+\}\{[^{}]+\}(?:\s*[\=\+\-\*\/]\s*(?:\\frac\{[^{}]+\}\{[^{}]+\}|[a-zA-Z0-9_{}\^]+))*)'
            p = re.sub(frac_pattern, r'$\1$', p)

            # Convert (R_{eq}) to ($R_{eq}$)
            p = re.sub(r'\(([A-Za-z]+_\{[A-Za-z0-9+-]+\})\)', r'($\1$)', p)
            # Convert standalone variable with subscript like R_{eq}, V_{p}, N_{s}
            p = re.sub(r'(?<![\$\\a-zA-Z0-9])([A-Za-z]{1,4}_\{[A-Za-z0-9+-]+\})(?![\$\\a-zA-Z0-9])', r'$\1$', p)
            cleaned_parts.append(p)
    text = "".join(cleaned_parts)

    # 7. Clean up extra blank lines around $$
    text = re.sub(r'\n{3,}\$\$', '\n\n$$', text)
    text = re.sub(r'\$\$\n{3,}', '$$\n\n', text)

    return text

# --- 5. BACKEND OUTPUT & REGEX STRING CLEANER ---
def clean_output_text(text: str) -> str:
    """
    Sanitizes raw backend and LLM output strings before rendering:
    - Strips citation tags like [cite: 23], [cite: 24, 27], [cite], etc.
    - Strips raw section headers like --- ASALI MU PAPERS DATA ... ---
    - Applies LaTeX math standardization via clean_latex_math()
    - Cleans up excessive newlines and whitespace
    """
    if not text or not isinstance(text, str):
        return "" if text is None else text

    # 1. Strip raw section headers like "--- ASALI MU PAPERS DATA (NEP 2020) ---" or "--- ASALI ... ---"
    text = re.sub(r'(?i)^\s*[-=*]{2,}\s*ASALI\b[^\n]*[-=*]{2,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'(?i)^\s*[-=*]{2,}\s*ASALI\b[^\n]*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'(?i)[-=*]{2,}\s*ASALI\s+MU\s+PAPERS[^\n]*?[-=*]{2,}', '', text)
    text = re.sub(r'(?i)[-=*]{2,}\s*ASALI\b[^\n]*?[-=*]{2,}', '', text)

    # 2. Strip citation tags like [cite: 23], [cite: 24, 27], [cite: ...], [cite], 【cite: ...】
    text = re.sub(r'\[\s*cite:?[^\]]*\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'【[^】]*】', '', text)
    text = re.sub(r'<\s*cite[^>]*>.*?<\s*/\s*cite\s*>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # 3. Clean and standardize LaTeX math
    text = clean_latex_math(text)

    # 4. Strip conversational introductory fluff at the very beginning (e.g. "Sure, here are...", "Here is...", "Certainly!...")
    text = re.sub(r'^(?:(?:Certainly|Sure|Here(?:\s+is|\s+are)?|Of course|Alright|Below(?:\s+is|\s+are)?)[^\n]*?\n+)+(?=###|\*\*|#)', '', text, flags=re.IGNORECASE)

    # 5. Normalize multiple blank lines and whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()



def parse_topic_research_json(raw_text: str) -> dict:
    """
    Safely parses backend response for Topic Research into a structured dict with:
    - 'definition'
    - 'breakdown'
    - 'working_principle'
    Guarantees no raw JSON strings, markdown code fences, or unparsed JSON scaffolds leak into the UI.
    """
    if not raw_text or not isinstance(raw_text, str):
        return {
            "definition": "Official definition unavailable.",
            "breakdown": "Technical breakdown unavailable.",
            "working_principle": "Working principle unavailable."
        }

    cleaned_text = clean_output_text(raw_text)

    def validate_and_clean(d: dict) -> dict:
        def_val = clean_output_text(str(d.get("definition", "") or "").strip())
        bkd_val = clean_output_text(str(d.get("breakdown", "") or "").strip())
        wp_val = clean_output_text(str(d.get("working_principle", "") or "").strip())

        if not def_val:
            def_val = "Key textbook definition and core university terminology."
        if not bkd_val:
            bkd_val = "Technical specifications, governing equations, and architectural breakdown."
        if not wp_val:
            wp_val = "Operational working principle and physical mechanics flow."

        return {
            "definition": def_val,
            "breakdown": bkd_val,
            "working_principle": wp_val
        }

    # Attempt 1: Direct JSON parsing (stripping code fences)
    s = cleaned_text.strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    s = s.strip()

    try:
        data = json.loads(s)
        if isinstance(data, dict):
            return validate_and_clean(data)
    except Exception:
        pass

    # Attempt 2: Extract JSON object substring
    m = re.search(r'(\{[\s\S]*\})', cleaned_text)
    if m:
        candidate = m.group(1)
        fixed_candidate = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', candidate)
        fixed_candidate = re.sub(r',\s*([}\]])', r'\1', fixed_candidate)
        try:
            data = json.loads(fixed_candidate, strict=False)
            if isinstance(data, dict):
                return validate_and_clean(data)
        except Exception:
            pass

    # Attempt 3: Regex key extraction for "definition", "breakdown", "working_principle"
    def extract_field(key_name: str, src: str) -> str:
        p1 = rf'"{key_name}"\s*:\s*"((?:\\.|[^"\\])*)"'
        match1 = re.search(p1, src, re.DOTALL)
        if match1:
            val = match1.group(1).replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
            return val.strip()
        p2 = rf'"{key_name}"\s*:\s*"(.*?)(?=",\s*"\w+"|\s*"\s*}}|\s*}}\s*\Z|\Z)'
        match2 = re.search(p2, src, re.DOTALL)
        if match2:
            return match2.group(1).replace('\\"', '"').replace('\\n', '\n').strip()
        return ""

    def_field = extract_field("definition", cleaned_text)
    bkd_field = extract_field("breakdown", cleaned_text)
    wp_field = extract_field("working_principle", cleaned_text)

    if def_field or bkd_field or wp_field:
        return validate_and_clean({
            "definition": def_field,
            "breakdown": bkd_field,
            "working_principle": wp_field
        })

    # Attempt 4: If backend returned markdown sections
    def_match = re.search(r'(?:###?\s*(?:1[.\s]*)?(?:Official\s+)?Definition[^\n]*\n)([\s\S]*?)(?=###?\s*(?:2[.\s]*)?Technical|###?\s*(?:3[.\s]*)?Working|\Z)', cleaned_text, re.IGNORECASE)
    bkd_match = re.search(r'(?:###?\s*(?:2[.\s]*)?Technical\s+Breakdown[^\n]*\n)([\s\S]*?)(?=###?\s*(?:3[.\s]*)?Working|\Z)', cleaned_text, re.IGNORECASE)
    wp_match = re.search(r'(?:###?\s*(?:3[.\s]*)?Working\s+Principle[^\n]*\n)([\s\S]*?)$', cleaned_text, re.IGNORECASE)

    if def_match or bkd_match or wp_match:
        return validate_and_clean({
            "definition": def_match.group(1).strip() if def_match else "",
            "breakdown": bkd_match.group(1).strip() if bkd_match else "",
            "working_principle": wp_match.group(1).strip() if wp_match else ""
        })

    # Fallback: Strip raw JSON delimiters so plain text displays without JSON noise
    clean_raw = re.sub(r'[{}"`]|(?i)definition:|breakdown:|working_principle:', '', cleaned_text).strip()
    return validate_and_clean({
        "definition": "Syllabus Concept Overview",
        "breakdown": clean_raw,
        "working_principle": "Operational details and examination steps."
    })

# --- 6. ACADEMIC PDF EXPORT ENGINE (FPDF2) ---
def replace_frac(text: str) -> str:
    """Replaces \\frac{A}{B} with (A / B) handling nested curly braces."""
    max_loops = 10
    while r"\frac" in text and max_loops > 0:
        max_loops -= 1
        idx = text.find(r"\frac")
        if idx == -1:
            break
        open1 = text.find("{", idx)
        if open1 == -1:
            break
        depth = 1
        pos1 = open1 + 1
        n = len(text)
        while pos1 < n and depth > 0:
            if text[pos1] == "{":
                depth += 1
            elif text[pos1] == "}":
                depth -= 1
            pos1 += 1
        if depth != 0:
            break
        num = text[open1 + 1 : pos1 - 1]

        open2 = text.find("{", pos1 - 1)
        if open2 == -1:
            break
        depth = 1
        pos2 = open2 + 1
        while pos2 < n and depth > 0:
            if text[pos2] == "{":
                depth += 1
            elif text[pos2] == "}":
                depth -= 1
            pos2 += 1
        if depth != 0:
            break
        den = text[open2 + 1 : pos2 - 1]

        text = text[:idx] + f"({num} / {den})" + text[pos2:]
    return text


def format_math_for_pdf(text: str) -> str:
    """
    Cleans LaTeX math formulas, delimiters, and notation for clean text/unicode rendering in PDF.
    - Removes LaTeX delimiters ($$, $)
    - Replaces \\frac{A}{B} -> (A / B)
    - Replaces \\sum -> Σ, \\cdot -> *, \\dots -> ..., \\text{...} -> ...
    - Preserves subscripts like _k and simplifies _{...} -> _...
    - Cleans double backslashes
    """
    if not text or not isinstance(text, str):
        return "" if text is None else text

    # 1. Clean double backslashes before LaTeX commands and line breaks
    text = re.sub(r'\\\\([a-zA-Z]+)', r'\\\1', text)
    text = re.sub(r'\\\\\s*', '\n', text)

    # 2. Convert \frac{A}{B} to (A / B) handling nested braces
    text = replace_frac(text)

    # 3. Replace common LaTeX math commands with standard Unicode/text math
    replacements = [
        (r'\\sum(?![a-zA-Z])', 'Σ'),
        (r'\\prod(?![a-zA-Z])', 'Π'),
        (r'\\cdot(?![a-zA-Z])', '*'),
        (r'\\times(?![a-zA-Z])', '×'),
        (r'\\div(?![a-zA-Z])', '÷'),
        (r'\\(dots|ldots|cdots|ddots)(?![a-zA-Z])', '...'),
        (r'\\sqrt\{([^{}]+)\}', r'sqrt(\1)'),
        (r'\\text\{([^{}]+)\}', r'\1'),
        (r'\\mathrm\{([^{}]+)\}', r'\1'),
        (r'\\mathbf\{([^{}]+)\}', r'\1'),
        (r'\\mathit\{([^{}]+)\}', r'\1'),
        (r'\\pm(?![a-zA-Z])', '±'),
        (r'\\neq(?![a-zA-Z])', '≠'),
        (r'\\leq(?![a-zA-Z])', '≤'),
        (r'\\geq(?![a-zA-Z])', '≥'),
        (r'\\approx(?![a-zA-Z])', '≈'),
        (r'\\infty(?![a-zA-Z])', '∞'),
        (r'\\alpha(?![a-zA-Z])', 'α'),
        (r'\\beta(?![a-zA-Z])', 'β'),
        (r'\\gamma(?![a-zA-Z])', 'γ'),
        (r'\\delta(?![a-zA-Z])', 'δ'),
        (r'\\theta(?![a-zA-Z])', 'θ'),
        (r'\\lambda(?![a-zA-Z])', 'λ'),
        (r'\\mu(?![a-zA-Z])', 'μ'),
        (r'\\pi(?![a-zA-Z])', 'π'),
        (r'\\sigma(?![a-zA-Z])', 'σ'),
        (r'\\omega(?![a-zA-Z])', 'ω'),
        (r'\\Omega(?![a-zA-Z])', 'Ω'),
        (r'\\Delta(?![a-zA-Z])', 'Δ'),
        (r'\\rightarrow(?![a-zA-Z])', '->'),
        (r'\\leftarrow(?![a-zA-Z])', '<-'),
        (r'\\Rightarrow(?![a-zA-Z])', '=>'),
        (r'\\Leftarrow(?![a-zA-Z])', '<='),
        (r'\\leftrightarrow(?![a-zA-Z])', '<->'),
        (r'\\int(?![a-zA-Z])', '∫'),
        (r'\\partial(?![a-zA-Z])', '∂'),
        (r'\\nabla(?![a-zA-Z])', '∇'),
        (r'\\displaystyle(?![a-zA-Z])', ''),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)

    # 4. Subscripts & superscripts: preserve _k, simplify _{eq} -> _eq
    text = re.sub(r'_\{([^{}]+)\}', r'_\1', text)
    text = re.sub(r'\^\{([^{}]+)\}', r'^\1', text)

    # 5. Clean trailing backslashes before $$ or end-of-line
    text = re.sub(r'\\+\s*(?=\$\$|\$)', '', text)
    text = re.sub(r'\\+\s*$', '', text, flags=re.MULTILINE)

    # 6. Remove LaTeX delimiters: $$ and $
    text = text.replace("$$", "").replace("$", "")

    # 7. Clean any remaining lone backslash commands
    text = re.sub(r'\\([a-zA-Z]+)\{([^{}]+)\}', r'\2', text)
    text = re.sub(r'\\([a-zA-Z]+)', r'\1', text)

    return text


def sanitize_pdf_text(text: str, is_unicode: bool = True) -> str:
    """
    Sanitizes markdown and unicode characters for safe PDF rendering.
    Maps common academic emojis and punctuation to clean readable text.
    If is_unicode is False (Helvetica fallback), maps Greek/math characters to Latin-1 safe strings.
    """
    if not text:
        return ""
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2014": "--", "\u2013": "-",
        "\u2022": "*", "\u2026": "...",
        "\u00b0": " deg",
        "💡": "[Tip] ", "🎯": "[Target] ", "⚡": "[Fast] ",
        "📘": "[Exam] ", "📑": "[Notes] ", "🧮": "[Formula] ",
        "⚠️": "[Alert] ", "📌": "[Key] ", "🔥": "[Streak] ",
        "🔍": "[Search] ", "✦": "* ", "✓": "[OK] ", "❌": "[X] ",
        "📥": "", "🚪": "", "👤": "", "🚀": "", "🔑": "", "📝": ""
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    if not is_unicode:
        math_fallbacks = {
            "Σ": "Sigma ", "Π": "Pi ", "α": "alpha", "β": "beta",
            "γ": "gamma", "δ": "delta", "θ": "theta", "λ": "lambda",
            "μ": "mu", "π": "pi", "σ": "sigma", "ω": "omega",
            "Ω": "Ohm", "Δ": "Delta", "∞": "inf", "≠": "!=",
            "≤": "<=", "≥": ">=", "≈": "~=", "±": "+/-",
            "×": "*", "÷": "/", "∫": "int", "∂": "d"
        }
        for k, v in math_fallbacks.items():
            text = text.replace(k, v)

        safe_chars = []
        for ch in text:
            try:
                ch.encode("latin-1")
                safe_chars.append(ch)
            except UnicodeEncodeError:
                safe_chars.append(" ")
        return "".join(safe_chars)

    return text


TABLE_REGEX = re.compile(
    r'(?:^[ \t]*\|?[^\n|]+\|.*?\n)'
    r'(?:^[ \t]*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)+\|?[ \t]*(?:\n|\Z))'
    r'(?:^[ \t]*\|?[^\n|]+\|.*?(?:\n|\Z))*',
    re.MULTILINE
)


def clean_split_pipe_line(line: str) -> list:
    """Splits a line by pipe |, ignoring leading/trailing whitespace and empty outer split segments."""
    raw = line.strip()
    if raw.startswith("|"):
        raw = raw[1:]
    if raw.endswith("|"):
        raw = raw[:-1]
    return [seg.strip() for seg in raw.split("|")]


def is_markdown_table_separator(line_str: str) -> bool:
    """Checks if a string is a markdown table separator row (|---|---| or |:---:|)."""
    if not line_str or "|" not in line_str:
        return False
    cells = clean_split_pipe_line(line_str)
    if not cells:
        return False
    return all(bool(re.match(r"^[:\-=\s]+$", c)) for c in cells if c) and any("-" in c or "=" in c for c in cells)


def parse_markdown_table(text: str) -> list:
    """
    Regex and parsing utility to detect and extract Markdown tables (| ... |).
    Parses headers, separators (|---|), and data rows into structured Python lists:
    [headers, [row1_data], [row2_data], ...]
    - Ignores trailing/leading whitespace and empty split segments.
    - Never renders markdown table separator lines (|---|---|) as data rows.
    - Stitches unescaped line breaks and auto-pads / merges mismatched columns to ensure uniform column widths.
    """
    if not text or not isinstance(text, str) or "|" not in text:
        return []

    match = TABLE_REGEX.search(text)
    table_block = match.group(0) if match else text

    raw_lines = [l.strip() for l in table_block.strip().split("\n") if l.strip()]
    if len(raw_lines) < 2:
        return []

    # Locate the header row and its separator
    header_idx = -1
    for i in range(len(raw_lines) - 1):
        if "|" in raw_lines[i] and is_markdown_table_separator(raw_lines[i + 1]):
            header_idx = i
            break

    if header_idx == -1:
        return []

    raw_headers = clean_split_pipe_line(raw_lines[header_idx])
    headers = [h for h in raw_headers if h] or raw_headers
    target_cols = len(headers)
    if target_cols == 0:
        return []

    # Process data lines after the separator
    data_lines = raw_lines[header_idx + 2:]
    stitched_lines = []
    curr = ""

    for dl in data_lines:
        if is_markdown_table_separator(dl):
            continue
        if "|" in dl:
            if curr:
                stitched_lines.append(curr)
            curr = dl
        else:
            if curr:
                curr += " " + dl
            else:
                curr = dl
    if curr and not is_markdown_table_separator(curr):
        stitched_lines.append(curr)

    parsed_rows = [headers]
    for sl in stitched_lines:
        if is_markdown_table_separator(sl):
            continue
        cells = clean_split_pipe_line(sl)
        if not cells:
            continue
        cleaned_cells = [re.sub(r'\|+', ' ', c).strip() for c in cells]
        if not any(cleaned_cells) or all(re.match(r"^[:\-=\s]*$", c) for c in cleaned_cells):
            continue

        # Merge or auto-pad so every row has exact target_cols
        if len(cleaned_cells) < target_cols:
            cleaned_cells = cleaned_cells + [""] * (target_cols - len(cleaned_cells))
        elif len(cleaned_cells) > target_cols:
            cleaned_cells = cleaned_cells[:target_cols - 1] + [" ".join(cleaned_cells[target_cols - 1:])]
        parsed_rows.append(cleaned_cells)

    if len(parsed_rows) >= 2:
        return parsed_rows
    return []


def get_proportional_col_widths(num_cols: int) -> list:
    """
    Returns explicit proportional column widths to prevent horizontal overflow.
    e.g., [35, 15, 50] for 3-column layouts.
    """
    if num_cols <= 1:
        return [100]
    elif num_cols == 2:
        return [35, 65]
    elif num_cols == 3:
        return [35, 15, 50]
    elif num_cols == 4:
        return [25, 20, 25, 30]
    elif num_cols == 5:
        return [20, 15, 20, 20, 25]
    else:
        eq = round(100.0 / num_cols, 2)
        return [eq] * num_cols


def render_markdown_table_to_fpdf(pdf, markdown_table_text: str) -> bool:
    """
    Renders a Markdown table string directly to FPDF using native pdf.table grid:
    - Parses Markdown table string line-by-line.
    - Strips out separator lines and empty rows generated by table divider lines (|---|---|).
    - Cleans out loose vertical pipe characters (|) before writing cell text.
    - Extracts header row separately from body rows.
    - Header Row: Dark background fill (RGB: 15, 23, 42), bold white text, center-aligned.
    - Data Rows: Alternating zebra background colors (RGB: 255, 255, 255 and RGB: 248, 250, 252).
    - Enforces uniform row height and auto-wrapping for multi-line cells using line_height=6 and min_row_height=7.
    """
    if not markdown_table_text or not isinstance(markdown_table_text, str):
        return False

    raw_lines = [l.strip() for l in markdown_table_text.strip().split("\n") if l.strip()]
    if not raw_lines:
        return False

    header_row = None
    body_rows = []

    # First pass: stitch unescaped line breaks and filter out separator rows
    stitched_lines = []
    curr = ""
    for l in raw_lines:
        if is_markdown_table_separator(l):
            if curr:
                stitched_lines.append(curr)
                curr = ""
            continue
        if "|" in l:
            if curr:
                stitched_lines.append(curr)
            curr = l
        else:
            if curr:
                curr += " " + l
            else:
                curr = l
    if curr:
        stitched_lines.append(curr)

    for l in stitched_lines:
        if is_markdown_table_separator(l):
            continue
        cells = clean_split_pipe_line(l)
        if not cells:
            continue

        # Clean out loose vertical pipe characters (|) from each cell segment
        cleaned_cells = [re.sub(r'\|+', ' ', c).strip() for c in cells]

        # Strip out empty rows or rows generated by table divider lines (|---|---|)
        if not any(cleaned_cells) or all(re.match(r"^[:\-=\s]*$", c) for c in cleaned_cells):
            continue

        if header_row is None:
            header_row = cleaned_cells
        else:
            target_cols = len(header_row)
            if len(cleaned_cells) < target_cols:
                cleaned_cells = cleaned_cells + [""] * (target_cols - len(cleaned_cells))
            elif len(cleaned_cells) > target_cols:
                cleaned_cells = cleaned_cells[:target_cols - 1] + [" ".join(cleaned_cells[target_cols - 1:])]
            body_rows.append(cleaned_cells)

    if not header_row:
        return False

    num_cols = len(header_row)
    if num_cols == 3:
        col_widths = (30, 20, 50)
    elif num_cols == 2:
        col_widths = (35, 65)
    elif num_cols == 4:
        col_widths = (25, 20, 25, 30)
    else:
        col_widths = tuple(round(100.0 / num_cols, 1) for _ in range(num_cols))

    font_family = getattr(pdf, "font_family_name", "Helvetica")
    h_style = None
    if FontFace is not None:
        try:
            h_style = FontFace(
                family=font_family,
                emphasis="B",
                color=(255, 255, 255),
                fill_color=(15, 23, 42)
            )
        except Exception:
            h_style = None

    try:
        pdf.ln(2)
        pdf.set_x(pdf.l_margin)
        pdf.set_font(font_family, size=8.5)
        pdf.set_text_color(30, 41, 59)

        with pdf.table(
            col_widths=col_widths,
            borders_layout="ALL",
            line_height=6,
            min_row_height=7,
            cell_fill_color=(248, 250, 252),
            cell_fill_mode="EVEN_ROWS",
            headings_style=h_style,
            first_row_as_headings=True,
            padding=(1.5, 2, 1.5, 2),
            v_align="MIDDLE",
            wrapmode="WORD"
        ) as table:
            # Header Row: Dark background fill (15, 23, 42), bold white text, center-aligned
            h_row = table.row()
            for h in header_row:
                clean_h = sanitize_pdf_text(format_math_for_pdf(h), is_unicode=getattr(pdf, "is_unicode", False))
                clean_h = clean_h.replace("|", " ")
                clean_h = re.sub(r'[*_`#|]', '', clean_h).strip()
                h_row.cell(clean_h, align="CENTER")

            # Data Rows: Alternating zebra background colors, uniform row height & clean auto-wrap
            for r in body_rows:
                d_row = table.row()
                for c in r:
                    clean_c = sanitize_pdf_text(format_math_for_pdf(c), is_unicode=getattr(pdf, "is_unicode", False))
                    clean_c = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_c)
                    clean_c = re.sub(r'(?<![a-zA-Z0-9])\*(.*?)\*(?![a-zA-Z0-9])', r'\1', clean_c)
                    clean_c = clean_c.replace("|", " ")
                    clean_c = re.sub(r'[`#|]', '', clean_c).strip()
                    d_row.cell(clean_c)

        pdf.ln(3)
        pdf.set_x(pdf.l_margin)
        return True
    except Exception as e:
        print(f"Table rendering fallback notice: {e}")
        return False


if FPDF is not None:
    class TopperPDF(FPDF):
        def __init__(self, title_text="Academic Document"):
            super().__init__(orientation="P", unit="mm", format="A4")
            self.doc_title = title_text
            self.is_unicode = False

            # Attempt to load Arial TrueType font for native math & Unicode glyph support
            win_font = r"C:\Windows\Fonts\arial.ttf"
            win_font_b = r"C:\Windows\Fonts\arialbd.ttf"
            win_font_i = r"C:\Windows\Fonts\ariali.ttf"
            if os.path.exists(win_font):
                try:
                    self.add_font("TopperFont", "", win_font)
                    if os.path.exists(win_font_b):
                        self.add_font("TopperFont", "B", win_font_b)
                    if os.path.exists(win_font_i):
                        self.add_font("TopperFont", "I", win_font_i)
                    self.font_family_name = "TopperFont"
                    self.is_unicode = True
                except Exception:
                    self.font_family_name = "Helvetica"
            else:
                self.font_family_name = "Helvetica"

            self.set_auto_page_break(auto=True, margin=18)
            self.set_margins(15, 30, 15)
            self.alias_nb_pages()

        def header(self):
            # 1. Subtle diagonal watermark text: "TOPPERGPT - ACADEMIC AI" in exact center
            # Rendered BEFORE header banner or body text so it stays strictly in the background
            try:
                self.set_font(self.font_family_name, style="B", size=32)
                self.set_text_color(240, 240, 240)
                w_text = "TOPPERGPT - ACADEMIC AI"
                str_w = self.get_string_width(w_text)
                if hasattr(self, "rotation"):
                    with self.rotation(angle=45, x=105, y=148.5):
                        self.text(105 - (str_w / 2), 148.5, w_text)
                else:
                    self.text(105 - (str_w / 2), 148.5, w_text)
            except Exception:
                pass

            # 2. Top bar branded header banner with dark background #0B0F19 (RGB: 11, 15, 25)
            self.set_fill_color(11, 15, 25)
            self.rect(0, 0, 210, 22, style="F")

            # Header Logo if available
            logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
            if os.path.exists(logo_path):
                try:
                    self.image(logo_path, x=15, y=4, w=14)
                    text_x = 33
                except Exception:
                    text_x = 15
            else:
                text_x = 15

            # Cyan Brand Title: "TopperGPT | Academic AI"
            self.set_xy(text_x, 5)
            self.set_font(self.font_family_name, style="B", size=13)
            self.set_text_color(88, 193, 200)  # Brand Cyan #58C1C8
            self.cell(0, 6, "TopperGPT | Academic AI", new_x="LMARGIN", new_y="NEXT")

            # Subtle document subtitle
            self.set_xy(text_x, 12)
            self.set_font(self.font_family_name, style="I", size=8.5)
            self.set_text_color(160, 175, 195)
            sub_title = self.doc_title if self.doc_title else "University Examination & Academic Resource"
            clean_sub = sanitize_pdf_text(sub_title[:75], is_unicode=self.is_unicode)
            self.cell(0, 5, clean_sub, new_x="LMARGIN", new_y="NEXT")

            # Reset Y position below header banner
            self.set_y(30)

        def footer(self):
            # Centered page numbers: "Page X of Y"
            self.set_y(-14)
            self.set_font(self.font_family_name, style="", size=8.5)
            self.set_text_color(140, 150, 165)
            self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="C")

        def add_markdown_content(self, md_text: str):
            md_text = clean_output_text(md_text)
            md_text = format_math_for_pdf(md_text)
            md_text = sanitize_pdf_text(md_text, is_unicode=self.is_unicode)

            lines = md_text.split("\n")
            in_code_block = False
            i = 0
            n = len(lines)

            while i < n:
                raw_line = lines[i]
                line = raw_line.rstrip()
                trimmed = line.strip()

                if not trimmed:
                    self.ln(2)
                    i += 1
                    continue

                if trimmed.startswith("```"):
                    in_code_block = not in_code_block
                    i += 1
                    continue

                # 1. Section Detector: Native FPDF Table Rendering
                if not in_code_block and (trimmed.startswith("|") or is_markdown_table_separator(trimmed) or ("|" in trimmed and i + 1 < n and ("|" in lines[i + 1] or is_markdown_table_separator(lines[i + 1])))):
                    table_lines = [trimmed]
                    i += 1
                    while i < n:
                        next_line = lines[i].strip()
                        if not next_line:
                            if i + 1 < n and ("|" in lines[i + 1] or is_markdown_table_separator(lines[i + 1])):
                                i += 1
                                continue
                            else:
                                break
                        if next_line.startswith("#") or (not is_markdown_table_separator(next_line) and (next_line.startswith("---") or next_line.startswith("==="))):
                            break
                        if "|" in next_line or is_markdown_table_separator(next_line):
                            table_lines.append(next_line)
                            i += 1
                        elif not next_line.startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.")):
                            table_lines.append(next_line)
                            i += 1
                        else:
                            break

                    table_text = "\n".join(table_lines)
                    rendered = render_markdown_table_to_fpdf(self, table_text)
                    if rendered:
                        continue
                    else:
                        for t_line in table_lines:
                            clean_t = re.sub(r'\|', '  ', t_line).strip()
                            if clean_t and not is_markdown_table_separator(t_line):
                                self.multi_cell(0, 7, clean_t, new_x="LMARGIN", new_y="NEXT")
                        self.ln(2)
                        continue

                # 2. Section Headings
                if trimmed.startswith("###"):
                    heading = trimmed.lstrip("#").strip()
                    heading = re.sub(r'[*_`|]', '', heading)
                    self.ln(3)
                    self.set_x(self.l_margin)
                    self.set_font(self.font_family_name, style="B", size=11)
                    self.set_text_color(15, 23, 42)
                    self.multi_cell(0, 7, heading, new_x="LMARGIN", new_y="NEXT")
                    self.ln(1)
                elif trimmed.startswith("##"):
                    heading = trimmed.lstrip("#").strip()
                    heading = re.sub(r'[*_`|]', '', heading)
                    self.ln(4)
                    self.set_x(self.l_margin)
                    self.set_font(self.font_family_name, style="B", size=12.5)
                    self.set_text_color(11, 15, 25)
                    self.multi_cell(0, 7, heading, new_x="LMARGIN", new_y="NEXT")
                    self.ln(1)
                elif trimmed.startswith("#"):
                    heading = trimmed.lstrip("#").strip()
                    heading = re.sub(r'[*_`|]', '', heading)
                    self.ln(5)
                    self.set_x(self.l_margin)
                    self.set_font(self.font_family_name, style="B", size=14)
                    self.set_text_color(11, 15, 25)
                    self.multi_cell(0, 7, heading, new_x="LMARGIN", new_y="NEXT")
                    self.ln(2)
                elif trimmed.startswith("---") or trimmed.startswith("==="):
                    self.ln(2)
                    self.set_draw_color(226, 232, 240)
                    self.set_line_width(0.3)
                    curr_y = self.get_y()
                    self.line(self.l_margin, curr_y, self.w - self.r_margin, curr_y)
                    self.ln(3)
                elif trimmed.startswith("- ") or trimmed.startswith("* "):
                    bullet_body = trimmed[2:].strip()
                    # Strip markdown bold/italic tags while preserving subscripts like _k, V_p
                    bullet_clean = re.sub(r'\*\*(.*?)\*\*', r'\1', bullet_body)
                    bullet_clean = re.sub(r'(?<![a-zA-Z0-9])\*(.*?)\*(?![a-zA-Z0-9])', r'\1', bullet_clean)
                    bullet_clean = re.sub(r'(?<=\s)_(?!\s)(.*?)(?<!\s)_(?=\s|[.,;:!?]|$)', r'\1', bullet_clean)
                    bullet_clean = re.sub(r'[`#|]', '', bullet_clean).strip()
                    self.set_font(self.font_family_name, style="", size=9.5)
                    self.set_text_color(51, 65, 85)
                    self.set_x(self.l_margin + 3)
                    self.multi_cell(self.epw - 3, 7, f"-  {bullet_clean}", new_x="LMARGIN", new_y="NEXT")
                else:
                    # 3. Standard Paragraphs (line_height=7, clean dangling markdown symbols)
                    clean_p = re.sub(r'\*\*(.*?)\*\*', r'\1', trimmed)
                    clean_p = re.sub(r'(?<![a-zA-Z0-9])\*(.*?)\*(?![a-zA-Z0-9])', r'\1', clean_p)
                    clean_p = re.sub(r'(?<=\s)_(?!\s)(.*?)(?<!\s)_(?=\s|[.,;:!?]|$)', r'\1', clean_p)
                    clean_p = re.sub(r'[`#]', '', clean_p)
                    # Clean lingering markdown pipes and dashed lines outside tables
                    clean_p = re.sub(r'(?<!\S)\|(?!\S)', ' ', clean_p)
                    clean_p = re.sub(r'^\s*\|\s*', '', clean_p)
                    clean_p = re.sub(r'\s*\|\s*$', '', clean_p)
                    clean_p = re.sub(r'\s*\|\s*', '  ', clean_p)
                    clean_p = re.sub(r'---+', '', clean_p).strip()
                    if clean_p:
                        self.set_x(self.l_margin)
                        self.set_font(self.font_family_name, style="", size=9.5)
                        self.set_text_color(51, 65, 85)
                        self.multi_cell(0, 7, clean_p, new_x="LMARGIN", new_y="NEXT")

                i += 1
else:
    TopperPDF = None


def generate_fallback_pdf(title: str, content: str, feature_name: str = "Academic Report") -> bytes:
    """Pure-Python fallback PDF generator if FPDF library is unavailable in environment."""
    clean_text = sanitize_pdf_text(format_math_for_pdf(clean_output_text(content)), is_unicode=False)
    lines = [
        "TopperGPT | Academic AI Workspace",
        f"Feature: {feature_name}",
        f"Title: {title}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "--------------------------------------------------",
        ""
    ]
    for raw_line in clean_text.split("\n"):
        line = raw_line.strip()
        while len(line) > 75:
            lines.append(line[:75])
            line = line[75:]
        lines.append(line)

    text_ops = [
        "BT /F1 28 Tf 50 400 Td (TOPPERGPT - ACADEMIC AI) Tj ET",
        "BT /F1 14 Tf 40 800 Td (TopperGPT | Academic AI Workspace) Tj ET",
        "BT /F2 11 Tf 40 782 Td (" + sanitize_pdf_text(title[:60], is_unicode=False).replace("(", "\\(").replace(")", "\\)") + ") Tj ET"
    ]
    y = 750
    for l in lines[:55]:
        safe_l = l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        text_ops.append(f"BT /F3 9.5 Tf 40 {y} Td ({safe_l}) Tj ET")
        y -= 12
        if y < 45:
            break

    stream_content = "\n".join(text_ops).encode("latin-1", "ignore")
    stream_len = len(stream_content)
    return (
        f"%PDF-1.4\n"
        f"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        f"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        f"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R /F2 5 0 R /F3 6 0 R >> >> /Contents 7 0 R >> endobj\n"
        f"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj\n"
        f"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj\n"
        f"6 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        f"7 0 obj << /Length {stream_len} >> stream\n"
    ).encode("latin-1") + stream_content + (
        f"\nendstream\nendobj\n"
        f"xref\n0 8\n0000000000 65535 f \n"
        f"trailer << /Size 8 /Root 1 0 R >>\nstartxref\n50\n%%EOF"
    ).encode("latin-1")


def generate_topper_pdf(title: str, content: str, feature_name: str = "Academic Report") -> bytes:
    """
    Generates a professional TopperGPT academic PDF with:
    - Top bar header banner with dark background #0B0F19, cyan title 'TopperGPT | Academic AI' (#58C1C8), and subtitle.
    - Subtle diagonal background watermark text: 'TOPPERGPT - ACADEMIC AI' (RGB: 240, 240, 240) in exact center.
    - Clean margins, multi_cell(0, 8, text) paragraph word wrapping, and centered 'Page X of Y' footer.
    Returns PDF bytes for st.download_button.
    """
    if FPDF is not None and TopperPDF is not None:
        try:
            pdf = TopperPDF(title_text=f"{feature_name} - {title}")
            pdf.add_page()

            # Main Title Header
            pdf.set_x(pdf.l_margin)
            pdf.set_font(pdf.font_family_name, style="B", size=15)
            pdf.set_text_color(11, 15, 25)
            clean_title = sanitize_pdf_text(title.upper(), is_unicode=pdf.is_unicode)
            pdf.multi_cell(0, 8, clean_title, new_x="LMARGIN", new_y="NEXT")

            pdf.set_x(pdf.l_margin)
            pdf.set_font(pdf.font_family_name, style="I", size=8.5)
            pdf.set_text_color(100, 116, 139)
            meta_text = f"Category: {feature_name}   |   Date: {datetime.now().strftime('%d %B %Y, %I:%M %p')}"
            pdf.cell(0, 6, sanitize_pdf_text(meta_text, is_unicode=pdf.is_unicode), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

            pdf.add_markdown_content(content)

            out = pdf.output()
            if isinstance(out, (bytes, bytearray)):
                return bytes(out)
            elif isinstance(out, str):
                return out.encode("latin-1")
        except Exception as e:
            print(f"FPDF Generation Notice: {e}")

    return generate_fallback_pdf(title, content, feature_name)


def format_topic_research_for_pdf(topic_name: str, topic_dict: dict) -> str:
    """Formats Topic Research 3-card dictionary into markdown for PDF generation."""
    definition = topic_dict.get("definition", "Details unavailable.")
    breakdown = topic_dict.get("breakdown", "Details unavailable.")
    working_principle = topic_dict.get("working_principle", "Details unavailable.")

    return f"""### 1. Official Definition (2-Mark University Standard)
{definition}

---

### 2. Technical Breakdown & Architecture
{breakdown}

---

### 3. Working Principle & Operational Mechanics
{working_principle}
"""

# --- 7. BACKEND AI ENGINE (GROQ P1 + GEMINI P2 + OPENROUTER P3) ---
def generate_ai_response(prompt_or_messages, max_toks=700, messages_context=None, temperature=0.2, max_tokens=None):
    """
    Automatic 3-Tier Multi-Model AI Engine for Ultra-Fast Execution:
    - Accepts either a single string prompt OR a list of chat message dicts:
      [{"role": "system"/"user"/"assistant", "content": ...}]
    - Priority 1: Groq llama-3.1-8b-instant or llama3-8b-8192
    - Priority 2: Gemini 1.5 Flash via direct HTTP REST
    - Priority 3: OpenRouter meta-llama/llama-3.1-8b-instruct:free
    - Silent failover across tiers without throwing st.error until all 3 tiers fail.
    """
    if max_tokens is not None:
        max_toks = max_tokens

    tier_timeout = 25 if max_toks > 1000 else 12
    gemini_timeout = 25 if max_toks > 1000 else 15

    # -------------------------------------------------------------------------
    # 0. NORMALIZE & SANITIZE MESSAGES ARRAY
    # -------------------------------------------------------------------------
    if isinstance(prompt_or_messages, list):
        raw_messages = prompt_or_messages
    else:
        p_text = str(prompt_or_messages or "").strip()
        raw_messages = []
        if messages_context:
            raw_messages.extend(messages_context)
        raw_messages.append({"role": "user", "content": p_text})

    messages_array = []
    for m in raw_messages:
        r = str(m.get("role", "user")).lower().strip()
        if r not in ("system", "user", "assistant"):
            r = "user"
        c = str(m.get("content", "")).strip()
        if c:
            messages_array.append({"role": r, "content": c})

    if not messages_array:
        messages_array = [{"role": "user", "content": "Hello"}]

    # -------------------------------------------------------------------------
    # PRIORITY 1: Groq llama-3.1-8b-instant or llama3-8b-8192
    # -------------------------------------------------------------------------
    groq_key = (get_env_secret("GROQ_API_KEY") or get_env_secret("GROQ_API_KEY_2", "")).strip()
    if groq_key:
        groq_models = ["llama-3.1-8b-instant", "llama3-8b-8192"]
        for g_model in groq_models:
            try:
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={
                        "model": g_model,
                        "messages": messages_array,
                        "temperature": temperature,
                        "max_tokens": max_toks
                    },
                    timeout=tier_timeout
                )
                if res.status_code == 200:
                    choices = res.json().get("choices", [])
                    if choices and "message" in choices[0] and choices[0]["message"].get("content"):
                        out_text = choices[0]["message"]["content"].strip()
                        if out_text:
                            return clean_output_text(out_text)
            except Exception:
                continue

    # -------------------------------------------------------------------------
    # PRIORITY 2: Gemini 1.5 Flash via direct HTTP REST
    # -------------------------------------------------------------------------
    gemini_key = (get_env_secret("GEMINI_API_KEY") or get_env_secret("GOOGLE_API_KEY", "")).strip()
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            
            # Format history array into Gemini contents
            sys_parts = [m["content"] for m in messages_array if m["role"] == "system"]
            sys_text = "\n\n".join(sys_parts).strip()

            gemini_contents = []
            for m in messages_array:
                if m["role"] == "system":
                    continue
                g_role = "model" if m["role"] == "assistant" else "user"
                text_val = m["content"]
                if gemini_contents and gemini_contents[-1]["role"] == g_role:
                    gemini_contents[-1]["parts"][0]["text"] += "\n\n" + text_val
                else:
                    gemini_contents.append({"role": g_role, "parts": [{"text": text_val}]})

            if not gemini_contents:
                gemini_contents = [{"role": "user", "parts": [{"text": sys_text or "Hello"}]}]
            elif gemini_contents[0]["role"] == "model":
                gemini_contents.insert(0, {"role": "user", "parts": [{"text": "Hello"}]})

            gemini_payload = {
                "contents": gemini_contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_toks
                }
            }
            if sys_text:
                gemini_payload["system_instruction"] = {"parts": [{"text": sys_text}]}

            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=gemini_payload,
                timeout=gemini_timeout
            )
            if res.status_code == 200:
                cand = res.json().get('candidates', [])
                if cand and 'content' in cand[0] and 'parts' in cand[0]['content'] and cand[0]['content']['parts']:
                    out_text = cand[0]['content']['parts'][0].get('text', '').strip()
                    if out_text:
                        return clean_output_text(out_text)
            elif sys_text:
                # Retry by prepending system text to first user message if system_instruction is not supported
                gemini_contents[0]["parts"][0]["text"] = sys_text + "\n\n" + gemini_contents[0]["parts"][0]["text"]
                res2 = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": gemini_contents,
                        "generationConfig": {
                            "temperature": temperature,
                            "maxOutputTokens": max_toks
                        }
                    },
                    timeout=gemini_timeout
                )
                if res2.status_code == 200:
                    cand = res2.json().get('candidates', [])
                    if cand and cand[0].get('content', {}).get('parts'):
                        out_text = cand[0]['content']['parts'][0].get('text', '').strip()
                        if out_text:
                            return clean_output_text(out_text)
        except Exception:
            pass

    # Secondary Gemini API Key fallback if provided
    sec_gemini_key = (
        get_env_secret("GEMINI_API_KEY_2")
        or get_env_secret("GOOGLE_API_KEY_2")
        or get_env_secret("GEMINI_BACKUP_KEY")
        or get_env_secret("GEMINI_SECONDARY_KEY")
    ).strip()
    if sec_gemini_key and sec_gemini_key != gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={sec_gemini_key}"
            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=gemini_payload,
                timeout=gemini_timeout
            )
            if res.status_code == 200:
                cand = res.json().get('candidates', [])
                if cand and cand[0].get('content', {}).get('parts'):
                    out_text = cand[0]['content']['parts'][0].get('text', '').strip()
                    if out_text:
                        return clean_output_text(out_text)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # PRIORITY 3: OpenRouter (meta-llama/llama-3.1-8b-instruct:free)
    # -------------------------------------------------------------------------
    openrouter_key = get_env_secret("OPENROUTER_API_KEY").strip()
    if openrouter_key:
        or_models = [
            "meta-llama/llama-3.1-8b-instruct:free",
            "meta-llama/llama-3.2-3b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
            "openrouter/auto",
            "qwen/qwen3.8-27b:free",
            "liquid/lfm-2.5-2.6b:free",
            "nvidia/nemotron-3.5-lightning:free",
            "nex-agi/nex-n2.5-mini:free"
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
                        "messages": messages_array,
                        "max_tokens": max_toks,
                        "temperature": temperature,
                        "include_reasoning": False
                    },
                    timeout=tier_timeout
                )
                if res.status_code == 200:
                    choices = res.json().get("choices", [])
                    if choices and "message" in choices[0]:
                        msg = choices[0]["message"]
                        out_text = str(msg.get("content") or msg.get("reasoning") or "").strip()
                        if out_text:
                            return clean_output_text(out_text)
            except Exception:
                continue

    # -------------------------------------------------------------------------
    # ALL 3 TIERS FAILED: Raise Exception (Silent failover until all 3 tiers fail)
    # -------------------------------------------------------------------------
    raise RuntimeError("All AI generation tiers (Groq, Gemini, OpenRouter) failed due to API timeout or rate limit. Please retry.")


def generate_chat_response(messages, max_toks=1000, temperature=0.3):
    """
    Dedicated Multi-Turn Chat Response Engine:
    Accepts a list of message dicts [{"role": "system"/"user"/"assistant", "content": ...}]
    and routes through the multi-tier AI engine with temperature=0.3 and max_tokens=1000.
    """
    return generate_ai_response(messages, max_toks=max_toks, temperature=temperature)



# --- 5. AUTHENTICATION ---
def clean_email_auth():
    if "user_data" not in st.session_state:
        st.session_state.user_data = None

    # Instant session persistence: if already authenticated, bypass login screen immediately
    if st.session_state.user_data is not None:
        return

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Back to Home"):
            st.query_params.clear()
            st.rerun()

    st.markdown("""
        <div style="text-align:center; padding: 20px 0 10px 0;">
            <h1 style="color:var(--text-primary, #ffffff); font-size: 2.8rem; font-weight:800; margin: 10px 0;">
                Topper<span style="color:#58c1c8;">GPT</span>
            </h1>
            <p style="color:var(--text-muted, #94a3b8); font-size:15px; margin-top:0;">
                AI Academic Workspace for Mumbai University Engineering.
            </p>
        </div>
    """, unsafe_allow_html=True)

    if "pending_query" in st.session_state and st.session_state.pending_query:
        st.markdown(f"""
            <div style="background: rgba(88, 193, 200, 0.1); border: 1px solid rgba(88, 193, 200, 0.35); border-radius: 12px; padding: 12px 18px; margin: 0 auto 20px auto; max-width: 580px; text-align: center;">
                <span style="color: #58c1c8; font-weight: 700; font-size: 13px;">✦ QUESTION CAPTURED:</span>
                <span style="color: var(--text-primary, #ffffff); font-weight: 600;"> "{st.session_state.pending_query}"</span>
                <p style="font-size: 12px; color: var(--text-muted, #94a3b8); margin: 4px 0 0 0;">Enter your email to unlock your verified solution in TopperGPT!</p>
            </div>
        """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 1.8, 1])
    with center_col:
        st.markdown("""
            <div style="background: rgba(88, 193, 200, 0.06); border: 1px solid rgba(88, 193, 200, 0.25); border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; text-align: center;">
                <span style="color: #58c1c8; font-weight: 700; font-size: 13px;">✦ INSTANT ACADEMIC ACCESS</span>
                <p style="color: var(--text-muted, #94a3b8); font-size: 12px; margin: 4px 0 0 0;">Enter your academic email below or continue as Guest Student.</p>
            </div>
        """, unsafe_allow_html=True)

        if not st.session_state.get("guest_prompt_open", False):
            if st.button("🚀 CONTINUE AS GUEST STUDENT", use_container_width=True):
                st.session_state.guest_prompt_open = True
                st.rerun()
        else:
            st.markdown("""
                <div style="background: rgba(88, 193, 200, 0.08); border: 1px solid rgba(88, 193, 200, 0.3); border-radius: 12px; padding: 14px 16px; margin-bottom: 14px;">
                    <div style="color: #58c1c8; font-weight: 700; font-size: 13px; margin-bottom: 4px;">✦ GUEST STUDENT ONBOARDING</div>
                    <p style="color: var(--text-muted, #94a3b8); font-size: 12px; margin: 0 0 10px 0;">Please enter your name below to initialize your free guest session with trial limits.</p>
                </div>
            """, unsafe_allow_html=True)
            with st.form("guest_name_form"):
                g_name = st.text_input("Your Full Name", placeholder="e.g. Rahul Sharma", key="guest_name_field").strip()
                col_g1, col_g2 = st.columns([2, 1])
                with col_g1:
                    g_submit = st.form_submit_button("ENTER WORKSPACE 🚀", use_container_width=True)
                with col_g2:
                    g_cancel = st.form_submit_button("Cancel", use_container_width=True)

                if g_submit:
                    if not g_name:
                        st.error("⚠️ Please enter your name to continue as a guest student!")
                    else:
                        st.session_state.user_data = {
                            "email": "guest@toppergpt.in",
                            "full_name": g_name,
                            "is_pro": False,
                            "is_guest": True,
                            "trial_count": 5
                        }
                        st.session_state.guest_prompt_open = False
                        st.rerun()
                if g_cancel:
                    st.session_state.guest_prompt_open = False
                    st.rerun()

        st.markdown("<div style='text-align: center; margin: 12px 0; color: var(--text-dim, #64748b); font-size: 12px;'>─── OR SIGN IN WITH EMAIL ───</div>", unsafe_allow_html=True)

        auth_tab = st.tabs(["🔑 Quick Access", "📝 New Registration"])
        
        with auth_tab[0]:
            with st.form("quick_login"):
                l_email = st.text_input("Registered Email Address", placeholder="name@domain.com", key="l_email_quick").strip().lower()
                if st.form_submit_button("ENTER DASHBOARD 🚀", use_container_width=True):
                    if not l_email:
                        st.error("⚠️ Please enter your registered email address!")
                    elif not is_valid_email(l_email):
                        st.error("⚠️ Please enter a valid email address with a proper domain (e.g. name@domain.com)!")
                    else:
                        active_email = l_email
                        # Instant cached lookup
                        cached_prof = get_cached_profile(active_email)
                        if cached_prof:
                            st.session_state.user_data = cached_prof
                        else:
                            st.session_state.user_data = {
                                "email": active_email,
                                "full_name": active_email.split('@')[0].capitalize(),
                                "is_pro": True
                            }
                        st.rerun()

        with auth_tab[1]:
            with st.form("reg_form_quick"):
                s_name = st.text_input("Full Name", placeholder="Enter your full name", key="reg_name_quick").strip()
                s_email = st.text_input("Email Address", placeholder="name@domain.com", key="reg_email_quick").strip().lower()
                if st.form_submit_button("CREATE ACCOUNT 🔥", use_container_width=True):
                    if not s_name:
                        st.warning("⚠️ Please provide your full name.")
                    elif not s_email:
                        st.error("⚠️ Please enter your email address!")
                    elif not is_valid_email(s_email):
                        st.error("⚠️ Please enter a valid email address with a proper domain (e.g. name@domain.com)!")
                    else:
                        new_u = {"email": s_email, "full_name": s_name, "is_pro": True}
                        if supabase:
                            try:
                                supabase.table("profiles").insert(new_u).execute()
                            except Exception:
                                pass
                        st.session_state.user_data = new_u
                        st.rerun()
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
            <h2 style="color:var(--text-primary, #ffffff); margin:0; font-size:24px; font-weight:800; letter-spacing:-0.5px;">Topper<span style="color:#58c1c8;">GPT</span></h2>
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
        feat = str(st.session_state.pop("pending_feature", "")).lower()
        if "predict" in feat:
            default_nav_idx = 1
        elif "note" in feat:
            default_nav_idx = 2
        elif any(k in feat for k in ["solver", "research", "analytics", "flashcard"]):
            default_nav_idx = 3
        st.session_state.pop("unified_nav_radio", None)

    nav_selection = st.radio(
        "Navigation",
        nav_options,
        index=default_nav_idx,
        key="unified_nav_radio",
        label_visibility="collapsed"
    )

    st.markdown("""
        <div class="status-card">
            <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                <span style="display:inline-block; width:8px; height:8px; background:#22c55e; border-radius:50%;"></span>
                <span style="color:#22c55e; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px;">SYSTEM UNLOCKED</span>
            </div>
            <h4 style="color:var(--text-primary, #ffffff); margin:4px 0 2px 0; font-size:16px; font-weight:800;">Academic Access</h4>
            <p style="color:var(--text-muted, #94a3b8); font-size:12px; margin:0; line-height:1.4;">Unlimited access enabled for all university modules.</p>
        </div>
    """, unsafe_allow_html=True)


    with st.expander(f"👤 {(st.session_state.user_data or {}).get('full_name', 'Student')}", expanded=False):
        curr_email = (st.session_state.user_data or {}).get("email", "student@toppergpt.in")
        curr_name = (st.session_state.user_data or {}).get("full_name", "Student")
        st.caption(f"Active Account: {curr_email}")
        with st.form("edit_profile_sidebar"):
            new_name = st.text_input("Name", value=curr_name).strip()
            new_email = st.text_input("Email", value=curr_email).strip().lower()
            if st.form_submit_button("Save Profile"):
                if not new_name:
                    st.warning("⚠️ Name cannot be empty.")
                elif new_email and not is_valid_email(new_email):
                    st.error("⚠️ Please enter a valid email address (e.g. name@domain.com)!")
                else:
                    if "user_data" not in st.session_state or not st.session_state.user_data:
                        st.session_state.user_data = {}
                    st.session_state.user_data["full_name"] = new_name
                    if new_email:
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
    st.markdown(f"<h1 class='page-main-title' style='color:var(--text-primary, #ffffff); margin:0 0 15px 0;'>{clean_title}</h1>", unsafe_allow_html=True)
with col_badge:
    st.markdown("<div class='streak-badge'>🔥 6-day study streak</div>", unsafe_allow_html=True)

# Helper function for Instant Hinglish Translation
def translate_to_hinglish(text_content):
    prompt = f"""Be extremely direct, concise, and structured. No fluff, no introductory chatter, no conversational filler.
Translate and simplify the following engineering explanation into clear, friendly Hinglish (Hindi written in English alphabets) so that an Indian student can understand it effortlessly. Keep all equations and mathematical variables intact.

    MATHEMATICAL NOTATION INSTRUCTIONS:
    - Wrap ALL inline math variables/formulas in single dollar signs (e.g., $V_p / V_s$, $R_{{eq}}$).
    - Wrap ALL standalone or display equations in double dollar signs ($$...$$).
    - Never use \\displaystyle or wrap equations in raw curly braces {{...}} without dollar signs.

    Text:
    {text_content}"""
    return generate_ai_response(prompt, max_toks=700, temperature=0.2)


# ==================================================
# --- 1. FEATURE: AI ACADEMIC TUTOR ---
# ==================================================
if nav_selection == "💡 AI Tutor":
    st.markdown("""
        <div class="starter-chip-container">
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

    AI_TUTOR_SYSTEM_INSTRUCTION = (
        "You are TopperGPT's 24/7 AI Academic Tutor, operating as a Senior Evaluator, Subject Matter Expert, and Academic Mentor "
        "for Mumbai University (MU) Engineering students under the C-Scheme. Maintain full context of the ongoing conversation history. "
        "If the student asks follow-up requests such as 'explain in simple english', 'give an example', 'summarize this', or 'explain again', "
        "apply the request directly to the previous AI response in the conversation history without asking what topic they are referring to.\n\n"
        "Be extremely direct, concise, and structured. No fluff, no introductory chatter, no conversational filler.\n"
        "Respond exclusively in professional, clear, exam-oriented English for Mumbai University Engineering (C-Scheme).\n\n"
        "MATHEMATICAL NOTATION RULES:\n"
        "- Wrap ALL inline variables and formulas in single dollar signs (e.g., $V_p / V_s$, $R_{eq}$, $I_1$).\n"
        "- Wrap ALL standalone or block equations in double dollar signs ($$...$$).\n"
        "- NEVER use \\displaystyle or wrap formulas in bare curly braces {...} without dollar signs.\n\n"
        "RESPONSE GUIDELINES:\n"
        "1. If conversational (greetings, general chat): Reply politely and concisely in 1-2 sentences.\n"
        "2. If follow-up request (e.g., 'explain in simple english', 'give an example', 'summarize this', 'explain again', 'simplify'): "
        "Apply the request directly to the previous AI response in the conversation history without asking what topic they are referring to.\n"
        "3. If academic topic/question: Use the strict 3-block structure:\n"
        "   ### 📌 1. University Standard Definition (2-Mark Standard)\n"
        "   Accurate textbook definition and mandatory examiner keywords.\n\n"
        "   ### ⚡ 2. Step-by-Step Technical Execution & Derivation\n"
        "   Logically organized steps, formulas with Markdown LaTeX ($...$ or $$...$$), and specific 'Exam Diagram Requirement' if applicable.\n\n"
        "   ### ⚠️ 3. Examiner Trap Alert\n"
        "   Precise calculation error, unit conversion, or assumption where students frequently lose marks."
    )

    # Auto-process pending query from Landing Page search
    if "pending_query" in st.session_state and st.session_state.pending_query:
        init_q = st.session_state.pop("pending_query")
        st.session_state.tutor_messages.append({"role": "user", "content": init_q, "hinglish": None})
        with st.spinner("⚡ Consulting AI Tutor..."):
            messages_payload = [{"role": "system", "content": AI_TUTOR_SYSTEM_INSTRUCTION}]
            for m in st.session_state.tutor_messages[-6:]:
                messages_payload.append({
                    "role": "assistant" if m.get("role") == "assistant" else "user",
                    "content": str(m.get("content", "")).strip()
                })
            try:
                ai_reply = generate_chat_response(messages_payload, max_toks=1000, temperature=0.3)
                st.session_state.tutor_messages.append({"role": "assistant", "content": ai_reply, "hinglish": None})
            except Exception:
                st.session_state.tutor_messages.append({
                    "role": "assistant",
                    "content": "Generation failed due to API timeout or rate limit. Please retry.",
                    "hinglish": None
                })
        st.rerun()

    for idx, msg in enumerate(st.session_state.tutor_messages):
        with st.chat_message(msg["role"]):
            st.markdown(clean_output_text(msg["content"]))
            if msg["role"] == "assistant" and idx > 0:
                if msg.get("hinglish"):
                    with st.expander("🗣️ View Hinglish Explanation"):
                        st.markdown(clean_output_text(msg["hinglish"]))
                else:
                    if st.button("🗣️ Explain in Hinglish", key=f"tr_{idx}"):
                        with st.spinner("⚡ Translating to simple Hinglish..."):
                            h_res = translate_to_hinglish(msg["content"])
                            st.session_state.tutor_messages[idx]["hinglish"] = h_res
                            st.rerun()

    user_query = st.chat_input("Ask a doubt, request notes, or get PYQs...")

    if user_query:
        st.session_state.tutor_messages.append({"role": "user", "content": user_query, "hinglish": None})
        with st.chat_message("user"):
            st.markdown(clean_output_text(user_query))

        # Dynamic messages payload with system instruction and the last 6 messages
        messages_payload = [{"role": "system", "content": AI_TUTOR_SYSTEM_INSTRUCTION}]
        for m in st.session_state.tutor_messages[-6:]:
            messages_payload.append({
                "role": "assistant" if m.get("role") == "assistant" else "user",
                "content": str(m.get("content", "")).strip()
            })

        with st.chat_message("assistant"):
            with st.spinner("⚡ Consulting AI Tutor..."):
                try:
                    ai_reply = generate_chat_response(messages_payload, max_toks=1000, temperature=0.3)
                    st.markdown(clean_output_text(ai_reply))
                    st.session_state.tutor_messages.append({"role": "assistant", "content": ai_reply, "hinglish": None})
                    st.rerun()
                except Exception:
                    st.error("Generation failed due to API timeout or rate limit. Please retry.")

# ==================================================
# --- 2. FEATURE: PREDICTED QUESTIONS ---
# ==================================================
elif nav_selection == "🎯 Predicted Qs":
    st.markdown("""
        <div class="topper-card">
            <h3 style="margin-top:0; color:#58c1c8;">Target High-Probability Examination Questions</h3>
            <p style="color:var(--text-muted, #94a3b8); font-size:14px; margin:0;">
                Predict recurring Mumbai University questions, examiner marking rubrics, and previous year variations.
            </p>
        </div>
    """, unsafe_allow_html=True)

    p_topic = st.text_input("Enter Topic or Module Name:", placeholder="e.g. Runge-Kutta 4th Order, Virtual Memory, BJT Biasing, Trees", key="pred_topic_input")

    if st.button("Generate Exam Blueprint ⚡", use_container_width=True):
        if not p_topic.strip():
            st.warning("Please enter a valid topic or chapter name.")
        else:
            with st.spinner(f"⚡ Predicting high-yield MU exam questions for '{p_topic}'..."):
                pred_prompt = f"""Be extremely direct, concise, and structured. No fluff, no introductory chatter, no conversational filler.
You are a Senior Mumbai University Engineering Paper Setter.
Target Topic: {p_topic}
Language: Strictly Professional English.

MATHEMATICAL NOTATION RULES:
- Wrap ALL inline variables and formulas in single dollar signs (e.g., $V_p / V_s$, $R_{{eq}}$, $I_1$).
- Wrap ALL standalone or block equations in double dollar signs ($$...$$).
- NEVER use \\displaystyle or wrap formulas in bare curly braces {{...}} without dollar signs.

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
                    res_text = generate_ai_response(pred_prompt, max_toks=700, temperature=0.2)
                    st.session_state.pred_result = res_text
                    st.session_state.pred_topic_name = p_topic
                    st.session_state.pred_hinglish = None
                    st.rerun()
                except Exception:
                    st.error("Generation failed due to API timeout or rate limit. Please retry.")

    if "pred_result" in st.session_state and st.session_state.pred_result:
        st.markdown("---")
        st.markdown(f"### 📘 Exam Blueprint: **{st.session_state.get('pred_topic_name', '').upper()}**")
        st.markdown(clean_output_text(st.session_state.pred_result))

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            if not st.session_state.get("pred_hinglish"):
                if st.button("🗣️ Translate to Hinglish", key="trans_pred", use_container_width=True):
                    with st.spinner("⚡ Translating blueprint to Hinglish..."):
                        st.session_state.pred_hinglish = translate_to_hinglish(st.session_state.pred_result)
                        st.rerun()
        with col_act2:
            pred_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            pred_pdf = generate_topper_pdf(
                title=f"Exam Blueprint: {st.session_state.get('pred_topic_name', 'Topic')}",
                content=st.session_state.pred_result,
                feature_name="Predicted Questions"
            )
            st.download_button(
                "📥 Download PDF",
                data=pred_pdf,
                file_name=f"TopperGPT_PredictedQuestions_{pred_ts}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        if st.session_state.get("pred_hinglish"):
            with st.expander("🗣️ View Hinglish Blueprint Translation", expanded=True):
                st.markdown(clean_output_text(st.session_state.pred_hinglish))

# ==================================================
# --- 3. FEATURE: CHAPTER SHORT-NOTES ---
# ==================================================
elif nav_selection == "📄 Short Notes":
    st.markdown("""
        <div class="topper-card">
            <h3 style="margin-top:0; color:#58c1c8;">1-Page Exam Cheat Sheet</h3>
            <p style="color:var(--text-muted, #94a3b8); font-size:14px; margin:0;">
                Synthesize high-yield formulas with proper SI units, high-scoring modules, and rapid revision notes.
            </p>
        </div>
    """, unsafe_allow_html=True)

    sn_topic = st.text_input("Enter Chapter / Module Name:", placeholder="e.g. Semiconductor Physics, AC Circuits, Interpolation", key="sn_topic_input")

    if st.button("Generate Revision Sheet 📑", use_container_width=True):
        if not sn_topic.strip():
            st.warning("Please enter a chapter name.")
        else:
            user_topic = sn_topic.strip()
            with st.spinner(f"⚡ Generating high-yield revision sheet for '{user_topic}'..."):
                sn_prompt = f"""Be extremely direct, concise, and structured. No fluff, no introductory chatter, no conversational filler.
Generate a comprehensive, structured 1-page Mumbai University (MU) exam revision sheet for topic: {user_topic}. Include 3 sections: 1. Core Numerical Formulas & Parameters, 2. High-Weightage Core Topics, 3. 5-Minute Rapid Revision Keywords.

CRITICAL INSTRUCTIONS:
- You are TopperGPT, Senior Academic Evaluator for Mumbai University.
- Provide comprehensive coverage of core formulas (at least 5 to 7 essential equations) so the student has complete coverage for numericals and derivations.
- STRICT PROHIBITION: Do NOT use markdown tables (|---|---|) anywhere in your response. Instead, use clean, organized bullet points with bold sub-headers so equations, parameters, and notes never break or wrap awkwardly.
- Use direct bullet points and clean markdown formatting without any conversational introductory fluff, greetings, apologies, or preamble (e.g., absolutely NO 'Sure, here are your notes...', 'Certainly! Here is...').
- Start IMMEDIATELY with the heading '### 1. 🧮 Core Numerical Formulas & Parameters'.
- Do NOT output conversational sign-offs or outro text.
- Strictly adhere to the EXACT 3-block structure below:

### 1. 🧮 Core Numerical Formulas & Parameters
- **[Formula Name]**: [Equation]
  - **Variables & SI Units**: [List each variable and its SI unit]
  - **Exam Application**: [1 line where and how it is applied in MU numericals]

### 2. 🎯 High-Weightage Core Topics
List 4 to 5 high-yield exam topics with expected marks ([2M], [6M], or [10M]). Do NOT use tables:
- **[Topic Name]** ([2M/6M/10M]):
  - **Key Requirements**: [Key definitions, derivations, circuit diagrams, or working points required by Mumbai University paper setters for full marks]
  - **Examiner Focus**: [Common pitfalls, examiner expectations, and must-include keywords]

### 3. ⚡ 5-Minute Rapid Revision Keywords
- **[Term/Keyword]**: [Direct 1-line definition with key exam buzzwords]
"""
                try:
                    sn_res = generate_ai_response(sn_prompt, max_tokens=1500, temperature=0.3)
                    sn_res_clean = (sn_res or "").strip()
                    if not sn_res_clean or len(sn_res_clean) < 50:
                        st.error("Generation failed due to API timeout or rate limit. Please retry.")
                    else:
                        st.session_state.short_notes_data = sn_res_clean
                        st.session_state.sn_data = sn_res_clean
                        st.session_state.sn_name = user_topic
                        st.session_state.sn_hinglish = None
                        st.rerun()
                except Exception:
                    st.error("Generation failed due to API timeout or rate limit. Please retry.")

    short_notes_content = st.session_state.get("short_notes_data") or st.session_state.get("sn_data")
    if short_notes_content and str(short_notes_content).strip():
        st.markdown("---")
        st.markdown(f"### 📘 Revision Sheet: **{st.session_state.get('sn_name', '').upper()}**")
        st.markdown(clean_output_text(short_notes_content))

        col_sn1, col_sn2 = st.columns([1, 1])
        with col_sn1:
            if not st.session_state.get("sn_hinglish"):
                if st.button("🗣️ Translate to Hinglish", key="trans_sn", use_container_width=True):
                    with st.spinner("⚡ Translating cheat sheet to Hinglish..."):
                        translated = translate_to_hinglish(short_notes_content)
                        if translated and translated.strip():
                            st.session_state.sn_hinglish = translated
                            st.rerun()
                        else:
                            st.error("Generation failed due to API timeout or rate limit. Please retry.")
        with col_sn2:
            sn_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            sn_pdf = generate_topper_pdf(
                title=f"Revision Sheet: {st.session_state.get('sn_name', 'Revision')}",
                content=short_notes_content,
                feature_name="Short Notes"
            )
            st.download_button(
                "📥 Download PDF",
                data=sn_pdf,
                file_name=f"TopperGPT_ShortNotes_{sn_ts}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        if st.session_state.get("sn_hinglish"):
            with st.expander("🗣️ View Hinglish Cheat Sheet Translation", expanded=True):
                st.markdown(clean_output_text(st.session_state.sn_hinglish))

# ==================================================
# --- 4. FEATURE: TOPIC RESEARCH (ZERO-FAIL JSON PARSING) ---
# ==================================================
elif nav_selection == "🔍 Topic Research":
    st.markdown("""
        <div class="topper-card">
            <h3 style="margin-top:0; color:#58c1c8;">Streamlined Concept Breakdown</h3>
            <p style="color:var(--text-muted, #94a3b8); font-size:14px; margin:0;">
                Get university-standard definitions, technical breakdowns, and working principles in 3 clean cards.
            </p>
        </div>
    """, unsafe_allow_html=True)

    topic_q = st.text_input("Enter Concept to Research:", placeholder="e.g. Transformer, BJT Biasing, Process Scheduling, Op-Amp", key="res_q_input")

    if st.button("Execute Deep Research ⚡", use_container_width=True):
        if not topic_q.strip():
            st.warning("Please enter a concept name.")
        else:
            with st.spinner(f"⚡ Conducting deep topic research on '{topic_q}'..."):
                res_prompt = f"""Be extremely direct, concise, and structured. No fluff, no introductory chatter, no conversational filler.
You are a Senior Mumbai University Engineering Professor.
Target Topic: "{topic_q}"
Language: Strictly Professional English.

MATHEMATICAL NOTATION RULES:
- Wrap ALL inline variables/formulas in single dollar signs (e.g., $V_p / V_s$, $R_{{eq}}$, $I_1$).
- Wrap ALL block equations in double dollar signs ($$...$$).
- NEVER use \\displaystyle or bare curly braces {{...}} without dollar signs.

Return ONLY a valid JSON object. Do NOT include any intro, draft thoughts, reasoning, or backticks around the json.
JSON structure must be exactly:
{{
  "definition": "Official 2-mark university textbook definition with examiner keywords.",
  "breakdown": "Technical breakdown covering architecture, circuit configurations, and key governing formulas written in clean LaTeX ($...$ or $$...$$).",
  "working_principle": "Step-by-step physical or operational working principle with clear cause-and-effect flow."
}}
"""
                try:
                    r_res = generate_ai_response(res_prompt, max_toks=700, temperature=0.2)
                    parsed_data = parse_topic_research_json(r_res)
                    st.session_state.topic_res_json = parsed_data
                    st.session_state.topic_res_name = topic_q
                    st.rerun()
                except Exception:
                    st.error("Generation failed due to API timeout or rate limit. Please retry.")

    if "topic_res_json" in st.session_state and st.session_state.topic_res_json:
        t_data = st.session_state.topic_res_json
        t_name = st.session_state.topic_res_name

        st.markdown(f"### 📘 Technical Report: **{t_name.upper()}**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.container(border=True):
                st.markdown("""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <h4 style="color:#58c1c8; margin:0; font-size:16px; font-weight:700;">1. Official Definition</h4>
                        <span class="research-card-tag research-tag-def">2-MARK STANDARD</span>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(clean_output_text(t_data.get("definition", "Details unavailable.")))
                
        with col2:
            with st.container(border=True):
                st.markdown("""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <h4 style="color:#00F2FE; margin:0; font-size:16px; font-weight:700;">2. Technical Breakdown</h4>
                        <span class="research-card-tag research-tag-tech">ARCHITECTURE & FORMULAS</span>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(clean_output_text(t_data.get("breakdown", "Details unavailable.")))
                
        with col3:
            with st.container(border=True):
                st.markdown("""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <h4 style="color:#22c55e; margin:0; font-size:16px; font-weight:700;">3. Working Principle</h4>
                        <span class="research-card-tag research-tag-work">OPERATIONAL FLOW</span>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(clean_output_text(t_data.get("working_principle", "Details unavailable.")))

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        col_res1, col_res2 = st.columns([1, 1])
        with col_res1:
            res_content = format_topic_research_for_pdf(t_name, t_data)
            res_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            res_pdf = generate_topper_pdf(
                title=f"Technical Report: {t_name}",
                content=res_content,
                feature_name="Topic Research"
            )
            st.download_button(
                "📥 Download PDF",
                data=res_pdf,
                file_name=f"TopperGPT_TopicResearch_{res_ts}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col_res2:
            if st.button("🗑️ Clear Research", use_container_width=True):
                del st.session_state.topic_res_json
                st.rerun()