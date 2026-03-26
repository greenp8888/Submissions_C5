import os

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from openrouter_client import call_openrouter
from storage import (
    ChatData,
    create_new_chat,
    delete_chat_file,
    get_chat_mtime_ns,
    get_chats_version,
    load_all_chats,
    load_chat_from_file,
    save_chat_to_file,
)
from summaries import (
    build_chat_export_text,
    local_conversation_summary,
    quick_summary_from_messages,
    summarize_chat,
)

# Load environment variables from .env file
load_dotenv()
STYLES_DIR = Path(__file__).parent / "styles"


@st.cache_data(show_spinner=False)
def cached_load_all_chats(chats_version: int) -> list[str]:
    return load_all_chats()


@st.cache_data(show_spinner=False)
def cached_load_chat(chat_id: str, chat_mtime_ns: int) -> ChatData:
    return load_chat_from_file(chat_id)


@st.cache_data(show_spinner=False)
def cached_build_export_text(chat_id: str, chat_mtime_ns: int, conversation_summary: str) -> str:
    chat_data = load_chat_from_file(chat_id)
    row_quick_summary = quick_summary_from_messages(chat_data.get("messages", []))
    row_conversation_summary = conversation_summary or chat_data.get("summary", "")
    if not row_conversation_summary:
        row_conversation_summary = local_conversation_summary(chat_data.get("messages", []))
    return build_chat_export_text(
        chat_id,
        chat_data,
        row_quick_summary,
        row_conversation_summary,
    )

st.set_page_config(
    page_title="ChatApp",
    page_icon=":speech_balloon:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "openrouter_api_key" not in st.session_state:
    st.session_state.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "openai/gpt-3.5-turbo"

if "chat_summaries" not in st.session_state:
    st.session_state.chat_summaries = {}

def _load_style_text(filename: str) -> str:
    with open(STYLES_DIR / filename, "r", encoding="utf-8") as f:
        return f.read()


def _inject_theme(css_text: str, theme: dict[str, str]) -> str:
    return (
        css_text.replace("__BG__", theme["bg"])
        .replace("__PANEL__", theme["panel"])
        .replace("__TEXT__", theme["text"])
        .replace("__MUTED__", theme["muted"])
        .replace("__BORDER__", theme["border"])
        .replace("__ACCENT__", theme["accent"])
        .replace("__ACCENT_HOVER__", theme["accent_hover"])
        .replace("__BUTTON_TEXT__", theme["button_text"])
    )

# Available OpenRouter models
OPENROUTER_MODELS = {
    "OpenAI": {
        "openai/gpt-4-turbo": "GPT-4 Turbo",
        "openai/gpt-4": "GPT-4",
        "openai/gpt-3.5-turbo": "GPT-3.5 Turbo",
    },
    "Anthropic": {
        "anthropic/claude-3-opus": "Claude 3 Opus",
        "anthropic/claude-3-sonnet": "Claude 3 Sonnet",
        "anthropic/claude-3-haiku": "Claude 3 Haiku",
    },
    "Meta": {
        "meta-llama/llama-2-70b-chat": "Llama 2 70B Chat",
        "meta-llama/llama-2-13b-chat": "Llama 2 13B Chat",
    },
    "Mistral": {
        "mistralai/mistral-large": "Mistral Large",
        "mistralai/mistral-medium": "Mistral Medium",
        "mistralai/mistral-small": "Mistral Small",
    },
}

# Custom CSS for styling
if st.session_state.dark_mode:
    theme = {
        "bg": "#0e1628",
        "panel": "#1a2238",
        "text": "#e5edff",
        "muted": "#a9b8d8",
        "border": "#2f3d5a",
        "accent": "#2f80ed",
        "accent_hover": "#1f6fd8",
        "button_text": "#ffffff",
    }
else:
    theme = {
        "bg": "#e7edf7",
        "panel": "#dfe7f4",
        "text": "#13294b",
        "muted": "#31486f",
        "border": "#bccbe3",
        "accent": "#1458bf",
        "accent_hover": "#0f4799",
        "button_text": "#ffffff",
    }

base_css = _inject_theme(_load_style_text("base.css"), theme)
st.markdown(f"<style>{base_css}</style>", unsafe_allow_html=True)

if not st.session_state.dark_mode:
    light_css = _load_style_text("light.css")
    st.markdown(f"<style>{light_css}</style>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ChatApp")

    # API Key Configuration
    with st.expander("API Configuration", expanded=False):
        api_key = st.text_input(
            "OpenRouter API Key:",
            value=st.session_state.openrouter_api_key,
            type="password",
            help="Get your API key from https://openrouter.ai/",
        )
        if api_key:
            st.session_state.openrouter_api_key = api_key
            os.environ["OPENROUTER_API_KEY"] = api_key
            st.success("OpenRouter API Key configured")

        st.divider()

        # Model Selection
        st.markdown("### Select Model")
        selected_provider = st.selectbox(
            "Provider:",
            options=list(OPENROUTER_MODELS.keys()),
            label_visibility="collapsed",
        )

        models_for_provider = OPENROUTER_MODELS[selected_provider]

        model_options = [f"{model_id} - {model_name}" for model_id, model_name in models_for_provider.items()]
        selected_model_display = st.selectbox(
            "Model:",
            options=model_options,
            label_visibility="collapsed",
        )

        # Extract the model ID from the display string
        st.session_state.selected_model = selected_model_display.split(" - ")[0]

        st.markdown(f"**Current Model:** `{st.session_state.selected_model}`")

    st.divider()

    # New Chat Button
    if st.button("+ New Chat", key="new_chat", use_container_width=True):
        chat_id = create_new_chat(st.session_state.selected_model)
        st.session_state.current_chat_id = chat_id
        st.rerun()

    st.divider()

    # Chat History Section
    all_chats = cached_load_all_chats(get_chats_version())
    if all_chats:
        st.markdown("### Chats")
        st.caption("⬇ Export  |  🗑 Delete")
        for chat_id in all_chats:
            chat_mtime_ns = get_chat_mtime_ns(chat_id)
            chat_data = cached_load_chat(chat_id, chat_mtime_ns)
            chat_name = chat_data.get("name", chat_id)

            row_conversation_summary = st.session_state.chat_summaries.get(chat_id, "")
            export_text = cached_build_export_text(chat_id, chat_mtime_ns, row_conversation_summary)

            col1, col2, col3 = st.columns([7, 1, 1])
            with col1:
                if st.button(
                    chat_name[:25] + "..." if len(chat_name) > 25 else chat_name,
                    key=f"chat_{chat_id}",
                    use_container_width=True,
                ):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with col2:
                st.download_button(
                    "⬇",
                    data=export_text,
                    file_name=f"{chat_id}_chat.txt",
                    mime="text/plain",
                    key=f"export_{chat_id}",
                    type="primary",
                    use_container_width=True,
                )
            with col3:
                if st.button("🗑", key=f"delete_{chat_id}", type="primary", use_container_width=True):
                    delete_chat_file(chat_id)
                    if st.session_state.current_chat_id == chat_id:
                        remaining_chats = cached_load_all_chats(get_chats_version())
                        st.session_state.current_chat_id = remaining_chats[0] if remaining_chats else None
                    st.rerun()
    else:
        st.info("No chats yet. Create one to get started.")

    st.divider()

    # Settings
    st.markdown("### Settings")
    st.caption("Use the sidebar chevron at the top to collapse or expand.")

    new_dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode)
    if new_dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = new_dark_mode
        st.rerun()

    if st.session_state.current_chat_id and st.button("Clear Current Chat", use_container_width=True):
        chat_data = cached_load_chat(
            st.session_state.current_chat_id,
            get_chat_mtime_ns(st.session_state.current_chat_id),
        )
        chat_data["messages"] = []
        save_chat_to_file(st.session_state.current_chat_id, chat_data)
        st.rerun()

