import streamlit as st
import json
import os
import uuid
import requests
from datetime import datetime

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="ChatGPT Clone", layout="wide")
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
MODEL = "openai/gpt-4o-mini"

SESSIONS_DIR = "sessions"
INDEX_FILE = f"{SESSIONS_DIR}/index.json"
DEFAULT_SESSION = "default"

os.makedirs(SESSIONS_DIR, exist_ok=True)

# ==============================
# STORAGE HELPERS
# ==============================
def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r") as f:
            return json.load(f)
    return {}

def save_index(data):
    with open(INDEX_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_session(session_id):
    path = f"{SESSIONS_DIR}/{session_id}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"title": session_id, "messages": []}

def save_session(session_id, data):
    path = f"{SESSIONS_DIR}/{session_id}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ==============================
# INIT INDEX + DEFAULT
# ==============================
index_data = load_index()

if DEFAULT_SESSION not in index_data:
    index_data[DEFAULT_SESSION] = {
        "title": "Ritesh ChatBot",
        "pinned": True,
        "created_at": str(datetime.now())
    }
    save_session(DEFAULT_SESSION, {"title": "Ritesh Chatbot", "messages": []})
    save_index(index_data)

# ==============================
# INIT SESSION STATE
# ==============================
if "current_session" not in st.session_state:
    st.session_state.current_session = DEFAULT_SESSION

if st.session_state.current_session not in index_data:
    st.session_state.current_session = DEFAULT_SESSION

if "chat_data" not in st.session_state:
    st.session_state.chat_data = load_session(st.session_state.current_session)

# ==============================
# OPENROUTER API
# ==============================
def get_response(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Streamlit Chat App"
    }

    payload = {
        "model": MODEL,
        "messages": messages
    }

    res = requests.post(url, headers=headers, json=payload)

    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {res.text}"

# ==============================
# SUMMARY
# ==============================
def summarize_chat(messages):
    prompt = [
        {"role": "system", "content": "Summarize in 5 bullet points."},
        {"role": "user", "content": str(messages)}
    ]
    return get_response(prompt)

# ==============================
# CSS
# ==============================
st.markdown("""
<style>
.chat-container { max-width: 800px; margin: auto; }
.user-msg { background:#DCF8C6; padding:10px; border-radius:10px; margin:5px; text-align:right;}
.bot-msg { background:#F1F0F0; padding:10px; border-radius:10px; margin:5px; text-align:left;}
</style>
""", unsafe_allow_html=True)

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title("📁 Chats")

# 🔍 Search
search = st.sidebar.text_input("🔍 Search")

# Filter
filtered = []
for sid, meta in index_data.items():
    if search.lower() in meta["title"].lower():
        filtered.append((sid, meta))

# Sort (Pinned first)
filtered = sorted(filtered, key=lambda x: (not x[1]["pinned"], x[1]["created_at"]))

# Render chats
for sid, meta in filtered:
    col1, col2 = st.sidebar.columns([4,1])

    if col1.button(meta["title"], key=sid):
        st.session_state.current_session = sid
        st.session_state.chat_data = load_session(sid)
        st.rerun()

    if meta["pinned"]:
        col2.markdown("⭐")

# ==============================
# NEW CHAT
# ==============================
st.sidebar.markdown("---")
new_name = st.sidebar.text_input("New Chat Name")

if st.sidebar.button("➕ Create Chat"):
    if not new_name.strip():
        st.sidebar.warning("Enter valid name")
    else:
        sid = new_name.lower().replace(" ", "_")

        if sid in index_data:
            st.sidebar.warning("Already exists")
        else:
            save_session(sid, {"title": new_name, "messages": []})

            index_data[sid] = {
                "title": new_name,
                "pinned": False,
                "created_at": str(datetime.now())
            }
            save_index(index_data)

            st.session_state.current_session = sid
            st.session_state.chat_data = {"title": new_name, "messages": []}
            st.rerun()

# ==============================
# PIN
# ==============================
if st.sidebar.button("⭐ Pin / Unpin"):
    sid = st.session_state.current_session
    index_data[sid]["pinned"] = not index_data[sid]["pinned"]
    save_index(index_data)
    st.rerun()

# ==============================
# DELETE
# ==============================
if st.sidebar.button("🗑 Delete"):
    sid = st.session_state.current_session

    if sid == DEFAULT_SESSION:
        st.sidebar.warning("Default cannot be deleted")
    else:
        os.remove(f"{SESSIONS_DIR}/{sid}.json")
        del index_data[sid]
        save_index(index_data)

        st.session_state.current_session = DEFAULT_SESSION
        st.session_state.chat_data = load_session(DEFAULT_SESSION)
        st.rerun()

# ==============================
# MAIN UI
# ==============================
st.title(st.session_state.chat_data["title"])

st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state.chat_data["messages"]:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg">{msg["content"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# INPUT
# ==============================
prompt = st.chat_input("Type message...")

if prompt:
    st.session_state.chat_data["messages"].append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        reply = get_response(st.session_state.chat_data["messages"])

    st.session_state.chat_data["messages"].append({"role": "assistant", "content": reply})

    save_session(st.session_state.current_session, st.session_state.chat_data)
    st.rerun()

# ==============================
# EXPORT
# ==============================
st.sidebar.markdown("---")

if st.sidebar.button("📥 Export JSON"):
    st.download_button("Download JSON",
        json.dumps(st.session_state.chat_data, indent=2),
        "chat.json"
    )

if st.sidebar.button("📄 Export TXT"):
    txt = "\n\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_data["messages"]])
    st.download_button("Download TXT", txt, "chat.txt")

# ==============================
# SUMMARY
# ==============================
if st.sidebar.button("🧠 Summary"):
    with st.spinner("Summarizing..."):
        summary = summarize_chat(st.session_state.chat_data["messages"])
    st.sidebar.write(summary)
