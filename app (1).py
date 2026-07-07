import streamlit as st
from groq import Groq
from agent import run_agent, make_available_functions, SYSTEM_PROMPT
from tools import init_db

st.set_page_config(
    page_title="FitCoach AI",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ============================
# CUSTOM STYLING
# ============================
st.markdown("""
<style>
    /* Overall app background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }

    /* Main title styling */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0;
    }

    /* Chat message bubbles */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.04);
        border-radius: 16px;
        padding: 0.5rem 0.2rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0b1220;
        border-right: 1px solid rgba(255,255,255,0.08);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f1f5f9;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] li {
        color: #cbd5e1;
    }

    /* Text input */
    .stTextInput input {
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.15);
        background-color: rgba(255,255,255,0.05);
        color: white;
    }

    /* Chat input box */
    .stChatInput textarea {
        border-radius: 12px !important;
    }

    /* Feature pills in sidebar */
    .feature-pill {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 3px 3px 3px 0;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    /* Expander (tools used) */
    .streamlit-expanderHeader {
        background-color: rgba(99, 102, 241, 0.08) !important;
        border-radius: 10px !important;
        color: #a5b4fc !important;
    }

    /* Hide default streamlit footer/menu for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Initialize database on first run ---
init_db()

# ============================
# SIDEBAR
# ============================
with st.sidebar:
    st.markdown("## 💪 FitCoach AI")
    st.markdown("Your personal AI-powered fitness and nutrition coach.")

    st.markdown("---")

    user_id = st.text_input(
        "👤 Your name or ID",
        value=st.session_state.get("user_id", ""),
        placeholder="e.g. Nafisat",
        help="Used to remember your profile and progress across sessions."
    )
    st.session_state["user_id"] = user_id

    st.markdown("---")
    st.markdown("**What I can help with:**")
    st.markdown("""
        <span class="feature-pill">📊 Calorie & macro calculator</span>
        <span class="feature-pill">🍗 Food nutrition lookup</span>
        <span class="feature-pill">📈 Progress tracking</span>
        <span class="feature-pill">🧠 Evidence-based guidance</span>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.session_state.get("user_id"):
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.rerun()

    st.markdown("---")
    st.caption("Built with Groq (Llama 3.3), Streamlit, USDA FoodData Central, and RAG.")

# --- Load API keys from Streamlit secrets ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    USDA_API_KEY = st.secrets["USDA_API_KEY"]
except Exception:
    st.error("API keys not found. Please configure GROQ_API_KEY and USDA_API_KEY in Streamlit secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
available_functions = make_available_functions(usda_api_key=USDA_API_KEY)

# ============================
# MAIN HEADER
# ============================
st.markdown("""
<div class="main-header">
    <h1>💪 FitCoach AI</h1>
    <p>Personalized fitness coaching, powered by AI</p>
</div>
""", unsafe_allow_html=True)

if not user_id:
    st.info("👈 Please enter your name or ID in the sidebar to get started.")
    st.stop()

# --- Initialize chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- Welcome message if no conversation yet ---
has_visible_messages = any(
    (msg["role"] if isinstance(msg, dict) else msg.role) == "user"
    for msg in st.session_state.messages
)

if not has_visible_messages:
    with st.chat_message("assistant", avatar="💪"):
        st.write(
            f"Hey {user_id}! 👋 I'm your AI fitness coach. Tell me a bit about "
            "yourself (age, weight, height, activity level, and goal) and I can "
            "calculate your calorie and macro targets, look up nutrition info for "
            "any food, and track your progress over time. What would you like to start with?"
        )

# --- Display chat history ---
for msg in st.session_state.messages:
    role = msg["role"] if isinstance(msg, dict) else msg.role
    content = msg["content"] if isinstance(msg, dict) else msg.content

    if role == "user":
        with st.chat_message("user", avatar="🧑"):
            # Strip the injected [user_id: ...] prefix before displaying
            display_content = content
            if display_content.startswith("[user_id:"):
                display_content = display_content.split("]", 1)[-1].strip()
            st.write(display_content)
    elif role == "assistant" and content:
        with st.chat_message("assistant", avatar="💪"):
            st.write(content)

# --- Chat input ---
user_input = st.chat_input("Ask me about calories, nutrition, or your progress...")

if user_input:
    contextual_input = f"[user_id: {user_id}] {user_input}"
    st.session_state.messages.append({"role": "user", "content": contextual_input})

    with st.chat_message("user", avatar="🧑"):
        st.write(user_input)

    with st.chat_message("assistant", avatar="💪"):
        with st.spinner("Thinking..."):
            answer, updated_messages, tool_log = run_agent(
                client, st.session_state.messages, available_functions
            )
            st.session_state.messages = updated_messages
            st.write(answer)

            if tool_log:
                with st.expander("🔧 Tools used in this response"):
                    for call in tool_log:
                        st.write(f"**{call['tool']}**({call['args']})")
