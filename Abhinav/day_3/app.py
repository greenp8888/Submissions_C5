import streamlit as st
import requests
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

# ---------------- CONFIG ----------------
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openai/gpt-oss-120b"

st.set_page_config(layout="wide")

# ---------------- SESSION ----------------
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat" not in st.session_state:
    chat_id = str(uuid.uuid4())
    st.session_state.current_chat = chat_id
    st.session_state.chats[chat_id] = []

# ---------------- LLM ----------------
def generate_response(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json", 
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
    }

    res = requests.post(url, headers=headers, json=payload)

    if res.status_code != 200:
        return f"Error: {res.text}"

    return res.json()["choices"][0]["message"]["content"]

# ---------------- UI STYLE ----------------
st.markdown("""
<style>
body { background-color: #0e1117; color: white; }
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("💬 Conversations")

if st.sidebar.button("+ New Chat"):
    chat_id = str(uuid.uuid4())
    st.session_state.current_chat = chat_id
    st.session_state.chats[chat_id] = []

for chat_id, msgs in st.session_state.chats.items():
    title = msgs[0]["content"][:20] if msgs else "New Chat"
    if st.sidebar.button(title, key=chat_id):
        st.session_state.current_chat = chat_id

# ---------------- MAIN ----------------
st.title("🤖 ChatGPT Clone")

messages = st.session_state.chats[st.session_state.current_chat]

# Display chat
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- INPUT ----------------
if prompt := st.chat_input("Type your message..."):
    messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        response = generate_response(messages)

    messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)

# ---------------- SUMMARIZE ----------------
if st.button("🧠 Summarize Conversation"):
    summary_prompt = messages + [
        {"role": "user", "content": "Summarize this conversation briefly."}
    ]

    summary = generate_response(summary_prompt)
    st.info(summary)