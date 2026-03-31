import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import time
import re
from datetime import datetime
from collections import Counter

# ---------------------------------
# LOAD .env
# ---------------------------------
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ---------------------------------
# OPENROUTER CLIENT
# ---------------------------------
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(
    page_title="NeuralChat",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------
# SESSION STATE
# ---------------------------------
defaults = {
    "conversations": {},
    "current_chat": None,
    "theme": "Dark",
    "agent_name": "Nova",
    "agent_tone": "Friendly",
    "temperature": 0.7,
    "show_summary": False,
    "summary_content": "",
    "show_analytics": False,
    "pinned_chats": set(),
    "chat_titles": {},
    "model": "openai/gpt-4o-mini",
    "system_prompt_override": "",
    "show_tokens": True,
    "message_reactions": {},
    "typing_effect": True,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------
# MODELS
# ---------------------------------
MODELS = {
    "GPT-4o Mini": "openai/gpt-4o-mini",
    "GPT-4o": "openai/gpt-4o",
    "Claude 3 Haiku": "anthropic/claude-3-haiku",
    "Gemini Flash": "google/gemini-flash-1.5",
    "Llama 3.1 8B": "meta-llama/llama-3.1-8b-instruct:free",
}

AGENTS = {
    "Nova": {"emoji": "🔮", "color": "#a78bfa", "desc": "Futuristic & brilliant"},
    "Sage": {"emoji": "🌿", "color": "#34d399", "desc": "Wise & thoughtful"},
    "Blaze": {"emoji": "🔥", "color": "#f97316", "desc": "Bold & energetic"},
    "Echo": {"emoji": "🌊", "color": "#38bdf8", "desc": "Calm & precise"},
    "Lyra": {"emoji": "🎵", "color": "#f472b6", "desc": "Creative & expressive"},
    "Custom": {"emoji": "⚙️", "color": "#94a3b8", "desc": "Your own agent"},
}

TONES = {
    "Friendly": "Be warm, approachable, and conversational. Use casual language and feel free to show enthusiasm.",
    "Casual": "Be laid-back, easygoing, and personable. Use familiar phrasing and a friendly tone.",
    "Professional": "Be polished, thorough, and accurate. Balance warmth with professionalism.",
    "Strict": "Be formal, precise, and concise. Avoid fluff. Maintain professional standards.",
    "Crisp": "Be ultra-brief and direct. No preamble. Just the answer.",
    "Socratic": "Help the user think by asking probing questions. Guide rather than answer directly.",
    "Creative": "Be imaginative, use metaphors, think outside the box, and bring unexpected angles.",
}

# ---------------------------------
# HELPERS
# ---------------------------------
def new_chat():
    chat_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    st.session_state.conversations[chat_id] = []
    st.session_state.current_chat = chat_id
    st.session_state.chat_titles[chat_id] = "New Conversation"

def delete_chat(chat_id):
    del st.session_state.conversations[chat_id]
    st.session_state.pinned_chats.discard(chat_id)
    if chat_id in st.session_state.chat_titles:
        del st.session_state.chat_titles[chat_id]
    if st.session_state.current_chat == chat_id:
        remaining = list(st.session_state.conversations.keys())
        st.session_state.current_chat = remaining[-1] if remaining else None

def add_message(role, content):
    cid = st.session_state.current_chat
    st.session_state.conversations[cid].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M"),
        "id": f"{cid}_{len(st.session_state.conversations[cid])}"
    })

def export_chat(chat_id):
    return json.dumps(st.session_state.conversations[chat_id], indent=2, default=str)

def get_system_prompt():
    name = st.session_state.agent_name
    tone = get_tone_instruction(st.session_state.agent_tone)
    override = st.session_state.system_prompt_override
    base = f"You are {name}, an advanced AI assistant. {tone}"
    if override.strip():
        base += f"\n\nAdditional instructions: {override}"
    return base

def get_tone_instruction(tone):
    return TONES.get(tone, TONES["Friendly"])

def count_words(messages):
    total = sum(len(m["content"].split()) for m in messages)
    return total

def estimate_tokens(text):
    return int(len(text.split()) * 1.3)

