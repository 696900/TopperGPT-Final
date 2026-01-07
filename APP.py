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
    uploaded_file = st.file_uploader("Upload a PDF file to begin", type=["pdf"]) #
    
    if uploaded_file:
        # PDF se text nikalna (Har baar refresh par nikalega taaki AI ke paas rahe)
        import pypdf
        pdf_reader = pypdf.PdfReader(uploaded_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()
        
        st.success(f"File '{uploaded_file.name}' read successfully!") #

        # Chat History Display
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Ask a question from your notes..."):
            # User ka message dikhana aur save karna
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # AI Logic (Groq)
            try:
                client = Groq(api_key=GROQ_API_KEY)
                
                # Sabse zaroori: PDF ka text aur User ka sawal ek saath bhejna
                # Limit context to 5000 chars to stay safe with token limits
                full_prompt = f"Context from PDF: {pdf_text[:5000]}\n\nUser Question: {prompt}"
                
                completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": full_prompt}],
                    model="llama-3.1-8b-instant", # Fix for decommissioned error
                )
                
                response = completion.choices[0].message.content
                
                # Assistant ka jawab save aur display karna
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
                
                # Page refresh taaki chat history update ho jaye
                st.rerun()
                
            except Exception as e:
                st.error(f"AI Error: {e}") #
        

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
