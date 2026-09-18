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

# --- 2. CSS STYLING OVERHAUL (DESKTOP & MOBILE RESPONSIVE) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700;800&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', 'Plus Jakarta Sans', -apple-system, sans-serif !important;
}

/* Custom sleek scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #030303;
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
    color: #ffffff !important;
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

/* Main block container max-width & padding for optimal reading ergonomics */
.main .block-container, div[data-testid="stMainBlockContainer"] {
    max-width: 1000px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding-top: 2rem !important;
    padding-bottom: 110px !important;
}

/* Header customization */
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* ================================================================ */
/* 1. SIDEBAR & FEATURE NAVIGATION (DESKTOP & MOBILE)               */
/* ================================================================ */
[data-testid="stSidebar"] {
    background-color: #060709 !important;
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
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    margin: 0 0 6px 0 !important;
    cursor: pointer !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(88, 193, 200, 0.08) !important;
    border-color: rgba(88, 193, 200, 0.4) !important;
    transform: translateY(-1px) translateX(3px) !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4), 0 0 12px rgba(88, 193, 200, 0.15) !important;
}

/* Completely Hide Streamlit default radio-button circles (input[type="radio"]) */
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

/* Sidebar Item Text: 1.1rem, bold and clean */
div[data-testid="stSidebar"] div[role="radiogroup"] label div p,
div[data-testid="stSidebar"] div[role="radiogroup"] label p,
div[data-testid="stSidebar"] div[role="radiogroup"] label span {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #cbd5e1 !important;
    letter-spacing: 0.2px !important;
    line-height: 1.4 !important;
    margin: 0 !important;
    padding: 0 !important;
    transition: color 0.2s ease !important;
    width: 100% !important;
}

/* Active State: Glowing Accent Outline (#58C1C8) & Dark Glassmorphism */
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
    font-size: 1.1rem !important;
    text-shadow: 0 0 12px rgba(88, 193, 200, 0.5) !important;
}

/* Status Card in Sidebar */
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

/* Glassmorphic Dark Cards & Topic Research UI Cards */
.topper-card {
    background: #08090d;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
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
    background-color: #08090d !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stChatMessage"]:hover {
    border-color: rgba(88, 193, 200, 0.2) !important;
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

/* ================================================================ */
/* 2. OPTIMIZE DESKTOP WORKSPACE (@media min-width: 769px)          */
/* ================================================================ */
@media (min-width: 769px) {
    /* Sidebar structural width 300px minimum */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"] {
        min-width: 300px !important;
        width: 300px !important;
        max-width: 340px !important;
    }

    /* Central chat workspace: center-aligned, 85% width, max-width 1000px */
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

    /* Bottom input container centered to 85% (max-width 1000px) */
    div[data-testid="stBottomBlockContainer"] {
        width: 85% !important;
        max-width: 1000px !important;
        margin: 0 auto !important;
        padding-bottom: 22px !important;
        padding-top: 8px !important;
    }
}

/* ================================================================ */
/* 3. CHAT INPUT BAR (SLEEK 1PX GLOW BORDER & FLOATING THEME)       */
/* ================================================================ */
/* Clear default Streamlit bottom bar gradient */
div[data-testid="stBottom"], .stBottom {
    background: transparent !important;
    background-color: transparent !important;
    z-index: 999 !important;
}

div[data-testid="stBottomBlockContainer"] {
    background: transparent !important;
    padding-bottom: 22px !important;
    padding-top: 8px !important;
}

div[data-testid="stChatInput"] {
    background-color: transparent !important;
    margin: 8px 0 12px 0 !important;
}

/* Floating Sleek Dark Box with 1px glow border rgba(88, 193, 200, 0.4) and 16px radius */
div[data-testid="stChatInput"] > div {
    background: rgba(8, 9, 13, 0.94) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(88, 193, 200, 0.4) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.7), 0 0 16px rgba(88, 193, 200, 0.12) !important;
    padding: 6px 12px !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stChatInput"] > div:focus-within {
    border-color: #58C1C8 !important;
    box-shadow: 0 10px 36px rgba(0, 0, 0, 0.8), 0 0 24px rgba(88, 193, 200, 0.45) !important;
    transform: translateY(-1px);
}

/* Textarea inside Floating Chat Input */
div[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: #f1f5f9 !important;
    font-family: inherit !important;
    font-size: 15px !important;
    line-height: 1.5 !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 8px 10px !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: #64748b !important;
    font-size: 14.5px !important;
    font-weight: 500 !important;
    letter-spacing: 0.2px !important;
}

/* Sharp, Centered Send Button with Cyber-Cyan Accent */
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
    color: #475569 !important;
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