def get_chat_preview(chat_id):
    msgs = st.session_state.conversations.get(chat_id, [])
    if not msgs:
        return "Empty chat"
    last = [m for m in msgs if m["role"] == "user"]
    if last:
        preview = last[-1]["content"][:40]
        return preview + "..." if len(last[-1]["content"]) > 40 else preview
    return "No messages yet"

def auto_title_chat(chat_id):
    msgs = st.session_state.conversations.get(chat_id, [])
    user_msgs = [m for m in msgs if m["role"] == "user"]
    if user_msgs:
        title = user_msgs[0]["content"][:28]
        if len(user_msgs[0]["content"]) > 28:
            title += "..."
        st.session_state.chat_titles[chat_id] = title

def call_ai(messages_payload, temperature=None, max_tokens=1500):
    t = temperature if temperature is not None else st.session_state.temperature
    system_msg = {"role": "system", "content": get_system_prompt()}
    full_msgs = [system_msg] + messages_payload
    res = client.chat.completions.create(
        model=st.session_state.model,
        messages=full_msgs,
        temperature=t,
        max_tokens=max_tokens,
    )
    return res.choices[0].message.content

def summarize_chat(chat_id):
    msgs = st.session_state.conversations.get(chat_id, [])
    if not msgs:
        return "Chat is empty."
    payload = [
        {"role": "user", "content": "Please provide a structured summary of this conversation. Include: key topics discussed, main conclusions or answers, and any action items or follow-ups mentioned."},
        *[{"role": m["role"], "content": m["content"]} for m in msgs]
    ]
    res = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a conversation summarizer. Be concise and structured."}] + payload,
        temperature=0.2,
        max_tokens=600,
    )
    return res.choices[0].message.content

def get_chat_analytics(chat_id):
    msgs = st.session_state.conversations.get(chat_id, [])
    if not msgs:
        return None
    user_msgs = [m for m in msgs if m["role"] == "user"]
    ai_msgs = [m for m in msgs if m["role"] == "assistant"]
    all_words = " ".join(m["content"] for m in msgs).lower()
    words = re.findall(r'\b[a-z]{4,}\b', all_words)
    stop = {"this","that","with","have","from","they","been","were","will","would","your","what","when","about","which","their","there","could","other","into","more","also","some","these","than","then","just","like","over","such","both","each","very"}
    filtered = [w for w in words if w not in stop]
    top_words = Counter(filtered).most_common(8)
    return {
        "total_messages": len(msgs),
        "user_messages": len(user_msgs),
        "ai_messages": len(ai_msgs),
        "total_words": count_words(msgs),
        "avg_user_length": int(sum(len(m["content"].split()) for m in user_msgs) / max(len(user_msgs), 1)),
        "avg_ai_length": int(sum(len(m["content"].split()) for m in ai_msgs) / max(len(ai_msgs), 1)),
        "top_words": top_words,
        "estimated_tokens": estimate_tokens(" ".join(m["content"] for m in msgs)),
    }

# ---------------------------------
# THEME CSS
# ---------------------------------
DARK_CSS = """
:root {
    --bg0: #0a0a0f;
    --bg1: #111118;
    --bg2: #1a1a24;
    --bg3: #22222e;
    --bg4: #2a2a38;
    --border: rgba(255,255,255,0.07);
    --border-bright: rgba(167,139,250,0.3);
    --text0: #f1f0ff;
    --text1: #c4c2e0;
    --text2: #8884aa;
    --accent: #a78bfa;
    --accent2: #7c3aed;
    --user-bubble: #1e1b4b;
    --user-bubble-border: #4c1d95;
    --ai-bubble: #1a1a24;
    --ai-bubble-border: rgba(255,255,255,0.06);
    --glow: 0 0 20px rgba(167,139,250,0.15);
    --shadow: 0 4px 24px rgba(0,0,0,0.4);
}
"""

LIGHT_CSS = """
:root {
    --bg0: #f8f7ff;
    --bg1: #ffffff;
    --bg2: #f3f2ff;
    --bg3: #ede9ff;
    --bg4: #ddd6fe;
    --border: rgba(0,0,0,0.07);
    --border-bright: rgba(124,58,237,0.25);
    --text0: #1a1028;
    --text1: #3d3460;
    --text2: #7c6fa0;
    --accent: #7c3aed;
    --accent2: #5b21b6;
    --user-bubble: #ede9ff;
    --user-bubble-border: #c4b5fd;
    --ai-bubble: #ffffff;
    --ai-bubble-border: rgba(0,0,0,0.06);
    --glow: 0 0 20px rgba(124,58,237,0.08);
    --shadow: 0 4px 24px rgba(0,0,0,0.08);
}
"""

