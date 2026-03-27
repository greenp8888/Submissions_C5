import streamlit as st
import requests
import json
from datetime import datetime

# -------------------- CONFIG --------------------
OPENROUTER_API_KEY = st.secrets.get("OP_API_KEY", "")
MODEL = "openai/gpt-oss-120b"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# -------------------- STATE --------------------
if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "default"

# -------------------- HELPERS --------------------

def call_llm(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": messages
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        return f"Error: {response.text}"

    return response.json()["choices"][0]["message"]["content"]


def summarize_chat(messages):
    summary_prompt = [
        {"role": "system", "content": "Summarize this conversation briefly."},
        {"role": "user", "content": json.dumps(messages)}
    ]
    return call_llm(summary_prompt)


def export_chat(messages):
    return json.dumps(messages, indent=2)

# -------------------- UI SETTINGS --------------------

st.set_page_config(page_title="ChatGPT-like App", layout="wide")

mode = st.sidebar.selectbox("Theme", ["Light", "Dark"])
if mode == "Dark":
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

elif mode == "Light":
    st.markdown("""
        <style>
        .stApp {
            background-color: white;
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------

st.sidebar.title("Conversations")

new_chat_name = st.sidebar.text_input("New chat name")
if st.sidebar.button("Create Chat") and new_chat_name:
    st.session_state.conversations[new_chat_name] = []
    st.session_state.current_chat = new_chat_name

chat_list = list(st.session_state.conversations.keys())
if chat_list:
    selected = st.sidebar.selectbox("Select Chat", chat_list)
    st.session_state.current_chat = selected

# -------------------- MAIN CHAT --------------------

st.title("ChatGPT-like App")

chat = st.session_state.conversations.get(st.session_state.current_chat, [])

for msg in chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    chat.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    response = call_llm(chat)

    chat.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.conversations[st.session_state.current_chat] = chat

# -------------------- ACTIONS --------------------

st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button("Summarize Conversation"):
        summary = summarize_chat(chat)
        st.subheader("Summary")
        st.write(summary)

with col2:
    if st.button("Export Conversation"):
        export_data = export_chat(chat)
        st.download_button(
            label="Download JSON",
            data=export_data,
            file_name=f"chat_{datetime.now().isoformat()}.json",
            mime="application/json"
        )
