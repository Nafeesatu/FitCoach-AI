%%writefile app.py
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

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
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
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.04);
        border-radius: 16px;
        padding: 0.5rem 0.2rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
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
    .stTextInput input {
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.15);
        background-color: rgba(255,255,255,0.05);
        color: white;
    }
    .stChatInput textarea {
        border-radius: 12px !important;
    }
    section[data-testid="stSidebar"] .stButton button {
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.82rem;
        width: 100%;
        text-align: left;
        margin-bottom: 6px;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: rgba(99, 102, 241, 0.35);
        color: #ffffff;
        border-color: rgba(99, 102, 241, 0.6);
    }
    .streamlit-expanderHeader {
        background-color: rgba(99, 102, 241, 0.08) !important;
        border-radius: 10px !important;
        color: #a5b4fc !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

init_db()

SUGGESTIONS = {
    "📊 Calorie & macro calculator": "I'm 28 years old, 70kg, 170cm, moderately active, and I want to maintain my weight. What are my daily calorie and macro targets?",
    "🍗 Food nutrition lookup": "How much protein and how many calories are in 150g of chicken breast?",
    "📈 Track my progress": "Please save my profile: I'm 25 years old, 65kg, 168cm, lightly active, trying to lose weight.",
    "🧠 Evidence-based guidance": "Is it safe to lose 5kg in 2 weeks?"
}

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
    st.markdown("**Try asking:**")

    for label, prompt_text in SUGGESTIONS.items():
        if st.button(label, key=f"sugg_{label}", use_container_width=True):
            st.session_state["pending_input"] = prompt_text

    st.markdown("---")
    if st.session_state.get("user_id"):
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.session_state.pop("pending_input", None)
            st.rerun()

    st.markdown("---")
    st.caption("Built with Groq (Llama 3.3), Streamlit, USDA FoodData Central, and RAG.")

try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    USDA_API_KEY = st.secrets["USDA_API_KEY"]
except Exception:
    st.error("API keys not found. Please configure GROQ_API_KEY and USDA_API_KEY in Streamlit secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
available_functions = make_available_functions(usda_api_key=USDA_API_KEY)

st.markdown("""
<div class="main-header">
    <h1>💪 FitCoach AI</h1>
    <p>Personalized fitness coaching, powered by AI</p>
</div>
""", unsafe_allow_html=True)

if not user_id:
    st.info("👈 Please enter your name or ID in the sidebar to get started.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

has_visible_messages = any(
    (msg["role"] if isinstance(msg, dict) else msg.role) == "user"
    for msg in st.session_state.messages
)

if not has_visible_messages:
    with st.chat_message("assistant", avatar="💪"):
        st.write(
            f"Hey {user_id}! 👋 I'm your AI fitness coach. Try one of the suggestions "
            "in the sidebar, or ask me anything about your calories, nutrition, or progress."
        )

for msg in st.session_state.messages:
    role = msg["role"] if isinstance(msg, dict) else msg.role
    content = msg["content"] if isinstance(msg, dict) else msg.content

    if role == "user":
        with st.chat_message("user", avatar="🧑"):
            display_content = content
            if display_content.startswith("[user_id:"):
                display_content = display_content.split("]", 1)[-1].strip()
            st.write(display_content)
    elif role == "assistant" and content:
        with st.chat_message("assistant", avatar="💪"):
            st.write(content)

typed_input = st.chat_input("Ask me about calories, nutrition, or your progress...")
pending_input = st.session_state.pop("pending_input", None)
user_input = typed_input or pending_input

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