theme_vars = DARK_CSS if st.session_state.theme == "Dark" else LIGHT_CSS

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');

{theme_vars}

* {{ box-sizing: border-box; }}

html, body, .stApp {{
    background-color: var(--bg0) !important;
    color: var(--text0) !important;
    font-family: 'DM Sans', sans-serif;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: var(--bg1) !important;
    border-right: 1px solid var(--border) !important;
}}
section[data-testid="stSidebar"] * {{
    color: var(--text0) !important;
}}
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stTextInput > div > div,
section[data-testid="stSidebar"] .stTextArea > div > div {{
    background: var(--bg2) !important;
    border-color: var(--border) !important;
    color: var(--text0) !important;
}}

/* Main content */
.main .block-container {{
    background: transparent !important;
    padding: 1.5rem 2rem 6rem 2rem !important;
    max-width: 900px !important;
}}

/* Header */
.nc-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 0 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
}}
.nc-logo {{
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    box-shadow: var(--glow);
    flex-shrink: 0;
}}
.nc-header-text h1 {{
    font-family: 'Syne', sans-serif;
    font-size: 22px;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, var(--text0), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.nc-header-text p {{
    font-size: 12px;
    color: var(--text2);
    margin: 2px 0 0 0;
}}
.nc-header-badge {{
    margin-left: auto;
    background: linear-gradient(135deg, rgba(167,139,250,0.15), rgba(124,58,237,0.1));
    border: 1px solid var(--border-bright);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 11px;
    color: var(--accent);
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

/* Chat Bubbles */
.msg-row {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 20px;
    animation: fadeSlideUp 0.25s ease;
}}
@keyframes fadeSlideUp {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
.msg-row.user {{ flex-direction: row-reverse; }}
.msg-avatar {{
    width: 34px;
    height: 34px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
    margin-top: 2px;
}}
.msg-avatar.user-av {{
    background: linear-gradient(135deg, #1e1b4b, #4c1d95);
    border: 1px solid #4c1d95;
}}
.msg-avatar.ai-av {{
    background: linear-gradient(135deg, var(--bg3), var(--bg4));
    border: 1px solid var(--border-bright);
}}
.msg-body {{ max-width: 72%; }}
.msg-meta {{
    font-size: 10px;
    color: var(--text2);
    margin-bottom: 4px;
    font-weight: 500;
}}
.msg-row.user .msg-meta {{ text-align: right; }}
.msg-bubble {{
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 14.5px;
    line-height: 1.65;
    word-break: break-word;
    white-space: pre-wrap;
    position: relative;
}}
.msg-bubble.user-bubble {{
    background: var(--user-bubble);
    border: 1px solid var(--user-bubble-border);
    border-top-right-radius: 4px;
}}
.msg-bubble.ai-bubble {{
    background: var(--ai-bubble);
    border: 1px solid var(--ai-bubble-border);
    border-top-left-radius: 4px;
    box-shadow: var(--shadow);
}}

/* Code blocks in messages */
.msg-bubble code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    background: rgba(0,0,0,0.3);
    padding: 2px 6px;
    border-radius: 4px;
    color: #c4b5fd;
}}

/* Token badge */
.token-badge {{
    display: inline-block;
    font-size: 10px;
    color: var(--text2);
    margin-top: 4px;
    font-family: 'JetBrains Mono', monospace;
}}

/* Empty state */
.empty-state {{
    text-align: center;
    padding: 80px 20px;
}}
.empty-state .big-emoji {{
    font-size: 64px;
    margin-bottom: 16px;
    display: block;
    filter: drop-shadow(0 0 20px rgba(167,139,250,0.3));
}}
.empty-state h2 {{
    font-family: 'Syne', sans-serif;
    font-size: 26px;
    font-weight: 800;
    background: linear-gradient(135deg, var(--text0), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 10px 0;
}}
.empty-state p {{
    color: var(--text2);
    font-size: 15px;
    max-width: 360px;
    margin: 0 auto 40px auto;
    line-height: 1.6;
}}
.suggestion-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
    max-width: 600px;
    margin: 0 auto;
}}
.chip {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 8px 18px;
    font-size: 13px;
    color: var(--text1);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
}}

/* Landing Page */
.landing-wrap {{
    min-height: 60vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 0;
}}
.landing-title {{
    font-family: 'Syne', sans-serif;
    font-size: 58px;
    font-weight: 800;
    line-height: 1.1;
    text-align: center;
    background: linear-gradient(135deg, var(--text0) 30%, var(--accent) 70%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 14px;
}}
.landing-sub {{
    font-size: 17px;
    color: var(--text2);
    text-align: center;
    margin-bottom: 56px;
    max-width: 440px;
    line-height: 1.7;
}}
.feature-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    width: 100%;
    max-width: 800px;
    margin-bottom: 48px;
}}
.feat-card {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px 18px;
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
}}
.feat-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), transparent);
    opacity: 0;
    transition: opacity 0.25s;
}}
.feat-card:hover {{ border-color: var(--border-bright); transform: translateY(-3px); }}
.feat-card:hover::before {{ opacity: 1; }}
.feat-icon {{ font-size: 28px; margin-bottom: 10px; display: block; }}
.feat-title {{ font-size: 14px; font-weight: 700; color: var(--text0); margin-bottom: 6px; }}
.feat-desc {{ font-size: 12px; color: var(--text2); line-height: 1.5; }}

