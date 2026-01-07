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
    
    # PDF Upload
    uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"], key="pdf_key")

    # 1. PDF Reading aur Memory Logic
    if uploaded_file:
        # Check agar ye nayi file hai ya purani
        if "file_name" not in st.session_state or st.session_state.file_name != uploaded_file.name:
            with st.spinner("Extracting text from PDF..."):
                try:
                    import pypdf
                    reader = pypdf.PdfReader(uploaded_file)
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                    
                    # Memory mein save karo
                    st.session_state.pdf_text = text
                    st.session_state.file_name = uploaded_file.name
                    st.success(f"Successfully loaded: {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")

    st.divider()

    # 2. Chat History Display
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. Chat Input aur AI Logic
    if prompt := st.chat_input("Ask a question from your notes..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Check agar memory mein PDF text hai
        if "pdf_text" in st.session_state and st.session_state.pdf_text:
            try:
                client = Groq(api_key=GROQ_API_KEY)
                
                # Context limit (8000 chars) taaki AI crash na ho
                context = st.session_state.pdf_text[:8000]
                
                # AI ko strict instructions
                messages = [
                    {
                        "role": "system", 
                        "content": f"You are a helpful study expert. Use the following text extracted from a PDF to answer the user's questions: \n\n{context}"
                    },
                    {"role": "user", "content": prompt}
                ]
                
                completion = client.chat.completions.create(
                    messages=messages,
                    model="llama-3.1-8b-instant", # Working model
                )
                
                response = completion.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.rerun()

            except Exception as e:
                st.error(f"AI Error: {e}")
        else:
            st.warning("Please upload a PDF first so I can analyze it!")

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
