"""
Example 5: Complete Streamlit Application

Key Teaching Points:
- Putting together all concepts: session state, chat interface, sidebar
- Professional app structure and organization
- Error handling and user feedback
- Production-ready patterns
"""

import streamlit as st
import time
import random
from datetime import datetime
from openai import OpenAI
import os


# Suppress the warning in bare mode
#os.environ["STREAMLIT_CLIENT_TOOLBAR_MODE"] = "minimal"

# Initialize OpenAI client
#client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))
try:    
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"],
                    base_url="https://openrouter.ai/api/v1")
except Exception as e:    st.error(f"Error initializing OpenAI client: {e}")


# Page configuration
st.set_page_config(
    page_title="Complete Streamlit Demo",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables with defaults"""
    defaults = {
        "messages": [{"role": "assistant", "content": "Hello! I'm your  assistant. How can I help you today?"}],
        "settings": {
            "assistant_name": "Assistant",
            "response_style": "Friendly",
            "max_history": 50,
            "show_timestamps": True
        },
        "stats": {
            "total_messages": 0,
            "session_start": datetime.now()
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize app
initialize_session_state()

# Helper functions
def add_message(role, content):
    """Add a message to chat history with timestamp"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    }
    st.session_state.messages.append(message)

    # Trim history if too long
    max_history = st.session_state.settings["max_history"]
    if len(st.session_state.messages) > max_history:
        # Keep first message (greeting) and trim from the middle
        st.session_state.messages = [st.session_state.messages[0]] + st.session_state.messages[-(max_history-1):]

def generate_response():
    """Generate a response using OpenAI API"""
    style = st.session_state.settings["response_style"]
    assistant_name = st.session_state.settings["assistant_name"]

    style_prompts = {
        "Friendly": "You are a friendly, warm, and approachable assistant. Use a casual and encouraging tone.",
        "Professional": "You are a professional and formal assistant. Use precise, polished language.",
        "Creative": "You are a creative and imaginative assistant. Use vivid language, metaphors, and emojis."
    }

    system_message = f"Your name is {assistant_name}. {style_prompts.get(style, style_prompts['Friendly'])}"

    # Build message history for context
    api_messages = [{"role": "system", "content": system_message}]
    for msg in st.session_state.messages:
        if msg["role"] in ("user", "assistant"):
            api_messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        response = client.chat.completions.create(
            #model="gpt-4o-mini",
           model="openrouter/auto",
            #"gpt-4o-mini" if "gpt-4o-mini" in client.models else "mistralai/mixtral-8x7b-instruct",
            messages=api_messages,
            max_tokens=1024,
            temperature=0.7,
        )
        st.write_stream(response)
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# Sidebar Configuration
with st.sidebar:
    st.header("🎛️ Configuration")

    # Assistant settings
    st.subheader("Assistant Settings")
    assistant_name = st.text_input(
        "Assistant Name:",
        value=st.session_state.settings["assistant_name"]
    )

    response_style = st.selectbox(
        "Response Style:",
        ["Friendly", "Professional", "Creative"],
        index=["Friendly", "Professional", "Creative"].index(st.session_state.settings["response_style"])
    )

    # Chat settings
    st.subheader("Chat Settings")
    max_history = st.slider(
        "Max Chat History:",
        min_value=10,
        max_value=100,
        value=st.session_state.settings["max_history"],
        help="Maximum number of messages to keep in chat history"
    )

    show_timestamps = st.checkbox(
        "Show Timestamps",
        value=st.session_state.settings["show_timestamps"]
    )

    # Update settings
    st.session_state.settings.update({
        "assistant_name": assistant_name,
        "response_style": response_style,
        "max_history": max_history,
        "show_timestamps": show_timestamps
    })

    st.divider()

    # Statistics
    st.subheader("📊 Session Stats")
    session_duration = datetime.now() - st.session_state.stats["session_start"]
    st.metric("Session Duration", f"{session_duration.seconds // 60}m {session_duration.seconds % 60}s")
    st.metric("Messages Sent", st.session_state.stats["total_messages"])
    st.metric("Total Messages", len(st.session_state.messages))

    st.divider()

    # Actions
    st.subheader("🔧 Actions")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = [
                {"role": "assistant", "content": f"Hello! I'm {assistant_name}. Chat cleared - let's start fresh!"}
            ]
            st.rerun()

    with col2:
        if st.button("📤 Export Chat", type="secondary"):
            chat_export = f"Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            chat_export += "=" * 50 + "\n\n"

            for msg in st.session_state.messages:
                role = "You" if msg["role"] == "user" else assistant_name
                timestamp = msg.get("timestamp", datetime.now()).strftime("%H:%M")
                chat_export += f"[{timestamp}] {role}: {msg['content']}\n\n"

            st.download_button(
                "💾 Download",
                chat_export,
                file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

# Main content area
st.title(f"🚀 {assistant_name}")
st.caption(f"Response Style: {response_style} | History Limit: {max_history} messages")

# Chat display
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        role_display = "You" if message["role"] == "user" else assistant_name

        with st.chat_message(message["role"]):
            if show_timestamps and "timestamp" in message:
                timestamp = message["timestamp"].strftime("%H:%M:%S")
                st.caption(f"{role_display} - {timestamp}")

            st.write(message["content"])

# Chat input
if prompt := st.chat_input(f"Message {assistant_name}..."):
    # Add user message
    add_message("user", prompt)
    st.session_state.stats["total_messages"] += 1

    # Display user message
    with st.chat_message("user"):
        if show_timestamps:
            st.caption(f"You - {datetime.now().strftime('%H:%M:%S')}")
        st.write(prompt)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        if show_timestamps:
            st.caption(f"{assistant_name} - {datetime.now().strftime('%H:%M:%S')}")

        # Show typing indicator
        with st.spinner(f"{assistant_name} is thinking..."):
            time.sleep(random.uniform(0.5, 2.0))  # Realistic delay

        # Generate response
        response = generate_response()
        st.write(response)

        # Add assistant response to history
        add_message("assistant", response)

        # Rerun to update the display
        st.rerun()

# Footer with helpful info
st.write("---")
with st.expander("ℹ️ About This Demo"):
    st.write(f"""
    **Complete Streamlit Application Demo**

    This example demonstrates a production-ready Streamlit application with:

    ✅ **Session State Management**: Persistent chat history and settings
    ✅ **Professional UI**: Clean layout with sidebar configuration
    ✅ **Error Handling**: Graceful handling of edge cases
    ✅ **User Feedback**: Loading indicators and confirmation messages
    ✅ **Export Functionality**: Download chat history as text file
    ✅ **Responsive Design**: Works well on different screen sizes
    ✅ **Statistics Tracking**: Session metrics and usage data

    **Architecture Patterns Used:**
    - Initialization functions for clean startup
    - Helper functions for common operations
    - Separation of concerns (UI, logic, data)
    - Consistent error handling and user feedback

    Current session: {len(st.session_state.messages)} messages in {max_history} message limit
    """)

# Teaching notes for instructors
with st.expander("🎓 Instructor Notes"):
    st.write("""
    **Teaching Points to Emphasize:**

    1. **Session State Patterns:**
       - Initialization with defaults
       - Nested dictionaries for organization
       - Trimming data to prevent memory issues

    2. **Professional App Structure:**
       - Page configuration at the top
       - Initialization functions
       - Helper functions for reusable logic
       - Consistent naming conventions

    3. **User Experience:**
       - Loading indicators during processing
       - Confirmation messages for actions
       - Export functionality for data portability
       - Responsive layout considerations

    4. **Production Considerations:**
       - Memory management (history limits)
       - Error handling and graceful failures
       - Performance optimization (minimize reruns)
       - Accessibility and usability

    **Extension Ideas for Advanced Students:**
    - Add user authentication
    - Implement persistent storage (database)
    - Add real AI model integration
    - Multi-page application structure
    - Custom CSS styling
    - Advanced analytics and metrics
    """)

# Development info (hidden by default)
if st.checkbox("Show Development Info", value=False):
    st.write("**Current Session State:**")
    st.json({k: v for k, v in dict(st.session_state).items() if k not in ["messages"]})
    st.write(f"**Messages in Memory:** {len(st.session_state.messages)}")