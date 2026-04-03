# Open router API key for using a free model , paid models
# How can we mimic the streaming behavior of ChatGPT in Streamlit?
# How can we have all the session_state stored for our conversation. 


import streamlit as st
from openai import OpenAI
import os
#from dotenv import load_dotenv

#load_dotenv()
# Configure the page
st.set_page_config(page_title="My ChatBot", page_icon="🤖")

# Initialize the OpenAI client with OpenRouter

api_key = os.getenv("OPEN_ROUTER_API_KEY")
if not api_key:
    st.warning("Please enter your OpenRouter API key to continue. ")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": "http://localhost:8501",  # Optional: shows on OpenRouter rankings
        "X-Title": "My ChatBot",                  # Optional: shows on OpenRouter rankings
    }
)

# App title
st.title("🤖 ChatFlow")




if "messages" not in st.session_state:
    st.session_state.messages = []

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "app_settings" not in st.session_state:
    st.session_state.app_settings = {
        "theme": "Light",
        "model": "openai/gpt-oss-120b",
        "temperature": 0.7,
        "max_tokens": 150,
        "show_debug": False
    }

# Sidebar configuration
with st.sidebar:
    st.header("🎛️ App Configuration")

    # Model selection
    
    model_choice = st.selectbox(
        "Choose AI Model:",
        ["openai/GPT-3.5", "openai/GPT-4", "openai/gpt-oss-120b", "Claude", "Llama 2"],
        index=["openai/GPT-3.5", "openai/GPT-4", "openai/gpt-oss-120b", "Claude", "Llama 2"].index(st.session_state.app_settings["model"])
        
    )

    
    # Temperature slider
    temperature = st.slider(
        "Temperature (creativity):",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.app_settings["temperature"],
        step=0.1,
        help="Higher values make output more creative but less focused"
    )

    # Max tokens
    max_tokens = st.number_input(
        "Max Tokens:",
        min_value=50,
        max_value=500,
        value=st.session_state.app_settings["max_tokens"],
        step=50
    )

    # Theme selection
    theme = st.radio(
        "App Theme:",
        ["Light", "Dark", "Auto"],
        index=["Light", "Dark", "Auto"].index(st.session_state.app_settings["theme"])
    )

    # Debug mode
    show_debug = st.checkbox(
        "Show Debug Info",
        value=st.session_state.app_settings["show_debug"]
    )

    st.divider()

    # Action buttons
    if st.button("💾 Save Settings", type="primary"):
        st.session_state.app_settings.update({
            "theme": theme,
            "model": model_choice,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "show_debug": show_debug
        })
        st.success("Settings saved!")

    if st.button("🔄 Reset to Defaults"):
        st.session_state.app_settings = {
            "theme": "Light",
            "model": "GPT-3.5",
            "temperature": 0.7,
            "max_tokens": 150,
            "show_debug": False
        }
        st.success("Settings reset!")
        st.rerun()

    # Info section
    with st.expander("ℹ️ About"):
        st.write("""
        This demo shows how to use the sidebar for:
        - App configuration
        - User preferences
        - Secondary controls
        - Information panels
        """)



def summarize_chat():
    chat_string = ""
    for message in st.session_state.messages:
        chat_string += f"{message['role']}: {message['content']}\n"
    response = client.chat.completions.create(
        model=st.session_state.app_settings["model"],
        messages=[{"role": "system", "content": "You are a helpful assistant that summarizes chats between a user and an assistant with 500 words."},
        {"role": "user", "content": f"Summarize the following chat: {chat_string}"}],
        stream=False
    )
    st.session_state.summary = response.choices[0].message.content
    update_export_file()
    st.write(st.session_state.summary)

st.button("Summirize Chat", on_click=summarize_chat)

def update_export_file():
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(str("--------------------------------"))   # convert to string before writing
        f.write(str(st.session_state.messages))   # convert to string before writing
        f.write(str(st.session_state.summary)) 

#st.download_button("Download Chat", data=open("output.txt", "rb").read(), file_name="chat.txt", mime="text/plain")


# Initialize chat history in session state
if "summary" not in st.session_state:
    st.session_state.summary = ""

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    update_export_file()

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)



# Training models on your inputs or prompts - Open router consent or privacy page
# Retention - How much time you'd want to store your input prompts to these models.

    # Generate AI response
    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model=st.session_state.app_settings["model"],  # safer free model
                messages=st.session_state.messages,
                stream=True,
                extra_headers={
                    "HTTP-Referer": "http://localhost:8501",
                    "X-Title": "My ChatBot"
                },
                extra_body={
                    "provider": {
                        "data_collection": "deny"  # or "allow" if you permit retention
                    }
                }
            )
# Hello how can I help you today ? 
# Hello how can I help you today ?


            # Stream the response
            response_text = ""
            response_placeholder = st.empty()

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    # Clean up unwanted tokens
                    content = chunk.choices[0].delta.content
                    content = (
                        content.replace('<s>', '')
                        .replace('<|im_start|>', '')
                        .replace('<|im_end|>', '')
                        .replace("<|OUT|>", "")
                    )
                    response_text += content
                    response_placeholder.markdown(response_text + "▌")

            # Final cleanup of response text
            response_text = (
                response_text.replace('<s>', '')
                .replace('<|im_start|>', '')
                .replace('<|im_end|>', '')
                .replace("<|OUT|>", "")
                .strip()
            )
            response_placeholder.markdown(response_text)

            # Add assistant response to chat history
            st.session_state.messages.append(
                {"role": "assistant", "content": response_text}
            )
            update_export_file()

        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please check your API key and try again.")