# Main Chat Area
if st.session_state.current_chat_id is None:
    st.title("Welcome to ChatApp")
    st.markdown(
        """
    ### Get Started
    1. Click **"+ New Chat"** in the sidebar to create a new conversation
    2. Enter your **API Key** in the Configuration section
    3. Start asking questions to the AI assistant

    **Note:** Make sure you have a valid OpenAI API key configured.
    """
    )
else:
    current_chat_id = st.session_state.current_chat_id
    current_chat_data = cached_load_chat(current_chat_id, get_chat_mtime_ns(current_chat_id))
    current_chat_name = current_chat_data.get("name", current_chat_id)

    st.markdown(f"## {current_chat_name}")

    # Summarize Conversation button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Summarize", use_container_width=True):
            if not st.session_state.openrouter_api_key:
                st.error("Please configure your OpenRouter API key first.")
            else:
                with st.spinner("Summarizing conversation..."):
                    st.session_state.chat_summaries[current_chat_id] = summarize_chat(
                        current_chat_id,
                        st.session_state.openrouter_api_key,
                        current_chat_data.get("model", st.session_state.selected_model),
                    )
                    current_chat_data["summary"] = st.session_state.chat_summaries[current_chat_id]
                    save_chat_to_file(current_chat_id, current_chat_data)

    summary_placeholder = st.empty()
    current_summary = st.session_state.chat_summaries.get(current_chat_id, "")
    if not current_summary:
        current_summary = current_chat_data.get("summary", "")
    if current_summary:
        with summary_placeholder.container():
            st.markdown("### Summary")
            st.markdown(current_summary)

    # Display messages
    st.divider()
    messages = current_chat_data.get("messages", [])

    for i, message in enumerate(messages):
        if message["role"] == "user":
            col1, col2 = st.columns([1, 20])
            with col1:
                st.markdown("U")
            with col2:
                st.markdown(f"**You**\n\n{message['content']}")
        else:
            col1, col2 = st.columns([1, 20])
            with col1:
                st.markdown("A")
            with col2:
                msg_col, up_col, down_col = st.columns([16, 1, 1])
                with msg_col:
                    st.markdown(f"**Assistant**\n\n{message['content']}")
                with up_col:
                    st.markdown("👍")
                with down_col:
                    st.markdown("👎")

    st.divider()

    # Input area
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "What would you like to know?",
            placeholder="Type your message here...",
            label_visibility="collapsed",
        )
        submit_button = st.form_submit_button("Send", use_container_width=True)

    if submit_button and user_input:
        if not st.session_state.openrouter_api_key:
            st.error("Please configure your OpenRouter API Key in the settings!")
        else:
            current_chat_data["messages"].append(
                {
                    "role": "user",
                    "content": user_input,
                }
            )
            save_chat_to_file(current_chat_id, current_chat_data)

            try:
                assistant_message = call_openrouter(
                    st.session_state.openrouter_api_key,
                    current_chat_data.get("model", st.session_state.selected_model),
                    current_chat_data["messages"],
                )

                current_chat_data["messages"].append(
                    {
                        "role": "assistant",
                        "content": assistant_message,
                    }
                )
                save_chat_to_file(current_chat_id, current_chat_data)

                st.rerun()
            except RuntimeError as e:
                st.error(f"Error: {str(e)}")