/* Analytics */
.analytics-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}}
.stat-card {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}}
.stat-value {{
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 800;
    background: linear-gradient(135deg, var(--text0), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.stat-label {{
    font-size: 11px;
    color: var(--text2);
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
}}

/* Word cloud-style */
.word-tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
.word-tag {{
    background: var(--bg3);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    color: var(--text1);
}}

/* Sidebar sections */
.sidebar-section {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 14px;
}}
.sidebar-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text2) !important;
    font-weight: 700;
    margin-bottom: 10px;
    display: block;
}}

/* Buttons */
.stButton > button {{
    background: var(--bg2) !important;
    color: var(--text0) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    padding: 6px 14px !important;
}}
.stButton > button:hover {{
    background: var(--bg3) !important;
    border-color: var(--border-bright) !important;
    transform: translateY(-1px) !important;
}}

/* Primary action button */
.primary-btn button {{
    background: linear-gradient(135deg, var(--accent2), var(--accent)) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}}

/* Divider */
hr {{
    border-color: var(--border) !important;
    margin: 20px 0 !important;
}}

/* Selectbox */
.stSelectbox > label, .stTextInput > label, .stTextArea > label, .stSlider > label {{
    color: var(--text1) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}}

/* Chat input */
.stChatInputContainer, div[data-testid="stChatInput"] {{
    background: var(--bg2) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 14px !important;
}}

/* Remove default streamlit elements */
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--bg4); border-radius: 4px; }}

/* Alert / info */
.stAlert {{
    background: var(--bg2) !important;
    border-color: var(--border-bright) !important;
    color: var(--text0) !important;
}}
.stSuccess {{
    background: rgba(52,211,153,0.1) !important;
    border-color: rgba(52,211,153,0.3) !important;
}}

/* Summary box */
.summary-box {{
    background: var(--bg2);
    border: 1px solid var(--border-bright);
    border-radius: 16px;
    padding: 24px;
    margin-top: 20px;
    position: relative;
}}
.summary-box::before {{
    content: '📋 SUMMARY';
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: var(--accent);
    display: block;
    margin-bottom: 14px;
}}