/* ================================================================ */
/* 4. COMPLETE MOBILE RESPONSIVENESS (@media max-width: 768px)      */
/* ================================================================ */
/* Sleek Hamburger Drawer Button */
[data-testid="collapsedControl"] {
    color: #58c1c8 !important;
    background: rgba(8, 9, 13, 0.92) !important;
    border: 1.5px solid rgba(88, 193, 200, 0.4) !important;
    border-radius: 10px !important;
    padding: 7px 9px !important;
    top: 12px !important;
    left: 12px !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.6), 0 0 12px rgba(88, 193, 200, 0.25) !important;
    z-index: 999999 !important;
    transition: all 0.2s ease !important;
}
[data-testid="collapsedControl"]:hover {
    border-color: #58C1C8 !important;
    box-shadow: 0 4px 22px rgba(0, 0, 0, 0.7), 0 0 18px rgba(88, 193, 200, 0.5) !important;
}
[data-testid="collapsedControl"] svg {
    stroke: #58C1C8 !important;
    fill: #58C1C8 !important;
}

@media (max-width: 768px) {
    /* Top Header Navbar Flex & Clean Stacking on Mobile */
    .navbar {
        padding: 0.65rem 0 !important;
    }
    .nav-wrapper {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        flex-wrap: wrap !important;
        gap: 0.5rem !important;
        width: 100% !important;
    }
    .nav-links {
        display: none !important;
    }
    .brand {
        gap: 0.5rem !important;
    }
    .brand-title {
        font-size: 1.15rem !important;
    }
    .brand-icon {
        width: 32px !important;
        height: 32px !important;
        font-size: 16px !important;
    }
    .nav-actions {
        display: flex !important;
        align-items: center !important;
        gap: 0.4rem !important;
        flex-wrap: nowrap !important;
    }
    .nav-actions .btn {
        padding: 0.45rem 0.85rem !important;
        font-size: 0.78rem !important;
        white-space: nowrap !important;
    }

    /* Mobile Sidebar Slide-Over Drawer */
    [data-testid="stSidebar"] {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        height: 100vh !important;
        width: 84vw !important;
        max-width: 320px !important;
        min-width: unset !important;
        background-color: rgba(6, 7, 9, 0.98) !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border-right: 1px solid rgba(88, 193, 200, 0.25) !important;
        box-shadow: 8px 0 36px rgba(0, 0, 0, 0.9) !important;
        z-index: 1000000 !important;
        overflow-y: auto !important;
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        transform: translateX(-100%) !important;
        box-shadow: none !important;
    }

    /* Main Container: Full Width, Responsive Padding */
    .main .block-container,
    div[data-testid="stMainBlockContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        padding-top: 4rem !important; /* space for fixed hamburger button */
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
        padding-bottom: 120px !important; /* ensures messages scroll cleanly above input */
        box-sizing: border-box !important;
    }

    /* Responsive Header & Streak Badge */
    h1 {
        font-size: 22px !important;
        line-height: 1.25 !important;
        margin: 0 0 10px 0 !important;
    }

    .streak-badge {
        float: none !important;
        display: inline-flex !important;
        font-size: 12px !important;
        padding: 4px 10px !important;
        margin-top: 4px !important;
        margin-bottom: 14px !important;
    }

    /* Prompt Starter Quick Pills: wrap cleanly horizontally */
    .starter-chip-container {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        width: 100% !important;
        margin-bottom: 12px !important;
    }
    .starter-chip {
        font-size: 12px !important;
        padding: 6px 12px !important;
        white-space: nowrap !important;
        flex-shrink: 0 !important;
    }

    /* Cards & Containers on Small Screens */
    .topper-card {
        padding: 16px 14px !important;
        margin-bottom: 14px !important;
        border-radius: 12px !important;
    }
    .topper-card h3 {
        font-size: 17px !important;
    }

    /* Chat Messages on Mobile */
    [data-testid="stChatMessage"] {
        padding: 12px 14px !important;
        margin-bottom: 10px !important;
        border-radius: 12px !important;
    }

    /* Pinned Bottom Chat Bar Container for Mobile */
    div[data-testid="stBottom"], .stBottom {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100% !important;
        background: linear-gradient(180deg, rgba(3, 3, 3, 0) 0%, rgba(3, 3, 3, 0.94) 30%, #030303 100%) !important;
        padding: 8px 10px 14px 10px !important;
        z-index: 9999 !important;
    }

    div[data-testid="stBottomBlockContainer"] {
        padding: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    div[data-testid="stChatInput"] {
        width: 100% !important;
        margin: 4px 0 !important;
    }

    div[data-testid="stChatInput"] > div {
        border-radius: 14px !important;
        padding: 4px 8px !important;
        background: rgba(8, 9, 13, 0.96) !important;
    }

    div[data-testid="stChatInput"] textarea {
        font-size: 14px !important;
        padding: 6px 8px !important;
    }

    div[data-testid="stChatInput"] button {
        width: 34px !important;
        height: 34px !important;
        min-width: 34px !important;
        min-height: 34px !important;
        border-radius: 10px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Default: If not logged in and not requesting login page, render landing page
if st.session_state.get("user_data") is None and qp_page != "login":
    render_landing_page()
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

    # 4. Normalize multiple blank lines and whitespace
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
        if not curr:
            curr = dl
        else:
            cells = clean_split_pipe_line(curr)
            # If current line already has target_cols and next line starts a new row, finish current
            if len(cells) >= target_cols and (curr.endswith("|") or dl.startswith("|")):
                stitched_lines.append(curr)
                curr = dl
            else:
                # Merge unescaped line break into current row
                curr += " " + dl
    if curr and not is_markdown_table_separator(curr):
        stitched_lines.append(curr)

    parsed_rows = [headers]
    for sl in stitched_lines:
        if is_markdown_table_separator(sl):
            continue
        cells = clean_split_pipe_line(sl)
        if not cells or not any(cells):
            continue

        # Merge or auto-pad so every row has exact target_cols
        if len(cells) < target_cols:
            cells = cells + [""] * (target_cols - len(cells))
        elif len(cells) > target_cols:
            cells = cells[:target_cols - 1] + [" | ".join(cells[target_cols - 1:])]
        parsed_rows.append(cells)

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

                # 1. Native FPDF Table Rendering for Markdown Tables
                if not in_code_block and "|" in trimmed and i + 1 < n and is_markdown_table_separator(lines[i + 1]):
                    table_lines = [trimmed, lines[i + 1].strip()]
                    i += 2
                    while i < n and "|" in lines[i] and lines[i].strip():
                        table_lines.append(lines[i].strip())
                        i += 1

                    parsed_table = parse_markdown_table("\n".join(table_lines))
                    if parsed_table and len(parsed_table) >= 2:
                        self.ln(2)
                        self.set_x(self.l_margin)
                        col_count = len(parsed_table[0])
                        col_widths = get_proportional_col_widths(col_count)

                        headings_style = None
                        if FontFace is not None:
                            try:
                                headings_style = FontFace(
                                    family=self.font_family_name,
                                    emphasis="B",
                                    color=(255, 255, 255),
                                    fill_color=(11, 15, 25)  # #0B0F19
                                )
                            except Exception:
                                headings_style = None

                        self.set_font(self.font_family_name, size=8.5)
                        self.set_text_color(30, 41, 59)

                        try:
                            with self.table(
                                borders_layout="ALL",
                                cell_fill_color=(245, 247, 250),
                                cell_fill_mode="EVEN_ROWS",
                                line_height=7,
                                col_widths=col_widths,
                                headings_style=headings_style,
                                first_row_as_headings=True
                            ) as table:
                                for row in parsed_table:
                                    # Never render separator lines as data rows
                                    if is_markdown_table_separator(" | ".join(str(c) for c in row)):
                                        continue

                                    # Auto-pad or merge to guarantee exact uniform column count matching col_widths
                                    if len(row) < col_count:
                                        row = list(row) + [""] * (col_count - len(row))
                                    elif len(row) > col_count:
                                        row = list(row[:col_count - 1]) + [" | ".join(str(x) for x in row[col_count - 1:])]

                                    clean_row = []
                                    for cell in row:
                                        c = str(cell).strip()
                                        c = format_math_for_pdf(c)
                                        c = sanitize_pdf_text(c, is_unicode=self.is_unicode)
                                        c = re.sub(r'\*\*(.*?)\*\*', r'\1', c)
                                        c = re.sub(r'(?<![a-zA-Z0-9])\*(.*?)\*(?![a-zA-Z0-9])', r'\1', c)
                                        c = re.sub(r'[`#]', '', c).strip()
                                        clean_row.append(c)
                                    table.row(clean_row)
                            self.ln(3)
                            self.set_x(self.l_margin)
                            continue
                        except Exception as e:
                            # Graceful fallback for unexpected table render issues
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

# --- 7. BACKEND AI ENGINE (GROQ + GEMINI + OPENROUTER) ---
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
                            return clean_output_text(res.json()["choices"][0]["message"]["content"].strip())
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
                    return clean_output_text(res.json()['candidates'][0]['content']['parts'][0]['text'].strip())
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
                        return clean_output_text(choices[0]["message"]["content"].strip())
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
            return clean_output_text("\n\n".join(matched[:2]))
    except Exception:
        pass

    return clean_output_text("### 📌 Core Concept\nWe are currently analyzing this syllabus question with high-yield university exam patterns. Please refresh or retry in a moment.")

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
    prompt = f"""Translate and simplify the following engineering explanation into clear, friendly Hinglish (Hindi written in English alphabets) so that an Indian student can understand it effortlessly. Keep all equations and mathematical variables intact.

    MATHEMATICAL NOTATION INSTRUCTIONS:
    - Wrap ALL inline math variables/formulas in single dollar signs (e.g., $V_p / V_s$, $R_{{eq}}$).
    - Wrap ALL standalone or display equations in double dollar signs ($$...$$).
    - Never use \\displaystyle or wrap equations in raw curly braces {{...}} without dollar signs.

    Text:
    {text_content}"""
    return generate_ai_response(prompt, max_toks=1000)

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

    # Auto-process pending query from Landing Page search
    if "pending_query" in st.session_state and st.session_state.pending_query:
        init_q = st.session_state.pop("pending_query")
        st.session_state.tutor_messages.append({"role": "user", "content": init_q, "hinglish": None})
        with st.spinner("Analyzing syllabus and generating exam-focused solution..."):
            tutor_prompt = f"""
            You are TopperGPT's Senior Academic Evaluator for Mumbai University Engineering (C-Scheme).
            Respond exclusively in professional, clear, exam-oriented English.

            Student Query: "{init_q}"

            MATHEMATICAL NOTATION RULES:
            - Wrap ALL inline variables and formulas in single dollar signs (e.g., $V_p / V_s$, $R_{{eq}}$, $I_1$).
            - Wrap ALL standalone or block equations in double dollar signs ($$...$$).
            - NEVER use \\displaystyle or wrap formulas in bare curly braces {{...}} without dollar signs.

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
            st.markdown(clean_output_text(msg["content"]))
            if msg["role"] == "assistant" and idx > 0:
                if msg.get("hinglish"):
                    with st.expander("🗣️ View Hinglish Explanation"):
                        st.markdown(clean_output_text(msg["hinglish"]))
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
            st.markdown(clean_output_text(user_query))

        tutor_prompt = f"""
        You are TopperGPT's Senior Academic Evaluator for Mumbai University Engineering (C-Scheme).
        Respond exclusively in professional, clear, exam-oriented English.

        Student Query: "{user_query}"

        MATHEMATICAL NOTATION RULES:
        - Wrap ALL inline variables and formulas in single dollar signs (e.g., $V_p / V_s$, $R_{{eq}}$, $I_1$).
        - Wrap ALL standalone or block equations in double dollar signs ($$...$$).
        - NEVER use \\displaystyle or wrap formulas in bare curly braces {{...}} without dollar signs.

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
                    st.markdown(clean_output_text(ai_reply))
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
        st.markdown(clean_output_text(st.session_state.pred_result))

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            if not st.session_state.get("pred_hinglish"):
                if st.button("🗣️ Translate to Hinglish", key="trans_pred", use_container_width=True):
                    with st.spinner("Translating blueprint to Hinglish..."):
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

                MATHEMATICAL NOTATION RULES:
                - Do not use markdown tables for equations. Use clean Markdown LaTeX ($$ display blocks).
                - Wrap ALL inline variables and formulas in single dollar signs (e.g., $V_p / V_s$, $R_{{eq}}$, $I_1$).
                - Wrap ALL standalone or block equations in double dollar signs ($$...$$).
                - NEVER use \\displaystyle or wrap formulas in bare curly braces {{...}} without dollar signs.

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
                    sn_res_clean = (sn_res or "").strip()
                    # Validate: non-empty string, minimum length, not rate limit or timeout notice
                    is_valid = (
                        bool(sn_res_clean)
                        and len(sn_res_clean) >= 50
                        and "Please refresh or retry" not in sn_res_clean
                        and "rate limit" not in sn_res_clean.lower()
                    )
                    if not is_valid:
                        st.error("Generation failed due to API timeout or rate limit. Please retry.")
                    else:
                        st.session_state.short_notes_data = sn_res_clean
                        st.session_state.sn_data = sn_res_clean
                        st.session_state.sn_name = sn_topic
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
                    with st.spinner("Translating cheat sheet to Hinglish..."):
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
                    r_res = generate_ai_response(res_prompt, max_toks=1200)
                    parsed_data = parse_topic_research_json(r_res)
                    st.session_state.topic_res_json = parsed_data
                    st.session_state.topic_res_name = topic_q
                    st.rerun()
                except Exception as e:
                    st.session_state.topic_res_json = parse_topic_research_json(str(e))
                    st.session_state.topic_res_name = topic_q
                    st.rerun()

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