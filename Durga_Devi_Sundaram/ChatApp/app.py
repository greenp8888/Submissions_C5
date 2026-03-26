import streamlit as st
import requests
import time
import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pulse AI",
    page_icon="〇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary:    #050d1a;
    --bg-secondary:  #08142b;
    --bg-card:       #0d1e38;
    --bg-hover:      #112444;
    --accent:        #00bfbf;
    --accent-soft:   #40d9d9;
    --accent-glow:   rgba(0,191,191,0.15);
    --gold:          #f0b429;
    --gold-soft:     #f7ca5e;
    --gold-glow:     rgba(240,180,41,0.15);
    --text-primary:  #e8f4ff;
    --text-secondary:#7fa8cc;
    --text-muted:    #3a5a7a;
    --border:        #1a3050;
    --border-soft:   #0f2040;
    --radius:        14px;
    --radius-sm:     8px;
}

* { font-family: 'Sora', sans-serif; box-sizing: border-box; }
code, pre { font-family: 'JetBrains Mono', monospace !important; }

.stApp { background: var(--bg-primary); color: var(--text-primary); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container { padding: 1.2rem 0.9rem !important; }

.sidebar-section {
    font-size: 9.5px; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--text-muted);
    margin: 1.3rem 0 0.45rem;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid var(--border-soft);
}

/* Inputs */
.stTextInput input, .stTextArea textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-size: 13px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}
div[data-baseweb="select"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-size: 13px !important;
}
[data-baseweb="popover"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; }
[role="option"] { background: var(--bg-card) !important; color: var(--text-primary) !important; font-size: 13px !important; }
[role="option"]:hover { background: var(--bg-hover) !important; }

/* Buttons */
.stButton button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-size: 12.5px !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    background: var(--bg-hover) !important;
    border-color: var(--accent) !important;
    color: var(--accent-soft) !important;
}
.stDownloadButton button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-size: 12.5px !important;
}
.stDownloadButton button:hover {
    border-color: var(--gold) !important;
    color: var(--gold-soft) !important;
}

/* Checkbox / labels */
.stCheckbox label { color: var(--text-secondary) !important; font-size: 12.5px !important; }
.stSelectbox label, .stSlider label, .stTextInput label { color: var(--text-secondary) !important; font-size: 12.5px !important; }

/* Radio — avatar picker */
.stRadio > div { gap: 4px !important; flex-wrap: wrap !important; }
.stRadio > label { color: var(--text-secondary) !important; font-size: 12.5px !important; }

/* Expander */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stExpander"] summary { color: var(--text-secondary) !important; font-size: 12.5px !important; }

/* ── Session stat rows ── */
.stat-row {
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 7px 11px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    margin-bottom: 5px;
}
.stat-row-label { font-size: 10px; color: var(--text-muted); letter-spacing: 0.07em; text-transform: uppercase; }
.stat-row-value { font-size: 13px; font-weight: 600; color: var(--accent-soft); font-variant-numeric: tabular-nums; }
.stat-row-value.gold { color: var(--gold-soft); }

/* ── Top bar ── */
.top-bar {
    background: linear-gradient(180deg, var(--bg-secondary) 0%, transparent 100%);
    border-bottom: 1px solid var(--border);
    padding: 15px 28px;
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
}

/* ── Chat area ── */
.chat-container { max-width: 780px; margin: 0 auto; padding: 2rem 1.5rem 9rem; }

/* ── Message wrappers ── */
.msg-wrapper { display: flex; gap: 12px; margin-bottom: 22px; animation: msgIn 0.22s ease; }
@keyframes msgIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.msg-wrapper.user { flex-direction: row-reverse; }

.avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
}
.avatar.ai { background: linear-gradient(135deg,#00bfbf,#005f6b); box-shadow: 0 0 12px rgba(0,191,191,0.3); }
.avatar.user { background: var(--bg-card); border: 1px solid var(--border); }

.bubble {
    max-width: 72%; background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 0 var(--radius) var(--radius) var(--radius);
    padding: 13px 17px; font-size: 14px; line-height: 1.72; color: var(--text-primary);
}
.bubble.user {
    background: linear-gradient(135deg,rgba(0,191,191,0.07),rgba(0,80,120,0.1));
    border-color: rgba(0,191,191,0.22);
    border-radius: var(--radius) 0 var(--radius) var(--radius);
}
.bubble-meta { font-size: 10.5px; color: var(--text-muted); margin-top: 5px; }

/* ── Mood badge ── */
.mood-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: var(--bg-hover); border: 1px solid var(--border);
    border-radius: 20px; padding: 2px 9px 2px 7px;
    font-size: 10.5px; color: var(--text-muted); margin-top: 6px;
}
.mood-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }

/* ── Welcome ── */
.welcome-hero { text-align: center; padding: 4.5rem 2rem 2rem; }
.welcome-hero .glyph {
    font-size: 52px;
    background: linear-gradient(135deg, #00bfbf, #f0b429, #40d9d9);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: block; margin-bottom: 1.1rem;
    animation: breathe 3.5s ease-in-out infinite;
}
@keyframes breathe { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.75;transform:scale(0.96)} }
.welcome-hero h1 { font-size: 2.2rem; font-weight: 700; letter-spacing: -0.04em; margin: 0 0 0.55rem; }
.welcome-hero p { font-size: 14.5px; color: var(--text-secondary); max-width: 460px; margin: 0 auto 2.2rem; }

