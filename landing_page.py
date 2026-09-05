import streamlit as st
import streamlit.components.v1 as components

def render_landing_page():
    # 1. Clean Streamlit Container Overrides
    st.markdown("""
        <style>
        header[data-testid="stHeader"] { display: none !important; }
        [data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }
        footer { display: none !important; }
        #MainMenu { display: none !important; }
        .stDeployButton { display: none !important; }

        .main .block-container,
        [data-testid="stMainBlockContainer"] {
            padding: 0 !important;
            max-width: 100% !important;
            margin: 0 !important;
            width: 100% !important;
        }

        .stApp {
            background-color: #030303 !important;
        }

        iframe {
            width: 100% !important;
            border: none !important;
            display: block !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. Complete HTML Document for IFrame Component (Zero Markdown Parsing Risk)
    landing_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TopperGPT - AI Academic Workspace</title>
  
  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
  
  <style>
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    :root {
        --bg-dark: #030303;
        --bg-card: #080808;
        --bg-card-hover: #0d0d0d;
        --bg-input: #0a0a0a;
        --text-main: #ffffff;
        --text-muted: #888888;
        --text-dim: #555555;
        --accent: rgb(88, 193, 200);
        --accent-hover: rgb(110, 210, 217);
        --accent-glow: rgba(88, 193, 200, 0.35);
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-highlight: rgba(88, 193, 200, 0.3);
        --font-display: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'Space Mono', monospace;
    }

    body {
        background-color: var(--bg-dark);
        color: var(--text-main);
        font-family: var(--font-display);
        line-height: 1.5;
        overflow-x: hidden;
        position: relative;
        width: 100%;
        min-height: 100vh;
    }

    /* Grid Background Effect */
    body::before {
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: 
            radial-gradient(circle at 50% 10%, rgba(88, 193, 200, 0.12) 0%, transparent 65%),
            linear-gradient(to right, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
        background-size: 100% 100%, 36px 36px, 36px 36px;
        pointer-events: none;
        z-index: 0;
    }

    .landing-content {
        position: relative;
        z-index: 1;
        width: 100%;
    }

    .container {
        max-width: 1240px;
        margin: 0 auto;
        padding: 0 1.5rem;
    }

    /* Navigation Bar */
    .navbar {
        position: sticky;
        top: 0;
        z-index: 100;
        background: rgba(3, 3, 3, 0.88);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border-bottom: 1px solid var(--border-subtle);
        padding: 0.9rem 0;
        width: 100%;
    }

    .nav-wrapper {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        text-decoration: none;
    }

    .brand-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: var(--accent);
        box-shadow: 0 0 18px var(--accent-glow);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: #000;
        font-size: 18px;
    }

    .brand-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #fff;
        letter-spacing: -0.02em;
    }

    .brand-title span {
        color: var(--accent);
    }

    .nav-links {
        display: flex;
        align-items: center;
        gap: 1rem;
        list-style: none;
    }

    .nav-link {
        color: var(--text-muted);
        text-decoration: none;
        font-size: 0.875rem;
        font-weight: 500;
        padding: 0.4rem 0.85rem;
        border-radius: 9999px;
        transition: all 0.2s ease;
    }

    .nav-link:hover,
    .nav-link.active {
        color: #ffffff;
        background: rgb(36, 118, 124);
        border: 1px solid var(--border-highlight);
        font-family: var(--font-mono);
        font-size: 0.8rem;
    }

    .nav-actions {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.65rem 1.5rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 700;
        cursor: pointer;
        text-decoration: none;
        transition: all 0.2s ease;
        border: none;
        font-family: var(--font-mono);
    }

    .btn-secondary {
        background: rgba(255, 255, 255, 0.04);
        color: var(--text-main);
        border: 1px solid var(--border-subtle);
        font-family: var(--font-display);
    }

    .btn-secondary:hover {
        border-color: var(--accent);
        color: var(--accent);
        background: rgba(88, 193, 200, 0.08);
    }

    .btn-primary {
        background: var(--accent);
        color: #050505;
        box-shadow: 0 0 20px var(--accent-glow);
    }

    .btn-primary:hover {
        background: var(--accent-hover);
        transform: translateY(-2px);
        box-shadow: 0 0 25px rgb(88, 193, 200);
    }

    /* Hero Section 1 */
    .hero-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 3.5rem;
        align-items: center;
        padding: 4rem 0 3rem;
    }

    @media (min-width: 1024px) {
        .hero-grid {
            grid-template-columns: 1.1fr 1fr;
            padding: 5rem 0 4rem;
        }
    }

    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 1rem;
        border-radius: 9999px;
        background: rgba(88, 193, 200, 0.1);
        border: 1px solid var(--border-highlight);
        color: var(--accent);
        font-size: 0.75rem;
        font-weight: 700;
        font-family: var(--font-mono);
        margin-bottom: 1.5rem;
        box-shadow: 0 0 15px rgba(88, 193, 200, 0.15);
    }

    .hero-title {
        font-size: clamp(2.4rem, 4.5vw, 3.8rem);
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.12;
        margin-bottom: 1.25rem;
    }

    .hero-title .highlight {
        color: var(--accent);
        background: linear-gradient(135deg, #58c1c8 0%, #22d3ee 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-desc {
        font-size: 1.1rem;
        color: var(--text-muted);
        line-height: 1.65;
        margin-bottom: 2rem;
        max-width: 540px;
    }

    .hero-actions {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2.5rem;
    }

    .features-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.25rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--border-subtle);
    }

    .feature-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .feature-icon {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 0.75rem;
        background: rgba(88, 193, 200, 0.1);
        border: 1px solid var(--border-highlight);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        flex-shrink: 0;
    }

    .feature-text h4 {
        font-size: 0.95rem;
        font-weight: 700;
        color: #fff;
    }

    .feature-text p {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    /* Right Column: Live Interactive Dashboard Mockup */
    .dashboard-wrapper {
        position: relative;
    }

    .dashboard-card {
        background: linear-gradient(145deg, #0d0d0d, #080808);
        border: 1px solid var(--border-subtle);
        border-radius: 1.75rem;
        padding: 1.75rem;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(30, 94, 98, 0.4);
        backdrop-filter: blur(12px);
        position: relative;
        z-index: 10;
        overflow: hidden;
    }

    .dash-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 1.15rem;
        border-bottom: 1px solid var(--border-subtle);
        margin-bottom: 1.25rem;
    }

    .dash-brand {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-weight: 700;
        font-size: 1.05rem;
        color: #fff;
    }

    .dash-brand span {
        color: var(--accent);
        font-family: var(--font-mono);
    }

    .dash-status {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        background: rgba(31, 85, 89, 0.6);
        border: 1px solid var(--border-highlight);
        color: var(--accent);
        font-size: 0.75rem;
        font-family: var(--font-mono);
        font-weight: 600;
    }

    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 8px var(--accent);
        animation: pulseDot 2s infinite;
    }

    @keyframes pulseDot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }

    .dash-greeting {
        margin-bottom: 1.25rem;
    }

    .dash-greeting h3 {
        font-size: 1.35rem;
        font-weight: 700;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .dash-greeting p {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
    }

    /* Live Search Form */
    .dash-search-form {
        position: relative;
        margin-bottom: 1rem;
    }

    .dash-input-container {
        height: 3.5rem;
        background: var(--bg-input);
        border: 1px solid var(--border-subtle);
        border-radius: 9999px;
        display: flex;
        align-items: center;
        padding: 0.35rem 0.5rem 0.35rem 1.25rem;
        transition: all 0.25s ease;
    }

    .dash-input-container:focus-within {
        border-color: var(--accent);
        box-shadow: 0 0 25px var(--accent-glow);
    }

    .dash-input {
        flex: 1;
        background: transparent;
        border: none;
        color: #fff;
        font-size: 0.9rem;
        font-family: var(--font-display);
        outline: none;
    }

    .dash-input::placeholder {
        color: var(--text-dim);
    }

    .dash-submit-btn {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 50%;
        background: var(--accent);
        color: #050505;
        border: none;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        font-weight: 800;
        cursor: pointer;
        transition: transform 0.2s, background 0.2s;
    }

    .dash-submit-btn:hover {
        transform: scale(1.08);
        background: var(--accent-hover);
    }

    /* Quick Action Prompt Chips */
    .quick-chips {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.5rem;
        margin-bottom: 1.25rem;
    }

    .chip-btn {
        padding: 0.55rem 0.4rem;
        border-radius: 0.75rem;
        background: #080808;
        border: 1px solid var(--border-subtle);
        color: var(--text-muted);
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
        transition: all 0.2s ease;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
    }

    .chip-btn:hover {
        border-color: var(--accent);
        color: var(--accent);
        background: rgba(88, 193, 200, 0.1);
    }

    /* 4-Tool Quick Grid */
    .tool-quad-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.65rem;
        margin-bottom: 1rem;
    }

    .quad-item {
        background: #080808;
        border: 1px solid var(--border-subtle);
        border-radius: 1rem;
        padding: 0.85rem 0.65rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        cursor: pointer;
        text-decoration: none;
        color: inherit;
        transition: all 0.25s ease;
    }

    .quad-item:hover {
        border-color: var(--border-highlight);
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(88, 193, 200, 0.15);
    }

    .quad-icon {
        font-size: 1.35rem;
        margin-bottom: 0.4rem;
    }

    .quad-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #fff;
    }

    .quad-desc {
        font-size: 0.65rem;
        color: var(--text-muted);
        margin: 0.2rem 0 0.5rem;
        line-height: 1.3;
    }

    .quad-action {
        font-size: 0.7rem;
        font-family: var(--font-mono);
        font-weight: 700;
        color: var(--accent);
    }

    /* Live Output Response Box */
    .ai-response-box {
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 1rem;
        background: rgb(7, 87, 93);
        border: 1px solid rgb(88, 193, 200);
        font-size: 0.85rem;
        line-height: 1.6;
        display: none;
        animation: fadeIn 0.3s ease;
    }

    .ai-response-box.visible {
        display: block;
    }

    .ai-response-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.5rem;
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--accent);
        font-weight: 700;
    }

    /* Floating Metric Badges */
    .floating-badge-progress {
        position: absolute;
        top: -1.5rem;
        right: -1.5rem;
        width: 11rem;
        background: rgba(13, 13, 13, 0.95);
        border: 1px solid var(--border-subtle);
        border-radius: 1.25rem;
        padding: 0.85rem;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        z-index: 20;
        display: none;
    }

    .radial-score {
        width: 3.5rem;
        height: 3.5rem;
        border-radius: 50%;
        border: 3px solid var(--accent);
        background: rgb(45, 117, 123);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0.4rem auto;
        font-family: var(--font-mono);
        font-weight: 800;
        color: var(--accent);
        font-size: 1rem;
        box-shadow: 0 0 15px var(--accent-glow);
    }

    .floating-badge-tutor {
        position: absolute;
        bottom: -1.5rem;
        left: -1.75rem;
        background: rgba(13, 13, 13, 0.95);
        border: 1px solid var(--border-subtle);
        border-radius: 1.25rem;
        padding: 0.75rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        z-index: 20;
        display: none;
    }

    .floating-badge-trophy {
        position: absolute;
        bottom: -1rem;
        right: -1rem;
        background: rgba(13, 13, 13, 0.95);
        border: 1px solid var(--border-subtle);
        border-radius: 1rem;
        padding: 0.6rem 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.8);
        z-index: 20;
        display: none;
        transform: rotate(-3deg);
    }

    @media (min-width: 1200px) {
        .floating-badge-progress,
        .floating-badge-tutor,
        .floating-badge-trophy {
            display: flex;
        }
        .floating-badge-progress {
            display: block;
        }
    }

    /* Hero Section 2 */
    .hero-center {
        padding: 5rem 0 3rem;
        text-align: center;
    }

    .badge-center {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 1.2rem;
        border-radius: 9999px;
        background: rgb(88, 193, 200);
        border: 1px solid var(--border-highlight);
        color: #000;
        font-size: 0.75rem;
        font-weight: 700;
        font-family: var(--font-mono);
        margin-bottom: 1.5rem;
        box-shadow: 0 0 25px rgba(88, 193, 200, 0.4);
    }

    .hero-center-title {
        font-size: clamp(2.2rem, 5vw, 4rem);
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin-bottom: 1.25rem;
    }

    .gradient-text {
        color: var(--accent);
        background: linear-gradient(135deg, #58c1c8 0%, #22d3ee 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-center-desc {
        font-size: 1.125rem;
        color: var(--text-muted);
        max-width: 680px;
        margin: 0 auto 2.5rem;
        line-height: 1.6;
    }

    /* Search Bar */
    .search-box {
        max-width: 640px;
        margin: 0 auto 3rem;
        background: var(--bg-input);
        border: 1px solid var(--border-subtle);
        border-radius: 1.25rem;
        padding: 0.5rem 0.75rem 0.5rem 1.25rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transition: all 0.2s ease;
    }

    .search-box:focus-within {
        border-color: var(--accent);
        box-shadow: 0 0 25px var(--accent-glow);
    }

    .search-box input {
        flex: 1;
        background: transparent;
        border: none;
        color: #fff;
        font-size: 0.95rem;
        font-family: var(--font-display);
        outline: none;
    }

    .search-box input::placeholder {
        color: var(--text-dim);
    }

    /* Tools Grid */
    .section-header {
        text-align: center;
        margin: 4rem 0 2.5rem;
    }

    .section-title {
        font-size: 2.25rem;
        font-weight: 800;
        letter-spacing: -0.02em;
    }

    .tools-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 1.5rem;
        margin-bottom: 5rem;
    }

    .tool-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 1.5rem;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        text-decoration: none;
        color: inherit;
        position: relative;
        overflow: hidden;
    }

    .tool-card:hover {
        background: var(--bg-card-hover);
        border-color: var(--border-highlight);
        transform: translateY(-6px);
        box-shadow: 0 15px 35px rgba(88, 193, 200, 0.25);
    }

    .tool-card-icon {
        width: 54px;
        height: 54px;
        border-radius: 1rem;
        background: rgb(34, 139, 147);
        border: 1px solid rgb(88, 193, 200);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.75rem;
        color: var(--accent);
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease;
    }

    .tool-card:hover .tool-card-icon {
        transform: scale(1.1);
        border-color: var(--accent);
    }

    .tool-card-badge {
        position: absolute;
        top: 1.75rem;
        right: 1.75rem;
        font-size: 0.75rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        background: rgb(88, 193, 200);
        border: 1px solid var(--border-highlight);
        color: black;
        font-family: var(--font-mono);
        font-weight: 700;
    }

    .tool-card h3 {
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #fff;
        transition: color 0.2s ease;
    }

    .tool-card:hover h3 {
        color: var(--accent);
    }

    .tool-card p {
        font-size: 0.875rem;
        color: var(--text-muted);
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }

    .tool-card-footer {
        border-top: 1px solid var(--border-subtle);
        padding-top: 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-family: var(--font-mono);
        font-size: 0.75rem;
    }

    .tool-card-footer .category {
        color: var(--text-dim);
    }

    .tool-card-footer .action {
        color: var(--accent);
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    /* Founder Section */
    .founder-section {
        text-align: center;
        padding: 4rem 0 5rem;
        border-top: 1px solid var(--border-subtle);
    }

    .founder-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        font-family: var(--font-mono);
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
    }

    .founder-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 2rem;
    }

    .founder-title span {
        color: var(--accent);
    }

    .founder-card {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: var(--bg-card);
        border: 1px solid var(--border-highlight);
        border-radius: 9999px;
        padding: 6px;
        box-shadow: 0 0 25px rgba(88, 193, 200, 0.2);
    }

    .founder-img {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid var(--accent);
    }

    /* Footer */
    .footer {
        border-top: 1px solid var(--border-subtle);
        padding: 3rem 0 2rem;
        background: #030303;
        color: var(--text-muted);
        font-size: 0.875rem;
    }

    .footer-content {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 1.5rem;
    }

    .footer-links {
        display: flex;
        gap: 1.5rem;
        font-family: var(--font-mono);
        font-size: 0.8rem;
    }

    .footer-links a {
        color: var(--text-muted);
        text-decoration: none;
        transition: color 0.2s ease;
    }

    .footer-links a:hover {
        color: var(--accent);
    }

    @media (max-width: 768px) {
        .nav-links,
        .nav-actions .btn-secondary {
            display: none;
        }

        .features-row {
            grid-template-columns: 1fr;
        }

        .tools-grid {
            grid-template-columns: 1fr;
        }

        .quick-chips,
        .tool-quad-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
  </style>
</head>
<body>
<div class="landing-content">

  <!-- Navigation Bar -->
  <header class="navbar">
    <div class="container nav-wrapper">
      <a href="/?page=home" target="_top" class="brand">
        <div class="brand-icon">🎓</div>
        <div class="brand-title">Topper<span>GPT</span></div>
      </a>

      <ul class="nav-links">
        <li><a href="#foundation" class="nav-link active">Foundation</a></li>
        <li><a href="#research" class="nav-link">Research</a></li>
        <li><a href="#business" class="nav-link">Business</a></li>
        <li><a href="#developers" class="nav-link">Developers</a></li>
        <li><a href="#tools" class="nav-link">Products</a></li>
      </ul>

      <div class="nav-actions">
        <a href="/?page=login" target="_top" class="btn btn-secondary">Login</a>
        <a href="/?page=login" target="_top" class="btn btn-primary">Explore Tools →</a>
      </div>
    </div>
  </header>

  <!-- Hero Grid: Left Content + Right Simulated Workspace -->
  <div class="container" id="foundation">
    <div class="hero-grid">
      
      <!-- LEFT COLUMN -->
      <div class="hero-left">
        <div class="badge-pill">
          <span>✦</span>
          AI POWERED LEARNING COMPANION
        </div>

        <h1 class="hero-title">
          Study Smarter<br />
          with <span class="highlight">TopperGPT</span>
        </h1>

        <p class="hero-desc">
          Get instant explanations, personalized answers, smart notes, and practice questions — all in one place. Your AI tutor for Mumbai University engineering.
        </p>

        <div class="hero-actions">
          <a href="/?page=login" target="_top" class="btn btn-primary">
            Start Learning Free →
          </a>
          <a href="#tools" class="btn btn-secondary">
            Explore All Features
          </a>
        </div>

        <div class="features-row">
          <div class="feature-item">
            <div class="feature-icon">📚</div>
            <div class="feature-text">
              <h4>2,500+</h4>
              <p>Syllabus Chapters</p>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">⚡</div>
            <div class="feature-text">
              <h4>98% Accuracy</h4>
              <p>Verified Equations</p>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">🎯</div>
            <div class="feature-text">
              <h4>24/7 Tutor</h4>
              <p>Instant Guidance</p>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN: LIVE INTERACTIVE WORKSPACE MOCKUP -->
      <div class="dashboard-wrapper">
        <div class="dashboard-card">
          
          <!-- Header -->
          <div class="dash-header">
            <div class="dash-brand">
              <span>♢</span> TopperGPT
            </div>
            <div class="dash-status">
              <span class="status-dot"></span>
              Online
            </div>
          </div>

          <!-- Greeting -->
          <div class="dash-greeting">
            <h3>Hello, Student <span>👋</span></h3>
            <p>What would you like to learn today?</p>
          </div>

          <!-- Live Search Form -->
          <form class="dash-search-form" id="studyForm" onsubmit="handleStudySubmit(event)">
            <div class="dash-input-container">
              <span style="color: var(--accent); margin-right: 0.5rem; font-family: var(--font-mono);">✧</span>
              <input
                type="text"
                id="studyInput"
                class="dash-input"
                placeholder="Ask anything (e.g. Newton's 3rd Law, Calculus, DNA)..."
                autocomplete="off"
              />
              <button type="submit" class="dash-submit-btn" title="Submit Question">↑</button>
            </div>
          </form>

          <!-- Quick Action Buttons -->
          <div class="quick-chips">
            <button type="button" class="chip-btn" onclick="setQuery('💡 Explain', 'Explain the mechanism of Photosynthesis and cellular energy balance.')">💡 Explain</button>
            <button type="button" class="chip-btn" onclick="setQuery('📄 Summarize', 'Summarize key laws of Thermodynamics in high-yield bullet points.')">📄 Summarize</button>
            <button type="button" class="chip-btn" onclick="setQuery('🎯 Practice', 'Give me 3 practice problems on Calculus Integration with step-by-step solutions.')">🎯 Practice</button>
            <button type="button" class="chip-btn" onclick="setQuery('📖 Study', 'Generate a 15-minute quick study roadmap for Quantum Physics basics.')">📖 Study</button>
          </div>

          <!-- 4-Tool Quad Grid -->
          <div class="tool-quad-grid">
            <a href="/?page=login&query=Study+GPT" target="_top" class="quad-item">
              <div>
                <div class="quad-icon">📖</div>
                <div class="quad-title">Study</div>
                <div class="quad-desc">Learn concepts</div>
              </div>
              <div class="quad-action">Launch →</div>
            </a>

            <a href="/?page=login&query=Short+Notes" target="_top" class="quad-item">
              <div>
                <div class="quad-icon">📄</div>
                <div class="quad-title">Notes</div>
                <div class="quad-desc">Cornell summaries</div>
              </div>
              <div class="quad-action">Launch →</div>
            </a>

            <a href="/?page=login&query=Practice+Exam+Questions" target="_top" class="quad-item">
              <div>
                <div class="quad-icon">🎯</div>
                <div class="quad-title">Practice</div>
                <div class="quad-desc">Take tests & score</div>
              </div>
              <div class="quad-action">Launch →</div>
            </a>

            <a href="/?page=login" target="_top" class="quad-item">
              <div>
                <div class="quad-icon">📈</div>
                <div class="quad-title">Growth</div>
                <div class="quad-desc">See progress</div>
              </div>
              <div class="quad-action">Launch →</div>
            </a>
          </div>

          <!-- Simulated Live Output Response Box -->
          <div id="aiResponseBox" class="ai-response-box">
            <div class="ai-response-header">
              <span>✦ TOPPERGPT AI RESPONSE</span>
              <span id="responseTag">Active Session</span>
            </div>
            <p id="responseText" style="color: #e5e5e5;"></p>
          </div>

        </div>

        <!-- Floating Badges -->
        <div class="floating-badge-progress">
          <span style="font-size: 0.75rem; font-family: var(--font-mono); color: var(--text-muted); font-weight: 700;">Your Progress</span>
          <div class="radial-score">78%</div>
          <p style="font-size: 0.7rem; font-family: var(--font-mono); color: var(--text-muted);">
            Topics <strong style="color: var(--accent);">24 / 31</strong>
          </p>
        </div>

        <div class="floating-badge-tutor">
          <div style="width: 2.75rem; height: 2.75rem; border-radius: 0.75rem; background: rgba(88, 193, 200, 0.15); border: 1px solid var(--border-highlight); display: flex; align-items: center; justify-content: center; font-size: 1.35rem;">
            🧠
          </div>
          <div>
            <span style="font-size: 0.65rem; color: var(--text-dim); text-transform: uppercase; font-family: var(--font-mono); font-weight: 700; display: block;">AI Study Tutor</span>
            <strong style="font-size: 0.8rem; color: #fff;">Always Ready</strong>
            <p style="font-size: 0.65rem; color: var(--accent);">24/7 Smart Guidance</p>
          </div>
        </div>

        <div class="floating-badge-trophy">
          <span style="font-size: 1.25rem;">🏆</span>
          <div>
            <div style="font-size: 0.75rem; font-weight: 700; color: var(--accent); font-family: var(--font-mono);">Higher Scores</div>
            <div style="font-size: 0.65rem; color: var(--text-muted);">Brighter Future →</div>
          </div>
        </div>

      </div>

    </div>
  </div>

  <!-- Hero Section 2 -->
  <section class="hero-center" id="research">
    <div class="container">
      <div class="badge-center">✦ ACADEMIC INTELLIGENCE 2024–2026</div>
      <h2 class="hero-center-title">
        The AI Tutor Built For<br />
        <span class="gradient-text">Top Academic Ranks</span>
      </h2>
      <p class="hero-center-desc">
        Turn complex formulas, thick textbooks, and exam syllabus into bite-sized mastery with interactive quizzes, Cornell notes, and step-by-step solutions.
      </p>

      <form action="/" method="GET" target="_top" class="search-box">
        <input type="hidden" name="page" value="login" />
        <input type="text" name="query" placeholder="Ask any physics problem, math theorem, or bio concept..." autocomplete="off" />
        <button type="submit" class="btn btn-primary">Explain</button>
      </form>
    </div>
  </section>

  <!-- AI Tools Grid Section -->
  <section id="tools" class="container">
    <div class="section-header">
      <div class="badge-pill">SMART MODULES</div>
      <h2 class="section-title">Supercharge Your <span style="color: var(--accent);">Study Routine</span></h2>
    </div>

    <div class="tools-grid">
      <!-- Card 1 -->
      <a href="/?page=login&feature=tutor" target="_top" class="tool-card">
        <span class="tool-card-badge">Most Popular</span>
        <div>
          <div class="tool-card-icon">💡</div>
          <h3>Study GPT Tutor</h3>
          <p>Instant conversational breakdown of any concept with visual analogies, formula derivations, and common exam pitfalls.</p>
        </div>
        <div class="tool-card-footer">
          <span class="category">Interactive AI</span>
          <span class="action">Open →</span>
        </div>
      </a>

      <!-- Card 2 -->
      <a href="/?page=login&feature=notes" target="_top" class="tool-card">
        <span class="tool-card-badge">Productivity</span>
        <div>
          <div class="tool-card-icon">📄</div>
          <h3>Smart Notes Maker</h3>
          <p>Convert messy syllabus lectures into Cornell-formatted, bulleted summary notes ready for high-recall active retention.</p>
        </div>
        <div class="tool-card-footer">
          <span class="category">Note-Taking</span>
          <span class="action">Open →</span>
        </div>
      </a>

      <!-- Card 3 -->
      <a href="/?page=login&feature=predict" target="_top" class="tool-card">
        <span class="tool-card-badge">Test Prep</span>
        <div>
          <div class="tool-card-icon">🎯</div>
          <h3>Interactive Quiz Arena</h3>
          <p>Practice with real exam questions, timer-based mock drills, and instant scoring diagnostics with answer explanations.</p>
        </div>
        <div class="tool-card-footer">
          <span class="category">Assessment</span>
          <span class="action">Open →</span>
        </div>
      </a>

      <!-- Card 4 -->
      <a href="/?page=login&feature=solver" target="_top" class="tool-card">
        <div>
          <div class="tool-card-icon">⚡</div>
          <h3>Step-by-Step Solver</h3>
          <p>Step-through math and science equations with step-by-step mathematical reasoning and verified logic.</p>
        </div>
        <div class="tool-card-footer">
          <span class="category">Problem Solving</span>
          <span class="action">Open →</span>
        </div>
      </a>

      <!-- Card 5 -->
      <a href="/?page=login&feature=flashcards" target="_top" class="tool-card">
        <div>
          <div class="tool-card-icon">🗂️</div>
          <h3>Flashcard Studio</h3>
          <p>Spaced repetition flashcards generated automatically from your curriculum chapters for instant memory locking.</p>
        </div>
        <div class="tool-card-footer">
          <span class="category">Memory Recall</span>
          <span class="action">Open →</span>
        </div>
      </a>

      <!-- Card 6 -->
      <a href="/?page=login&feature=analytics" target="_top" class="tool-card">
        <div>
          <div class="tool-card-icon">📊</div>
          <h3>Performance Tracker</h3>
          <p>Monitor your subject mastery %, test readiness scores, and daily study streaks with AI-guided recommendations.</p>
        </div>
        <div class="tool-card-footer">
          <span class="category">Analytics</span>
          <span class="action">Open →</span>
        </div>
      </a>
    </div>
  </section>

  <!-- Founder Section -->
  <section class="founder-section" id="business">
    <div class="container">
      <div class="founder-badge">Meet The Founders</div>
      <h2 class="founder-title">
        The mind behind <span>Topper</span><span style="color: var(--accent);">GPT</span>
      </h2>
      <div class="founder-card">
        <img 
          src="https://raw.githubusercontent.com/Kunal1315/TopperGpt-v2.0/main/images/Picsart_26-06-29_09-47-44-859.jpg" 
          alt="Founder" 
          class="founder-img"
          onerror="this.src='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80'"
        />
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="footer">
    <div class="container footer-content">
      <div>
        <strong style="color: #fff;">© 2024–2026 TopperGPT Inc.</strong> All rights reserved.
      </div>
      <div class="footer-links">
        <a href="/?page=login" target="_top">Terms of Use</a>
        <a href="/?page=login" target="_top">Privacy Policy</a>
        <a href="/?page=login" target="_top">Cookie Policy</a>
      </div>
    </div>
  </footer>

</div>

<!-- Interactive Client-Side Handler -->
<script>
  function focusDashboardInput() {
    const input = document.getElementById('studyInput');
    if (input) {
      input.focus();
      input.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function setQuery(tag, queryText) {
    const input = document.getElementById('studyInput');
    if (input) {
      input.value = queryText;
      handleStudySubmit(null, tag);
    }
  }

  function handleStudySubmit(event, customTag) {
    if (event) event.preventDefault();
    const input = document.getElementById('studyInput');
    const query = (input && input.value.trim()) ? input.value.trim() : "Explain Newton's 3rd Law of Motion with everyday examples";
    
    const responseBox = document.getElementById('aiResponseBox');
    const responseText = document.getElementById('responseText');
    const tagLabel = document.getElementById('responseTag');

    if (tagLabel) tagLabel.innerText = customTag || 'Instant Explanation';
    if (responseBox) responseBox.classList.add('visible');

    if (responseText) {
      responseText.innerHTML = '<span style="color: rgb(88, 193, 200);">✦ Formulating verified answer for: "<em>' + query + '</em>"...</span><br><br>' +
        '<strong>Key Takeaway:</strong> Concepts are structured into core university definitions, step-by-step mathematical reasoning, and high-frequency exam problems.<br><br>' +
        '<a href="/?page=login&query=' + encodeURIComponent(query) + '" target="_top" style="display:inline-block; margin-top:8px; background:rgb(88, 193, 200); color:#000; padding:8px 16px; border-radius:9999px; font-weight:700; text-decoration:none; font-size:12px; box-shadow:0 0 15px rgba(88,193,200,0.4);">👉 Unlock Full Verified Solution in TopperGPT →</a>';
    }
  }
</script>
</body>
</html>
"""
    # 3. Render directly via Streamlit HTML Component
    components.html(landing_html, height=2950, scrolling=True)