/* Chat list items */
.chat-item {{
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: all 0.2s;
}}
.chat-item:hover, .chat-item.active {{
    border-color: var(--border-bright);
    background: var(--bg3);
}}
.chat-item-title {{
    font-size: 13px;
    font-weight: 600;
    color: var(--text0);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.chat-item-preview {{
    font-size: 11px;
    color: var(--text2);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.pinned-badge {{
    font-size: 10px;
    color: #fbbf24;
    margin-left: 4px;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------
# SIDEBAR
# ---------------------------------
with st.sidebar:
    # Logo
    agent_info = AGENTS.get(st.session_state.agent_name, AGENTS["Custom"])
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; padding:10px 0 20px 0; border-bottom:1px solid var(--border); margin-bottom:16px;">
        <div style="width:40px;height:40px;background:linear-gradient(135deg,{agent_info['color']}44,{agent_info['color']}22);
            border:1px solid {agent_info['color']}66;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px;">
            {agent_info['emoji']}
        </div>
        <div>
            <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:18px;">NeuralChat</div>
            <div style="font-size:11px;color:var(--text2);">Powered by OpenRouter</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme
    st.markdown('<span class="sidebar-label">🎨 Appearance</span>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("☀️ Light", use_container_width=True):
            st.session_state.theme = "Light"; st.rerun()
    with col2:
        if st.button("🌙 Dark", use_container_width=True):
            st.session_state.theme = "Dark"; st.rerun()

    st.markdown("---")

    # Model Selection
    st.markdown('<span class="sidebar-label">🤖 Model</span>', unsafe_allow_html=True)
    model_display = {v: k for k, v in MODELS.items()}
    current_model_name = model_display.get(st.session_state.model, "GPT-4o Mini")
    selected_model = st.selectbox("Model", list(MODELS.keys()),
        index=list(MODELS.keys()).index(current_model_name), label_visibility="collapsed")
    st.session_state.model = MODELS[selected_model]

    st.markdown("---")

    # Agent Configuration
    st.markdown('<span class="sidebar-label">🧠 Agent</span>', unsafe_allow_html=True)

    agent_choice = st.selectbox("Persona", list(AGENTS.keys()),
        index=list(AGENTS.keys()).index(st.session_state.agent_name) if st.session_state.agent_name in AGENTS else 0)
    if agent_choice != "Custom":
        st.session_state.agent_name = agent_choice
    else:
        custom_name = st.text_input("Custom Name", value=st.session_state.agent_name if st.session_state.agent_name not in AGENTS else "Aria")
        st.session_state.agent_name = custom_name

    st.session_state.agent_tone = st.selectbox("Tone", ["Friendly", "Casual", "Professional", "Strict", "Crisp", "Socratic", "Creative"],
        index=["Friendly", "Casual", "Professional", "Strict", "Crisp", "Socratic", "Creative"].index(st.session_state.agent_tone) if st.session_state.agent_tone in ["Friendly", "Casual", "Professional", "Strict", "Crisp", "Socratic", "Creative"] else 0)

    st.markdown('<small style="color:var(--text2);">Agent tone drives response style. Friendly/Casual/Professional available.</small>', unsafe_allow_html=True)

    st.markdown('---')

    with st.expander("⚙️ Custom System Prompt"):
        st.session_state.system_prompt_override = st.text_area(
            "Additional instructions", value=st.session_state.system_prompt_override,
            height=80, placeholder="e.g. Always respond in bullet points...", label_visibility="collapsed")

    st.markdown("---")

    # Creativity
    st.markdown('<span class="sidebar-label">🌡️ Creativity</span>', unsafe_allow_html=True)
    st.session_state.temperature = st.slider("Creativity", 0.0, 1.0, st.session_state.temperature, 0.05, label_visibility="collapsed")
    temp_labels = {0.0: "Deterministic", 0.3: "Focused", 0.7: "Balanced", 1.0: "Wild"}
    closest = min(temp_labels.keys(), key=lambda x: abs(x - st.session_state.temperature))
    st.markdown(f"<div style='font-size:11px;color:var(--text2);text-align:center;margin-top:-8px;'>{temp_labels[closest]}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Chats
    st.markdown('<span class="sidebar-label">💬 Conversations</span>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("✦ New Conversation", use_container_width=True):
            new_chat(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.conversations:
        st.markdown("")
        pinned = [c for c in st.session_state.conversations if c in st.session_state.pinned_chats]
        regular = [c for c in sorted(st.session_state.conversations.keys(), reverse=True) if c not in st.session_state.pinned_chats]

        for section_label, chat_ids in [("📌 Pinned", pinned), ("Recent", regular)]:
            if not chat_ids:
                continue
            st.markdown(f"<div style='font-size:10px;color:var(--text2);font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:8px 0 4px 2px;'>{section_label}</div>", unsafe_allow_html=True)
            for chat_id in chat_ids[:20]:
                is_active = st.session_state.current_chat == chat_id
                title = st.session_state.chat_titles.get(chat_id, "New Conversation")
                preview = get_chat_preview(chat_id)
                is_pinned = chat_id in st.session_state.pinned_chats
                msg_count = len(st.session_state.conversations.get(chat_id, []))
                chat_date = datetime.strptime(chat_id, '%Y%m%d%H%M%S%f').strftime('%b %d, %I:%M %p')
                active_dot = "🟣 " if is_active else ""

                # Chat card as HTML info display
                active_style = "border-color:var(--border-bright);background:var(--bg3);" if is_active else ""
                st.markdown(f"""
                <div class="chat-item {'active' if is_active else ''}" style="{active_style}">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:2px;">
                        <div class="chat-item-title">{active_dot}{title[:26]}{'...' if len(title)>26 else ''}</div>
                        <div style="font-size:10px;color:var(--text2);flex-shrink:0;margin-left:6px;">{'📌' if is_pinned else ''} {msg_count} msgs</div>
                    </div>
                    <div class="chat-item-preview">{preview}</div>
                    <div style="font-size:10px;color:var(--text2);margin-top:3px;">{chat_date}</div>
                </div>
                """, unsafe_allow_html=True)

                # Action buttons below each card
                col_a, col_b, col_c = st.columns([5, 1, 1])
                with col_a:
                    btn_label = f"{'▶ Open' if not is_active else '✓ Active'}"
                    if st.button(btn_label, key=f"sel_{chat_id}", use_container_width=True):
                        st.session_state.current_chat = chat_id; st.rerun()
                with col_b:
                    pin_label = "📍" if is_pinned else "📌"
                    if st.button(pin_label, key=f"pin_{chat_id}", help="Pin/unpin chat"):
                        if is_pinned:
                            st.session_state.pinned_chats.discard(chat_id)
                        else:
                            st.session_state.pinned_chats.add(chat_id)
                        st.rerun()
                with col_c:
                    if st.button("🗑", key=f"del_{chat_id}", help="Delete chat"):
                        delete_chat(chat_id); st.rerun()

    st.markdown("---")

    # Export section
    st.markdown('<span class="sidebar-label">📦 Export</span>', unsafe_allow_html=True)
    if st.session_state.current_chat and st.session_state.conversations.get(st.session_state.current_chat):
        current_title = st.session_state.chat_titles.get(st.session_state.current_chat, "chat")
        msgs = st.session_state.conversations[st.session_state.current_chat]
        st.markdown(f"<div style='font-size:11px;color:var(--text2);margin-bottom:8px;'>Current: <b style=\"color:var(--text1);\">{current_title[:30]}</b> · {len(msgs)} messages</div>", unsafe_allow_html=True)

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.download_button(
                "⬇️ JSON",
                data=export_chat(st.session_state.current_chat),
                file_name=f"neuralchat_{st.session_state.current_chat}.json",
                mime="application/json",
                use_container_width=True,
                help="Export as JSON"
            )
        with col_exp2:
            # Export as plain text
            txt_lines = []
            for m in msgs:
                role_label = "You" if m["role"] == "user" else st.session_state.agent_name
                ts = m.get("timestamp", "")
                txt_lines.append(f"[{ts}] {role_label}:\n{m['content']}\n")
            txt_export = "\n".join(txt_lines)
            st.download_button(
                "📄 TXT",
                data=txt_export,
                file_name=f"neuralchat_{st.session_state.current_chat}.txt",
                mime="text/plain",
                use_container_width=True,
                help="Export as plain text"
            )

        # Export ALL chats
        if len(st.session_state.conversations) > 1:
            all_chats = {
                cid: {
                    "title": st.session_state.chat_titles.get(cid, "Conversation"),
                    "messages": msgs_list
                }
                for cid, msgs_list in st.session_state.conversations.items()
            }
            st.download_button(
                "⬇️ Export All Chats",
                data=json.dumps(all_chats, indent=2, default=str),
                file_name=f"neuralchat_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                help="Export all conversations as JSON"
            )
    else:
        st.markdown("<div style='font-size:12px;color:var(--text2);'>Start a conversation to enable export.</div>", unsafe_allow_html=True)

    # Token indicator
    if st.session_state.current_chat:
        msgs = st.session_state.conversations.get(st.session_state.current_chat, [])
        tokens = estimate_tokens(" ".join(m["content"] for m in msgs))
        pct = min(tokens / 4000, 1.0)
        color = "#34d399" if pct < 0.5 else "#fbbf24" if pct < 0.8 else "#f87171"
        st.markdown(f"""
        <div style="margin-top:8px;padding:10px;background:var(--bg2);border-radius:10px;border:1px solid var(--border);">
            <div style="font-size:10px;color:var(--text2);font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Context Usage</div>
            <div style="background:var(--bg3);border-radius:4px;height:5px;overflow:hidden;">
                <div style="width:{int(pct*100)}%;height:100%;background:{color};transition:width 0.3s;border-radius:4px;"></div>
            </div>
            <div style="font-size:10px;color:var(--text2);margin-top:4px;font-family:'JetBrains Mono',monospace;">~{tokens} tokens</div>
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------
# MAIN AREA
# ---------------------------------
agent_info = AGENTS.get(st.session_state.agent_name, AGENTS["Custom"])

if not st.session_state.current_chat:
    # Landing
    st.markdown(f"""
    <div class="landing-wrap">
        <div class="landing-title">Meet {st.session_state.agent_name}</div>
        <p class="landing-sub">An AI assistant tuned to your needs — {agent_info['desc']}. Ready to think, create, and explore with you.</p>
        <div class="feature-grid">
            <div class="feat-card">
                <span class="feat-icon">🧠</span>
                <div class="feat-title">Multi-Model Support</div>
                <div class="feat-desc">Switch between GPT-4o, Claude, Gemini and more on the fly</div>
            </div>
            <div class="feat-card">
                <span class="feat-icon">💬</span>
                <div class="feat-title">Smart Conversations</div>
                <div class="feat-desc">Full chat history, pinned threads, and persistent context</div>
            </div>
            <div class="feat-card">
                <span class="feat-icon">📊</span>
                <div class="feat-title">Chat Analytics</div>
                <div class="feat-desc">Word frequency, message stats, and conversation insights</div>
            </div>
            <div class="feat-card">
                <span class="feat-icon">🎭</span>
                <div class="feat-title">Agent Personas</div>
                <div class="feat-desc">Pre-built characters or fully custom system prompts</div>
            </div>
            <div class="feat-card">
                <span class="feat-icon">📝</span>
                <div class="feat-title">AI Summaries</div>
                <div class="feat-desc">One-click structured summaries of any conversation</div>
            </div>
            <div class="feat-card">
                <span class="feat-icon">🌡️</span>
                <div class="feat-title">Tunable Creativity</div>
                <div class="feat-desc">From deterministic to wildly creative responses</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("✦ Start a Conversation", use_container_width=True):
            new_chat(); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Active Chat
messages = st.session_state.conversations[st.session_state.current_chat]
chat_title = st.session_state.chat_titles.get(st.session_state.current_chat, "Conversation")

# Header
st.markdown(f"""
<div class="nc-header">
    <div class="nc-logo">{agent_info['emoji']}</div>
    <div class="nc-header-text">
        <h1>{st.session_state.agent_name}</h1>
        <p>{st.session_state.agent_tone} · {chat_title}</p>
    </div>
    <div class="nc-header-badge">{selected_model}</div>
</div>
""", unsafe_allow_html=True)

# Action bar
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    if st.button("📝 Summarize", use_container_width=True):
        if messages:
            with st.spinner("Generating summary..."):
                st.session_state.summary_content = summarize_chat(st.session_state.current_chat)
            st.session_state.show_summary = True
        else:
            st.warning("No messages to summarize.")
with col2:
    if st.button("📊 Analytics", use_container_width=True):
        st.session_state.show_analytics = not st.session_state.show_analytics
with col3:
    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.conversations[st.session_state.current_chat] = []
        st.session_state.show_summary = False
        st.session_state.show_analytics = False
        st.rerun()
with col4:
    if st.button("🆕 New Chat", use_container_width=True):
        new_chat(); st.rerun()

# Analytics Panel
if st.session_state.show_analytics and messages:
    analytics = get_chat_analytics(st.session_state.current_chat)
    if analytics:
        st.markdown(f"""
        <div style="background:var(--bg2);border:1px solid var(--border-bright);border-radius:16px;padding:20px;margin:16px 0;">
            <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;color:var(--accent);margin-bottom:16px;">📊 CONVERSATION ANALYTICS</div>
            <div class="analytics-grid">
                <div class="stat-card">
                    <div class="stat-value">{analytics['total_messages']}</div>
                    <div class="stat-label">Total Messages</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analytics['total_words']}</div>
                    <div class="stat-label">Total Words</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analytics['estimated_tokens']}</div>
                    <div class="stat-label">Est. Tokens</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analytics['user_messages']}</div>
                    <div class="stat-label">Your Messages</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analytics['avg_user_length']}</div>
                    <div class="stat-label">Avg You (words)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{analytics['avg_ai_length']}</div>
                    <div class="stat-label">Avg AI (words)</div>
                </div>
            </div>
            <div style="font-size:11px;color:var(--text2);font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-top:4px;">Top Keywords</div>
            <div class="word-tags">
                {"".join(f'<span class="word-tag">{w} <span style="color:var(--accent);font-size:10px;">×{c}</span></span>' for w,c in analytics['top_words'])}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Summary
if st.session_state.show_summary and st.session_state.summary_content:
    st.markdown(f"""
    <div class="summary-box">
        <div style="font-size:14.5px;color:var(--text0);line-height:1.7;">{st.session_state.summary_content}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("✕ Close Summary"):
        st.session_state.show_summary = False; st.rerun()

st.markdown("---")

# Messages
if not messages:
    suggestions = [
        ("💡", "Explain quantum computing simply"),
        ("🐍", "Write a Python web scraper"),
        ("✉️", "Draft a professional email"),
        ("🌍", "Top 5 underrated travel spots"),
        ("📈", "How do I learn machine learning?"),
        ("🎨", "Creative writing prompt ideas"),
    ]
    st.markdown("""
    <div class="empty-state">
        <span class="big-emoji">✦</span>
        <h2>What's on your mind?</h2>
        <p>Ask anything — I'm here to think, create, and explore with you.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="suggestion-chips">', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (icon, suggestion) in enumerate(suggestions):
        with cols[i % 3]:
            if st.button(f"{icon} {suggestion}", key=f"sugg_{i}", use_container_width=True):
                # Inject as message
                add_message("user", suggestion)
                with st.spinner(f"{st.session_state.agent_name} is thinking..."):
                    try:
                        resp = call_ai([{"role": "user", "content": suggestion}])
                    except Exception as e:
                        resp = f"⚠️ Error: {str(e)}"
                add_message("assistant", resp)
                auto_title_chat(st.session_state.current_chat)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        ts = msg.get("timestamp", "")
        tokens = estimate_tokens(content)
        
        if role == "user":
            st.markdown(f"""
            <div class="msg-row user">
                <div class="msg-avatar user-av">👤</div>
                <div class="msg-body">
                    <div class="msg-meta">You · {ts}</div>
                    <div class="msg-bubble user-bubble">{content}</div>
                    <div class="token-badge">~{tokens} tokens</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-row ai">
                <div class="msg-avatar ai-av">{agent_info['emoji']}</div>
                <div class="msg-body">
                    <div class="msg-meta">{st.session_state.agent_name} · {ts}</div>
                    <div class="msg-bubble ai-bubble">{content}</div>
                    <div class="token-badge">~{tokens} tokens</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Chat Input
prompt = st.chat_input(f"Message {st.session_state.agent_name}...")

if prompt:
    add_message("user", prompt)
    
    with st.spinner(f"{agent_info['emoji']} {st.session_state.agent_name} is thinking..."):
        try:
            payload = [{"role": m["role"], "content": m["content"]} for m in messages]
            response = call_ai(payload)
        except Exception as e:
            response = f"⚠️ Connection error: {str(e)}\n\nPlease check your OpenRouter API key in `.env`."

    add_message("assistant", response)
    auto_title_chat(st.session_state.current_chat)
    st.rerun()