/* Input bar */
.input-bar-wrap {
    position: fixed; bottom: 0; left: 0; right: 0;
    background: linear-gradient(0deg, var(--bg-primary) 55%, transparent);
    padding: 0.8rem 1.5rem 1.4rem; z-index: 50;
}
.input-bar-inner { max-width: 780px; margin: 0 auto; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
MOOD_COLORS = {
    "Positive":    "#00bfbf",
    "Neutral":     "#7fa8cc",
    "Negative":    "#f87171",
    "Inquisitive": "#f0b429",
}

AVATAR_OPTIONS = [
    ("🤖", "Robot"),
    ("🧙", "Wizard"),
    ("🦊", "Fox"),
    ("👾", "Alien"),
    ("🎩", "Classy"),
]

# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "groups":        {"General": []},
        "active_group":  "General",
        "session_start": time.time(),
        "total_tokens":  0,
        "api_key":       "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ── Helpers ───────────────────────────────────────────────────────────────────
def detect_mood(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["great","thanks","love","awesome","perfect","happy","good","nice","excellent","amazing","wonderful"]):
        return "Positive"
    if any(w in t for w in ["why","how","what","when","where","?"]):
        return "Inquisitive"
    if any(w in t for w in ["bad","wrong","error","fail","broken","hate","terrible","frustrated","awful"]):
        return "Negative"
    return "Neutral"

def current_msgs():
    return st.session_state.groups.get(st.session_state.active_group, [])

def add_msg(role, content, tokens=0):
    grp = st.session_state.active_group
    if grp not in st.session_state.groups:
        st.session_state.groups[grp] = []
    st.session_state.groups[grp].append({
        "role":    role,
        "content": content,
        "time":    datetime.datetime.now().strftime("%H:%M:%S"),
        "date":    datetime.datetime.now().strftime("%b %d"),
        "tokens":  tokens,
        "mood":    detect_mood(content) if role == "user" else None,
    })
    st.session_state.total_tokens += tokens

def build_system_prompt(cfg) -> str:
    style_map = {
        "Friendly":     "warm, approachable, and conversational. Use casual language and light humor when appropriate.",
        "Professional": "precise, structured, and formal. Use clear formatting, cite reasoning, stay objective.",
        "Creative":     "inventive, vivid, and expressive. Use metaphors, unexpected angles, and imaginative language.",
    }
    warmth_map = {1:"cold and terse", 2:"neutral", 3:"warm", 4:"very warm and encouraging", 5:"extremely warm and enthusiastic"}
    return (
        f"You are {cfg['name']}, an AI assistant. "
        f"Style: {style_map[cfg['style']]} "
        f"Warmth: {warmth_map.get(cfg['warmth'],'warm')}. "
        f"Tone: {cfg['tone']}. "
        f"{'Use emojis occasionally.' if cfg['emoji'] else 'No emojis.'} "
        "Be helpful, honest, and concise."
    )

def call_openrouter(messages, cfg, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://pulse-ai.app",
        "X-Title":       "Pulse AI",
    }
    payload = {
        "model":       cfg.get("model", "openai/gpt-4o-mini"),
        "messages":    [{"role":"system","content":build_system_prompt(cfg)}] + messages,
        "temperature": 0.7,
    }
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data    = r.json()
        content = data["choices"][0]["message"]["content"]
        tokens  = data.get("usage", {}).get("total_tokens", len(content.split()) * 2)
        return content, tokens
    except requests.exceptions.HTTPError:
        return f"❌ API Error {r.status_code}: {r.text[:200]}", 0
    except Exception as e:
        return f"❌ Error: {str(e)}", 0

def export_chat(msgs, group_name):
    lines = [
        "Pulse AI — Chat Export",
        f"Group: {group_name}",
        f"Exported: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50, ""
    ]
    for m in msgs:
        ts = f" [{m['time']}]" if m.get("time") else ""
        lines.append(f"[{m['role'].upper()}]{ts}\n{m['content']}\n")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # Logo
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.3rem">
        <div style="width:36px;height:36px;
                    background:linear-gradient(135deg,#00bfbf,#006f6f);
                    border-radius:10px;display:flex;align-items:center;
                    justify-content:center;font-size:18px;
                    box-shadow:0 0 16px rgba(0,191,191,0.3);">〇</div>
        <div>
            <div style="font-weight:700;font-size:17px;color:#e8f4ff;letter-spacing:-0.02em;">Pulse</div>
            <div style="font-size:9px;color:#3a5a7a;letter-spacing:0.18em;margin-top:1px;">FLOW WITH ME...</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Connection
    st.markdown('<div class="sidebar-section">Connection</div>', unsafe_allow_html=True)
    api_key_input = st.text_input("OpenRouter API Key", type="password",
                                   value=st.session_state.api_key,
                                   placeholder="sk-or-...",
                                   help="Get yours at openrouter.ai")
    if api_key_input:
        st.session_state.api_key = api_key_input

    model_choice = st.selectbox("Model", [
        "openai/gpt-4o-mini",
        "openai/gpt-4o",
        "anthropic/claude-3.5-haiku",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-flash-1.5",
        "meta-llama/llama-3.3-70b-instruct",
    ])

    # Assistant
    st.markdown('<div class="sidebar-section">Assistant</div>', unsafe_allow_html=True)
    assistant_name = st.text_input("Assistant Name", value="Pulse", placeholder="e.g. Aria, Sage, Max")
    response_style = st.selectbox("Response Style", ["Friendly", "Professional", "Creative"])

    # Chat Groups
    st.markdown('<div class="sidebar-section">Chat Groups</div>', unsafe_allow_html=True)
    for g in list(st.session_state.groups.keys()):
        count     = len(st.session_state.groups[g])
        is_active = (g == st.session_state.active_group)
        c1, c2    = st.columns([4, 1])
        with c1:
            if st.button(f"{'▸ ' if is_active else '  '}{g}  ({count})", key=f"grp_{g}", use_container_width=True):
                st.session_state.active_group = g
                st.rerun()
        with c2:
            if g != "General" and st.button("✕", key=f"del_{g}"):
                del st.session_state.groups[g]
                if st.session_state.active_group == g:
                    st.session_state.active_group = "General"
                st.rerun()

    new_group = st.text_input("", placeholder="New group name…", label_visibility="collapsed", key="ng")
    if st.button("＋ Create Group", use_container_width=True):
        ng = new_group.strip()
        if ng and ng not in st.session_state.groups:
            st.session_state.groups[ng] = []
            st.session_state.active_group = ng
            st.rerun()

    # Chat Settings
    st.markdown('<div class="sidebar-section">Chat Settings</div>', unsafe_allow_html=True)
    max_history     = st.slider("Max chat history", 5, 50, 20)
    show_timestamps = st.checkbox("Show timestamps", value=True)
    show_mood       = st.checkbox("Show mood detection", value=True)

    # Personalization
    st.markdown('<div class="sidebar-section">Personalization</div>', unsafe_allow_html=True)
    with st.expander("⚙  Customize your experience"):
        use_emoji  = st.checkbox("Emojis in responses", value=True)
        warmth     = st.slider("Warmth level", 1, 5, 3, help="1=terse · 5=very warm")
        base_style = st.selectbox("Base style", ["Conversational","Academic","Casual","Technical","Storytelling"])
        tone       = st.selectbox("Tone", ["Optimistic","Balanced","Analytical","Empathetic","Direct"])

        st.markdown("<div style='font-size:12px;color:#7fa8cc;margin:10px 0 5px;font-weight:500;'>Your Avatar</div>", unsafe_allow_html=True)

        # Avatar radio — 5 curated options displayed as emoji + label
        avatar_labels = [f"{e}  {lbl}" for e, lbl in AVATAR_OPTIONS]
        avatar_idx    = st.radio(
            "Pick your avatar",
            options=range(len(AVATAR_OPTIONS)),
            format_func=lambda i: avatar_labels[i],
            index=0,
            label_visibility="collapsed",
        )
        user_emoji = AVATAR_OPTIONS[avatar_idx][0]

    # Session Stats — vertical stacked rows
    st.markdown('<div class="sidebar-section">Session Stats</div>', unsafe_allow_html=True)
    msgs_all       = current_msgs()
    user_msg_count = sum(1 for m in msgs_all if m["role"] == "user")
    elapsed        = int(time.time() - st.session_state.session_start)
    h, rem         = divmod(elapsed, 3600)
    m_, s          = divmod(rem, 60)
    duration_str   = f"{h:02d}:{m_:02d}:{s:02d}"

    st.markdown(f"""
    <div class="stat-row">
        <span class="stat-row-label">⏱ Duration</span>
        <span class="stat-row-value">{duration_str}</span>
    </div>
    <div class="stat-row">
        <span class="stat-row-label">💬 Messages Sent</span>
        <span class="stat-row-value">{user_msg_count}</span>
    </div>
    <div class="stat-row">
        <span class="stat-row-label">🔢 Tokens Used</span>
        <span class="stat-row-value gold">{st.session_state.total_tokens:,}</span>
    </div>
    """, unsafe_allow_html=True)

    # Actions
    st.markdown('<div class="sidebar-section">Actions</div>', unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        if st.button("🗑  Clear", use_container_width=True):
            st.session_state.groups[st.session_state.active_group] = []
            st.rerun()
    with cb:
        st.download_button(
            "⬇  Export",
            export_chat(current_msgs(), st.session_state.active_group),
            file_name=f"pulse_{st.session_state.active_group}_{datetime.date.today()}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════
cfg = {
    "name":       assistant_name or "Pulse",
    "style":      response_style,
    "model":      model_choice,
    "emoji":      use_emoji,
    "warmth":     warmth,
    "tone":       tone,
    "base_style": base_style,
}

# Top bar
st.markdown(f"""
<div class="top-bar">
    <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:32px;height:32px;background:linear-gradient(135deg,#00bfbf,#006f6f);
                    border-radius:9px;display:flex;align-items:center;justify-content:center;
                    font-size:15px;box-shadow:0 0 12px rgba(0,191,191,0.3);">〇</div>
        <div>
            <div style="font-size:17px;font-weight:700;letter-spacing:-0.02em;color:#e8f4ff;line-height:1.1;">Pulse</div>
            <div style="font-size:8.5px;color:#3a5a7a;letter-spacing:0.18em;">FLOW WITH ME...</div>
        </div>
        <div style="height:16px;width:1px;background:#1a3050;margin:0 4px;"></div>
        <div style="font-size:12px;color:#3a5a7a;">{st.session_state.active_group} · {response_style}</div>
    </div>
    <div style="display:flex;align-items:center;gap:7px;">
        <div style="width:8px;height:8px;border-radius:50%;background:#00bfbf;
                    box-shadow:0 0 10px rgba(0,191,191,0.8);"></div>
        <span style="font-size:11px;color:#3a5a7a;">{cfg['name']} ready</span>
    </div>
</div>
""", unsafe_allow_html=True)

msgs = current_msgs()

# ── Chat display ──────────────────────────────────────────────────────────────
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

if not msgs:
    hour     = datetime.datetime.now().hour
    greeting = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
    st.markdown(f"""
    <div class="welcome-hero">
        <span class="glyph">〇</span>
        <h1>Good {greeting}.</h1>
        <p>I'm <strong>{cfg['name']}</strong> — your {response_style.lower()} AI. Ready to flow.</p>
    </div>
    """, unsafe_allow_html=True)

    suggestions = [
        ("✍", "Help me write something"),
        ("💡", "Brainstorm an idea"),
        ("🔍", "Explain a concept"),
        ("📊", "Analyze some data"),
        ("🐛", "Debug my code"),
        ("🌍", "Teach me something fascinating"),
    ]
    cols = st.columns(3)
    for i, (icon, label) in enumerate(suggestions):
        with cols[i % 3]:
            if st.button(f"{icon}  {label}", key=f"sug_{i}", use_container_width=True):
                add_msg("user", label)
                st.rerun()

else:
    for msg in msgs[-max_history:]:
        is_user      = msg["role"] == "user"
        bubble_cls   = "user" if is_user else "ai"
        avatar_cls   = "user" if is_user else "ai"
        wrapper_cls  = "user" if is_user else ""
        avatar_icon  = user_emoji if is_user else "〇"

        # Timestamp
        ts_html = ""
        if show_timestamps and msg.get("time"):
            ts_html = f'<div class="bubble-meta">⏱ {msg["date"]} · {msg["time"]}</div>'

        # Safe-escape content
        content_safe = (
            msg["content"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )

        # Mood badge — only for user messages, built purely with inline styles
        # so it renders correctly regardless of which group is active
        mood_html = ""
        if show_mood and is_user and msg.get("mood"):
            mood_label = msg["mood"]
            mood_color = MOOD_COLORS.get(mood_label, "#7fa8cc")
            mood_html = (
                '<div style="display:inline-flex;align-items:center;gap:5px;'
                'background:#112444;border:1px solid #1a3050;border-radius:20px;'
                'padding:2px 9px 2px 7px;font-size:10.5px;color:#3a5a7a;margin-top:6px;">'
                f'<div style="width:7px;height:7px;border-radius:50%;'
                f'background:{mood_color};flex-shrink:0;"></div>'
                f'{mood_label}'
                '</div>'
            )

        # Single st.markdown call per message — keeps HTML intact across all groups
        st.markdown(
            f'<div class="msg-wrapper {wrapper_cls}">'
            f'<div class="avatar {avatar_cls}">{avatar_icon}</div>'
            f'<div>'
            f'<div class="bubble {bubble_cls}">{content_safe}</div>'
            f'{ts_html}'
            f'{mood_html}'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown('</div>', unsafe_allow_html=True)

# ── Input bar ─────────────────────────────────────────────────────────────────
st.markdown('<div class="input-bar-wrap"><div class="input-bar-inner">', unsafe_allow_html=True)
user_input = st.chat_input(placeholder=f"Message {cfg['name']}…")
st.markdown('</div></div>', unsafe_allow_html=True)

# ── Handle send ───────────────────────────────────────────────────────────────
if user_input and user_input.strip():
    if not st.session_state.api_key:
        st.warning("⚠  Enter your OpenRouter API key in the sidebar to start chatting.")
    else:
        add_msg("user", user_input.strip())
        history_ctx  = current_msgs()[-(max_history):]
        api_messages = [{"role": m["role"], "content": m["content"]} for m in history_ctx]

        with st.spinner(f"{cfg['name']} is thinking…"):
            response, tokens = call_openrouter(api_messages, cfg, st.session_state.api_key)

        add_msg("assistant", response, tokens)
        st.rerun()
