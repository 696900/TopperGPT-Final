import streamlit as st
from groq import Groq
import pypdf
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TopperGPT Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SECURE CONFIGURATION (Fetch from Streamlit Secrets) ---
# Note: Ensure these names match exactly in your Streamlit Dashboard Secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"] #
    RZP_KEY_ID = st.secrets["RAZORPAY_KEY_ID"] #
    # Firebase key optional for now but kept for structure
    FIREBASE_API_KEY = st.secrets.get("FIREBASE_API_KEY", "") #
except Exception as e:
    st.error("Secrets not found! Please check Streamlit Dashboard Settings > Secrets.")
    st.stop()

# --- 3. SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_pro" not in st.session_state:
    st.session_state.is_pro = False # Default user is FREE

# --- 4. SIDEBAR (User Profile & Credits) ---
with st.sidebar:
    st.title("👤 User Profile")
    st.info(f"Status: {'✅ PRO' if st.session_state.is_pro else '🆓 FREE Tier'}") #
    
    if not st.session_state.is_pro:
        if st.button("🚀 Upgrade to PRO (₹99)"):
            st.warning("Payment integration coming soon! (Verification in progress)") #
    
    st.divider()
    st.markdown("### 🛠️ Quick Tools")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 5. MAIN INTERFACE (Multi-Feature Tabs) ---
st.title("🎓 TopperGPT: Your Personal AI Study Studio")
st.markdown("---")

# NotebookLM inspired feature tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Chat with PDF", 
    "🎥 YouTube Analyzer", 
    "🎧 AI Study Podcast", 
    "🧠 Mind Maps & Quizzes"
])

# --- TAB 1: PDF CHAT (Core Feature) ---
with tab1:
    st.subheader("📚 Upload & Analyze your Notes")
    
    # 1. PDF Upload widget (Key dena zaroori hai memory ke liye)
    pdf_file = st.file_uploader("Upload your study material", type=["pdf"], key="unique_study_uploader")

    # 2. FILE PROCESSING & PERSISTENT MEMORY
    # Agar nayi file aayi hai toh hi processing hogi
    if pdf_file:
        if "pdf_mem" not in st.session_state or st.session_state.get("last_file") != pdf_file.name:
            with st.spinner("🧠 AI is reading your PDF..."):
                try:
                    import pypdf
                    reader = pypdf.PdfReader(pdf_file)
                    extracted_text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += page_text
                    
                    # Memory mein hamesha ke liye save
                    st.session_state.pdf_mem = extracted_text
                    st.session_state.last_file = pdf_file.name
                    st.success(f"✅ {pdf_file.name} is ready for Chat!")
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")

    st.divider()

    # 3. CHAT DISPLAY
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 4. AI LOGIC (Strict Context Injection)
    if user_query := st.chat_input("Ask from your notes..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Check agar memory mein PDF text hai
        if "pdf_mem" in st.session_state and st.session_state.pdf_mem:
            try:
                client = Groq(api_key=GROQ_API_KEY)
                
                # Context limit setting (8000 chars safe side)
                doc_context = st.session_state.pdf_mem[:8000]
                
                # AI ko Force karna ki PDF ka text dekhe
                system_instr = f"You are a study expert. Answer strictly using this PDF content: \n\n{doc_context}"
                
                final_messages = [
                    {"role": "system", "content": system_instr},
                    {"role": "user", "content": user_query}
                ]
                
                comp = client.chat.completions.create(
                    messages=final_messages,
                    model="llama-3.1-8b-instant" # Latest model
                )
                
                ai_reply = comp.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                with st.chat_message("assistant"):
                    st.markdown(ai_reply)
                st.rerun()

            except Exception as e:
                st.error(f"AI Service Error: {e}")
        else:
            # Ye warning tab aati hai jab memory khali ho
            st.warning("⚠️ OOPS! Please upload the PDF again and wait for the 'Success' message.")

# --- TAB 2: YOUTUBE ANALYZER ---
with tab2:
    st.subheader("🎥 Instant Video Insights")
    yt_url = st.text_input("Paste YouTube Video URL")
    if st.button("Analyze Video"):
        st.info("Extracting transcript and generating study notes... (Coming Soon)")

# --- TAB 3: AI PODCAST ---
with tab3:
    st.subheader("🎧 Listen to your Notes")
    st.write("Convert your study material into an AI-generated audio podcast.")
    if st.button("Generate Audio Guide"):
        st.warning("Audio synthesis (gTTS) module will be active once logic is updated.") #

# --- TAB 4: STUDY EXPERT ---
with tab4:
    st.subheader("🧠 Visual & Interactive Learning")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Mind Map"):
            st.write("Mapping your topics visually...")
    with col2:
        if st.button("Create Practice Quiz"):
            st.write("Generating flashcards and MCQ questions...")
