import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
import pdfplumber
import io
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
if "syllabus" not in st.session_state: st.session_state.syllabus = []

# --- 3. LOGIN PAGE ---
def login_page():
    st.title("🔐 TopperGPT Login")
    email = st.text_input("Email")
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
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🎓 TopperGPT")
        st.success(f"Hi, {st.session_state.user}")
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.markdown("[Payment Link](https://rzp.io/l/your_link)")
        st.divider()
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    # --- UPDATED TABS (YouTube removed, New Features added) ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💬 Chat PDF", "📋 Syllabus Tracker", "📝 Answer Evaluator", 
        "🧠 Mind Map", "🃏 Flashcards", "❓ PYQs & Quiz", "⚖️ Legal"
    ])

    # --- TAB 1: CHAT PDF ---
    with tab1:
        st.subheader("📚 Analyze Notes")
        up_1 = st.file_uploader("Upload Notes", type=["pdf", "png", "jpg", "jpeg"])
        if up_1:
            with st.spinner("Scanning..."):
                text = ""
                if up_1.type == "application/pdf":
                    with pdfplumber.open(io.BytesIO(up_1.read())) as pdf:
                        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                else:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([{"mime_type": up_1.type, "data": up_1.getvalue()}, "Extract text."])
                    text = res.text
                st.session_state.pdf_content = text
                st.success("✅ Synced!")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if u_input := st.chat_input("Ask anything..."):
            st.session_state.messages.append({"role": "user", "content": u_input})
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Context: {st.session_state.pdf_content[:12000]}\n\nQ: {u_input}"}])
            st.session_state.messages.append({"role": "assistant", "content": res.choices[0].message.content})
            st.rerun()

    # --- TAB 2: SYLLABUS TRACKER (NEW) ---
    with tab2:
        st.subheader("📋 Exam Syllabus Tracker")
        new_topic = st.text_input("Add Topic (e.g., Thermodynamics):")
        if st.button("Add to List"):
            st.session_state.syllabus.append({"topic": new_topic, "done": False})
        
        for i, item in enumerate(st.session_state.syllabus):
            col_t, col_c = st.columns([4, 1])
            done = col_c.checkbox("Done", key=f"check_{i}", value=item["done"])
            st.session_state.syllabus[i]["done"] = done
            col_t.write(f"**{item['topic']}**")

    # --- TAB 3: ANSWER EVALUATOR (NEW) ---
    with tab3:
        st.subheader("📝 AI Answer Evaluator")
        q_text = st.text_area("Question dalo:")
        ans_file = st.file_uploader("Apne answer ki photo ya PDF dalo:", type=["pdf", "png", "jpg", "jpeg"])
        if st.button("Evaluate My Answer"):
            if ans_file and q_text:
                with st.spinner("Checking answer..."):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    ans_data = ans_file.getvalue()
                    res = model.generate_content([{"mime_type": ans_file.type, "data": ans_data}, f"Question: {q_text}. Evaluate this answer out of 10 and give feedback."])
                    st.info(res.text)

    # --- TAB 4: MIND MAP ---
    with tab4:
        st.subheader("🧠 Mind Map")
        m_topic = st.text_input("Topic for Map:")
        if st.button("Generate Map"):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Mermaid code ONLY (graph TD) for: {m_topic}"}])
            st_mermaid(res.choices[0].message.content.replace("```mermaid", "").replace("```", ""))

    # --- TAB 5: AI FLASHCARDS (NEW) ---
    with tab5:
        st.subheader("🃏 Quick Revision Flashcards")
        if st.button("Generate Flashcards from Notes"):
            if st.session_state.pdf_content:
                res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Create 5 flashcards (Front: Question, Back: Answer) from: {st.session_state.pdf_content[:5000]}"}])
                st.write(res.choices[0].message.content)

    # --- TAB 6: PYQs & QUIZ (NEW) ---
    with tab6:
        st.subheader("❓ Previous Year Questions & Quiz")
        exam_name = st.text_input("Exam Name (e.g., JEE, NEET, UPSC):")
        if st.button("Get PYQs"):
            res = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"List 5 important PYQs for {exam_name} with answers."}])
            st.write(res.choices[0].message.content)

    # --- TAB 7: LEGAL ---
    with tab7:
        st.subheader("⚖️ Legal Policies")
        st.write("Privacy Policy | Terms | Contact: support@toppergpt.com")