import streamlit as st
import requests
import json
import os
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_OPTIONS = {
    "openai/gpt-oss-120b": "GPT OSS 120B",
    "meta-llama/llama-3.1-8b-instruct": "Llama 3.1 8B",
    "microsoft/phi-4-mini": "Phi-4 Mini",
    "qwen/qwen-2.5-7b-instruct": "Qwen 2.5 7B",
    "google/gemma-3-4b-it": "Gemma 3 4B",
}

CONVERSATIONS_FILE = "conversations.json"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ---------------------------------------------------------------------------
# Data Persistence Functions
# ---------------------------------------------------------------------------

def load_conversations() -> dict:
    """Load conversations from JSON file. Creates file if missing."""
    if not os.path.exists(CONVERSATIONS_FILE):
        return {}
    try:
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("conversations", {})
    except (json.JSONDecodeError, IOError):
        # Corrupted file — back it up and start fresh
        backup = f"{CONVERSATIONS_FILE}.bak"
        if os.path.exists(CONVERSATIONS_FILE):
            os.replace(CONVERSATIONS_FILE, backup)
        return {}


def save_conversations(conversations: dict) -> None:
    """Persist conversations dict to JSON file."""
    data = {"conversations": conversations}
    tmp = CONVERSATIONS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONVERSATIONS_FILE)


def generate_chat_id() -> str:
    """Generate a unique chat ID from timestamp + random suffix."""
    return f"chat_{int(time.time())}_{os.urandom(4).hex()}"


def init_session_state() -> None:
    """Initialize all session state keys with defaults."""
    if "initialized" in st.session_state:
        return

    conversations = load_conversations()

    st.session_state.api_key = ""
    st.session_state.messages = {
        cid: conv["messages"] for cid, conv in conversations.items()
    }
    st.session_state.chat_titles = {
        cid: conv["title"] for cid, conv in conversations.items()
    }
    st.session_state.chat_created_at = {
        cid: conv.get("created_at", datetime.now(timezone.utc).isoformat())
        for cid, conv in conversations.items()
    }
    st.session_state.current_chat_id = (
        next(iter(conversations)) if conversations else None
    )
    st.session_state.selected_model = list(MODEL_OPTIONS.keys())[0]
    st.session_state.temperature = 0.7
    st.session_state.is_generating = False
    st.session_state.stop_generation = False
    st.session_state.pending_message = None
    st.session_state.streaming_response = ""
    st.session_state.initialized = True


def create_new_chat(title: str = "New Chat") -> str:
    """Create a new chat and return its ID."""
    chat_id = generate_chat_id()
    st.session_state.messages[chat_id] = []
    st.session_state.chat_titles[chat_id] = title
    st.session_state.current_chat_id = chat_id
    st.session_state.chat_created_at[chat_id] = datetime.now(timezone.utc).isoformat()
    save_all_conversations()
    return chat_id


def delete_chat(chat_id: str) -> None:
    """Delete a chat by ID."""
    st.session_state.messages.pop(chat_id, None)
    st.session_state.chat_titles.pop(chat_id, None)
    st.session_state.chat_created_at.pop(chat_id, None)
    if st.session_state.current_chat_id == chat_id:
        remaining = list(st.session_state.messages.keys())
        st.session_state.current_chat_id = remaining[0] if remaining else None
    save_all_conversations()


def save_all_conversations() -> None:
    """Build conversations dict from session state and persist."""
    conversations = {}
    for cid, msgs in st.session_state.messages.items():
        conversations[cid] = {
            "id": cid,
            "title": st.session_state.chat_titles.get(cid, "Untitled"),
            "created_at": st.session_state.chat_created_at.get(cid, datetime.now(timezone.utc).isoformat()),
            "messages": msgs,
        }
    save_conversations(conversations)


# ---------------------------------------------------------------------------
# Settings Dialog
# ---------------------------------------------------------------------------

