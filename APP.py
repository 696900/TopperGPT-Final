import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
import pandas as pd
from streamlit_mermaid import st_mermaid
from groq import Groq
from gtts import gTTS

# --- 1. CONFIGURATION & FIREBASE ---
st.set_page_config(page_title="TopperGPT Pro", layout="wide", page_icon="🎓")

if not firebase_admin._apps:
    try:
        fb_dict = dict(st.secrets["firebase"])
        fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Error: {e}")

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. SESSION STATE ---
if "user" not in st.session_state: st.session_state.user = None
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "auto_syllabus" not in st.session_state: st.session_state.auto_syllabus = []
if "flashcards" not in st.session_state: st.session_state.flashcards = []

# --- 3. LOGIN PAGE ---
def login_page():
    st.title("🔐 TopperGPT Advanced Login")
    email = st.text_input("Email", placeholder="example@gmail.com")
    password = st.text_input("Password", type="password")
    if st.button("Login / Sign Up"):
        try:
            try: user = auth.get_user_by_email(email)
            except: user = auth.create_user(email=email, password=password)
            st.session_state.user = user.email
            st.rerun()
        except Exception as e: st.error(f"Auth Error: {e}")

if st.session_state.user is None:
    login_page()
else:
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Hi, {st.session_state.user}")
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.markdown("[Razorpay Payment Link](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # --- FULL TABS (1-7) ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💬 Chat PDF", "📋 Syllabus Magic", "📝 Answer Eval", 
        "🧠 Mind Map", "🃏 Flashcards", "❓ Verified PYQs", "⚖️ Legal & Policies"
    ])

    # --- TAB 1: CHAT PDF ---
    with tab1:
        st.subheader("📚 Smart Note Analysis")
        up_1 = st.file_uploader("Upload Study Material", type=["pdf", "png", "jpg", "jpeg"], key="chat_up")
        if up_1:
            with st.spinner("AI reading your notes..."):
                text = ""
                if up_1.type == "application/pdf":
                    with pdfplumber.open(io.BytesIO(up_1.read())) as pdf:
                        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([{"mime_type": up_1.type, "data": up_1.getvalue()}, "Extract text strictly."])
                    text = res.text
                st.session_state.pdf_content = text
                st.success("✅ Notes Synced!")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_input := st.chat_input("Ask from notes..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:15000]}\n\nQ: {u_input}"}])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # --- TAB 2: SYLLABUS TRACKER (LAZY FIX) ---
    with tab2:
        st.subheader("📋 Instant Syllabus Checklist")
        s_file = st.file_uploader("Upload Syllabus PDF (AI will create the roadmap)", type=["pdf"])
        if s_file and st.button("Generate My Roadmap"):
            with st.spinner("Decoding Syllabus..."):
                with pdfplumber.open(io.BytesIO(s_file.read())) as pdf:
                    raw_s = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"Create a clear hierarchical list of chapters and sub-topics from this syllabus text. Format it as a simple list for a checklist: {raw_s[:12000]}"
                res = model.generate_content(prompt)
                st.session_state.auto_syllabus = [line.strip() for line in res.text.split("\n") if line.strip()]
        
        for i, topic in enumerate(st.session_state.auto_syllabus):
            st.checkbox(topic, key=f"syll_{i}")

    # --- TAB 3: ANSWER EVALUATOR (CONTEXT FIX) ---
    with tab3:
        st.subheader("📝 Context-Aware Answer Evaluation")
        q_target = st.text_area("Step 1: Paste Question here (Taaki AI accuracy check kare):")
        ans_target = st.file_uploader("Step 2: Upload Handwritten Answer", type=["png", "jpg", "jpeg", "pdf"])
        if st.button("Evaluate Answer") and q_target and ans_target:
            with st.spinner("AI checking your answer..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content([
                    {"mime_type": ans_target.type, "data": ans_target.getvalue()},
                    f"Target Question: {q_target}. Evaluate this answer out of 10. Check if points are missed. Give improvement feedback."
                ])
                st.info(res.text)

    # --- TAB 4: MIND MAP ---
    with tab4:
        st.subheader("🧠 Professional Mind Map")
        m_in = st.text_input("Map Topic:")
        if st.button("Generate Map"):
            with st.spinner("Designing..."):
                prompt = f"Mermaid graph TD code strictly for: {m_in}. Only code."
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                st_mermaid(res.choices[0].message.content.replace("```mermaid", "").replace("```", "").strip())

    # --- TAB 5: FLASHCARDS (ANKI EXPORT) ---
    with tab5:
        st.subheader("🃏 Smart Swipe Flashcards")
        if st.button("Create Cards from My Notes"):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Create 5 Q&A Flashcards (Question|Answer format) from: {st.session_state.pdf_content[:5000]}"}])
            st.session_state.flashcards = res.choices[0].message.content.split("\n")
        
        for card in st.session_state.flashcards:
            if "|" in card:
                q, a = card.split("|")
                with st.expander(f"Question: {q}"): st.write(f"Answer: {a}")
        
        if st.session_state.flashcards:
            csv_data = "Question,Answer\n" + "\n".join([c.replace("|", ",") for c in st.session_state.flashcards if "|" in c])
            st.download_button("📤 Export to Anki (.csv)", csv_data, "cards.csv")

    # --- TAB 6: VERIFIED PYQS (TRUST FIX) ---
    with tab6:
        st.subheader("❓ Verified PYQ Bank")
        e_name = st.selectbox("Exam:", ["JEE", "NEET", "Boards", "UPSC"])
        t_name = st.text_input("Topic Name for PYQs:")
        if st.button("Get Real Questions"):
            with st.spinner("Searching..."):
                prompt = f"List 5 Real PYQs for {e_name} on topic {t_name}. Rule: If unsure of the year, tag [PRACTICE], if 100% sure tag [VERIFIED PYQ - YEAR]."
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                st.write(res.choices[0].message.content)

    # --- TAB 7: LEGAL & POLICIES (DETAILED) ---
    with tab7:
        st.header("⚖️ Legal, Terms & Policies")
        st.write("Last Updated: January 10, 2026")
        
        with st.expander("🛡️ Privacy Policy", expanded=True):
            st.write("""
            **Introduction:** We value your privacy. This policy explains how we handle your data.
            * **Data Protection:** We use Firebase for secure authentication. We do not sell your personal data.
            * **Study Content:** Your uploaded PDFs/Images are processed in real-time. We do not store your private notes on our servers permanently.
            * **Usage Analytics:** We may collect anonymous usage data to improve the AI's accuracy and user experience.
            """)

        with st.expander("📜 Terms of Service"):
            st.write("""
            **User Agreement:** By using TopperGPT, you agree to the following:
            * **Educational Use:** This tool is for study purposes only. AI results can sometimes be inaccurate; always verify with textbooks.
            * **Account Safety:** Users are responsible for maintaining the confidentiality of their login credentials.
            * **Fair Use:** Any attempt to scrape the platform or misuse AI credits will result in account termination.
            """)

        with st.expander("💰 Refund & Support"):
            st.write("""
            **Payments:** All transactions are handled securely via Razorpay.
            * **Refund Policy:** Refunds are only issued in case of technical failure where PRO features are not accessible for more than 48 hours.
            * **Support:** For any queries, reach out at **support@toppergpt.com**.
            """)
        
        st.divider()
        st.write("📍 **Address:** Neral, Karjat, Maharashtra, India - 410101")