@st.dialog("Settings")
def settings_dialog() -> None:
    """Render the settings modal dialog."""
    api_key = st.text_input(
        "OpenRouter API key",
        value=st.session_state.api_key,
        type="password",
        placeholder="sk-or-...",
    )

    temperature = st.slider(
        "Response temperature",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.temperature,
        step=0.1,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", use_container_width=True):
            st.session_state.api_key = api_key
            st.session_state.temperature = temperature
            st.rerun()
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()


# ---------------------------------------------------------------------------
# Render Functions
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    """Render the sidebar with model selection, new chat, and conversation list."""
    with st.sidebar:
        st.selectbox(
            "Model",
            options=list(MODEL_OPTIONS.keys()),
            format_func=lambda x: MODEL_OPTIONS[x],
            key="selected_model",
        )

        if st.button("➕ New chat", use_container_width=True):
            create_new_chat()
            st.rerun()

        st.caption("Conversations")

        for chat_id in list(st.session_state.chat_titles.keys()):
            title = st.session_state.chat_titles[chat_id]
            is_active = chat_id == st.session_state.current_chat_id
            col1, col2 = st.columns([4, 1])
            with col1:
                btn_type = "primary" if is_active else "secondary"
                if st.button(title, key=f"chat_{chat_id}", use_container_width=True, type=btn_type):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with col2:
                if st.button("🗑", key=f"del_{chat_id}"):
                    delete_chat(chat_id)
                    st.rerun()


def render_header() -> None:
    """Render the header with title, active model badge, and settings button."""
    col1, col2 = st.columns([7, 1])
    with col1:
        model_label = MODEL_OPTIONS.get(st.session_state.selected_model, "")
        st.title(f"ED GPT  :violet[{model_label}]")
    with col2:
        if st.button("⚙️", help="Settings"):
            settings_dialog()


def render_messages() -> None:
    """Display chat messages for the current conversation."""
    chat_id = st.session_state.current_chat_id
    if chat_id is None:
        st.info("No conversations yet. Click **➕ New chat** in the sidebar to begin.", icon=":material/chat:")
        return

    title = st.session_state.chat_titles.get(chat_id, "Untitled")
    st.subheader(title)

    messages = st.session_state.messages.get(chat_id, [])

    if not messages:
        st.caption(":material/keyboard: Type a message below to start the conversation.")
        return

    for msg in messages:
        avatar = ":material/smart_toy:" if msg["role"] == "assistant" else ":material/person:"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])


def call_openrouter(messages: list[dict], model: str, temperature: float, api_key: str):
    """Call OpenRouter API with streaming. Yields text chunks."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ed-gpt.hf.space",
        "X-Title": "ED GPT",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60,
        )

        if response.status_code == 401:
            yield "[Error] Invalid API key. Please check your key in Settings."
            return
        if response.status_code == 429:
            yield "[Error] Rate limited or out of credits. Please wait or check your OpenRouter balance."
            return
        if response.status_code != 200:
            yield f"[Error] API returned status {response.status_code}. Try a different model."
            return

        response.encoding = "utf-8"
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[len("data: "):]
            if data_str.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content
            except json.JSONDecodeError:
                continue

    except requests.exceptions.Timeout:
        yield "[Error] Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        yield "[Error] Could not connect to OpenRouter. Check your internet connection."
    except requests.exceptions.RequestException as e:
        yield f"[Error] Request failed: {e}"


def render_chat_input() -> None:
    """Render the chat input box and handle sending messages."""
    chat_id = st.session_state.current_chat_id
    if chat_id is None:
        return

    # Two-run approach for stop button:
    # Run 1 — user submits → store pending_message, set is_generating=True, rerun
    # Run 2 — is_generating=True → stop button rendered above, then we stream here
    pending = st.session_state.get("pending_message")
    if pending and st.session_state.get("is_generating", False):
        user_input = pending
        st.session_state.pending_message = None
    else:
        user_input = st.chat_input("Type your message...")
        if not user_input or not user_input.strip():
            return
        if not st.session_state.api_key:
            st.toast("Please set your API key in Settings first.", icon="🔑")
            return
        st.session_state.pending_message = user_input.strip()
        st.session_state.stop_generation = False
        st.session_state.is_generating = True
        st.rerun()
        return

    # If stop was clicked before streaming began, cancel cleanly
    if st.session_state.get("stop_generation", False):
        st.session_state.stop_generation = False
        st.session_state.is_generating = False
        return

    # Add user message
    st.session_state.messages[chat_id].append(
        {"role": "user", "content": user_input}
    )

    # Auto-title if this is the first message in the chat
    if len(st.session_state.messages[chat_id]) == 1:
        auto_title = user_input[:40] + ("..." if len(user_input) > 40 else "")
        st.session_state.chat_titles[chat_id] = auto_title

    # Build API message list
    api_messages = [{"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[chat_id]]

    # Display user message and stream AI response
    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=":material/smart_toy:"):
        placeholder = st.empty()
        st.session_state.streaming_response = ""
        for chunk in call_openrouter(
            messages=api_messages,
            model=st.session_state.selected_model,
            temperature=st.session_state.temperature,
            api_key=st.session_state.api_key,
        ):
            st.session_state.streaming_response += chunk
            placeholder.markdown(st.session_state.streaming_response + "▌")
        placeholder.markdown(st.session_state.streaming_response)
        response_text = st.session_state.streaming_response
        st.session_state.streaming_response = ""

    st.session_state.is_generating = False

    # Save AI response (skip if it's an error message)
    if response_text.startswith("[Error]"):
        # Remove the user message we already appended since the request failed
        st.session_state.messages[chat_id].pop()
        if not st.session_state.messages[chat_id]:
            st.session_state.chat_titles[chat_id] = "New Chat"
        st.rerun()
    elif response_text:
        st.session_state.messages[chat_id].append(
            {"role": "assistant", "content": response_text}
        )
        save_all_conversations()
        st.rerun()
    else:
        # No response at all - remove the user message
        st.session_state.messages[chat_id].pop()
        st.rerun()


def render_chat_actions() -> None:
    """Render stop button (during generation) and Export, Clear, Summarize buttons."""
    chat_id = st.session_state.current_chat_id
    if chat_id is None:
        return

    # Stop button — visible while the model is generating.
    # Due to Streamlit's synchronous execution model, clicking this after the stream
    # has already started will discard the response once it completes rather than
    # interrupting it mid-flight. True mid-stream cancellation requires threading.
    if st.session_state.get("is_generating", False):
        if st.button("⏹ Stop generating", use_container_width=True, type="primary"):
            st.session_state.stop_generation = True
            st.session_state.is_generating = False
            st.rerun()

    messages = st.session_state.messages.get(chat_id, [])
    if not messages:
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        export_data = json.dumps(messages, indent=2, ensure_ascii=False)
        title = st.session_state.chat_titles.get(chat_id, "chat")
        st.download_button(
            "📥 Export",
            data=export_data,
            file_name=f"{title}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.messages[chat_id] = []
            save_all_conversations()
            st.rerun()

    with col3:
        if st.button("📝 Summarize", use_container_width=True):
            if not st.session_state.api_key:
                st.toast("Set your API key first.", icon="🔑")
            else:
                summarize_chat(chat_id)
                st.rerun()


def summarize_chat(chat_id: str) -> None:
    """Generate a summary of the chat and insert it at the top."""
    messages = st.session_state.messages.get(chat_id, [])
    if not messages:
        return

    # Build a transcript for summarization
    transcript = "\n".join(
        f"{m['role'].title()}: {m['content']}" for m in messages
    )

    summary_messages = [
        {
            "role": "system",
            "content": "Summarize this conversation in 2-3 sentences. Be concise.",
        },
        {"role": "user", "content": transcript},
    ]

    summary_text = ""
    for chunk in call_openrouter(
        messages=summary_messages,
        model=st.session_state.selected_model,
        temperature=0.3,
        api_key=st.session_state.api_key,
    ):
        summary_text += chunk

    # Guard against API errors
    if not summary_text or summary_text.startswith("[Error]"):
        if summary_text:
            st.toast(summary_text, icon="⚠️")
        return

    # Insert summary at the top
    summary_msg = {
        "role": "assistant",
        "content": f"**📋 Summary:** {summary_text}",
    }
    st.session_state.messages[chat_id].insert(0, summary_msg)
    save_all_conversations()


def main():
    st.set_page_config(page_title="ED GPT", page_icon="💬", layout="wide")
    init_session_state()

    # If stop was clicked mid-stream, the run was interrupted before response_text
    # could be saved. Recover the partial text accumulated in session state.
    if st.session_state.get("stop_generation") and st.session_state.get("streaming_response"):
        chat_id = st.session_state.current_chat_id
        if chat_id:
            st.session_state.messages[chat_id].append(
                {"role": "assistant", "content": st.session_state.streaming_response}
            )
            save_all_conversations()
        st.session_state.streaming_response = ""
        st.session_state.stop_generation = False
        st.session_state.is_generating = False

    render_sidebar()
    render_header()
    render_messages()
    render_chat_actions()
    render_chat_input()


if __name__ == "__main__":
    main()
