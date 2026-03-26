# ChatAPI OpenRouter - Streamlit Chat Application

A complete, production-ready Streamlit chat application that uses OpenRouter's API for AI-powered conversations.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8 or higher
- An OpenRouter API key (get one at [openrouter.ai](https://openrouter.ai))
- pip (Python package manager)

---

## 📋 Installation Steps

### Step 1: Clone or Download the Project
Download the `ChatAPI_OpenRouter.py` file to your computer.

### Step 2: Create a Virtual Environment (Optional but Recommended)
Open a terminal in your project folder and run:

```bash
python -m venv .venv
```

### Step 3: Activate the Virtual Environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

### Step 4: Install Required Dependencies
```bash
pip install streamlit openai
```

### Step 5: Set Up Your OpenRouter API Key
Create a file called `.streamlit/secrets.toml` in your project directory:

```bash
mkdir -p .streamlit
```

Then create the file `.streamlit/secrets.toml` with your API key:

```
OPENAI_API_KEY = "your_openrouter_api_key_here"
```

**To get your API key:**
1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up or log in
3. Go to your dashboard and copy your API key
4. Paste it in the `.streamlit/secrets.toml` file

---

## ▶️ How to Run

### Running the Application

Open a terminal in your project folder and run:

```bash
streamlit run ChatAPI_OpenRouter.py
```

The app will start and display:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://YOUR_IP:8501
```

### Open in Browser
Click the URL or copy-paste `http://localhost:8501` into your browser.

---

## ✨ Features

### Chat Interface
- Clean, modern chat interface with message history
- Real-time responses from AI models
- Typing indicators while waiting for responses

### Configuration Panel (Sidebar)
- **Assistant Settings:**
  - Change assistant name
  - Choose response style (Friendly, Professional, Creative)
  
- **Chat Settings:**
  - Adjust maximum chat history (10-100 messages)
  - Toggle timestamps display
  
- **Session Stats:**
  - Session duration tracking
  - Message count monitoring
  - Total messages in memory

### Actions
- **Clear Chat:** Start a fresh conversation
- **Export Chat:** Download chat history as a text file

### Session Management
- Persistent chat history during session
- Automatic memory management (prevents slowdowns)
- Configurable history limits

---

## 🎯 Basic Usage

1. **Start the app** using the command above
2. **Type your message** in the input field at the bottom
3. **Press Enter** or click send
4. **Wait for the AI response** (progress indicator shows processing)
5. **Configure settings** in the sidebar as needed
6. **Export your chat** anytime using the Export Chat button

---

## 🛠️ Customization

### Change Response Style
In the sidebar, use the dropdown menu to select:
- **Friendly:** Warm, casual, encouraging tone
- **Professional:** Precise, formal, polished language
- **Creative:** Vivid, imaginative, with metaphors and emojis

### Change Assistant Name
Use the "Assistant Name" input field in the sidebar to give your assistant a custom name.

### Adjust Chat History Limit
Use the slider to control how many messages are kept in memory (default: 50).

### Show/Hide Timestamps
Toggle the checkbox to display or hide message timestamps.

---

## 🔧 Troubleshooting

### "command not found: streamlit"
**Solution:** Make sure you've activated your virtual environment and installed Streamlit:
```bash
source .venv/bin/activate
pip install streamlit openai
```

### "Error initializing OpenAI client"
**Solution:** Check that your API key is correctly set in `.streamlit/secrets.toml`

### "ModuleNotFoundError: No module named 'openai'"
**Solution:** Install the OpenAI package:
```bash
pip install openai
```

### App not responding to requests
**Solution:** 
1. Stop the app (press Ctrl+C in terminal)
2. Clear cache: `streamlit cache clear`
3. Run the app again

### "localhost:8501 refused to connect"
**Solution:** 
1. The app may still be starting - wait a few seconds
2. Check that port 8501 is not blocked
3. Try accessing the Network URL instead of localhost

---

## 📝 Project Structure

```
ChatAPI_OpenRouter.py          # Main application file
.streamlit/
  └── secrets.toml            # Your API key (create this)
.venv/                         # Virtual environment (created during setup)
```

---

## 🎓 What This App Teaches

- **Streamlit Basics:** Session state, chat interface, sidebar widgets
- **State Management:** Persistent data across sessions
- **Professional Structure:** Clean code organization and error handling
- **API Integration:** Using OpenRouter's API for AI responses
- **User Experience:** Loading indicators, timestamps, export functionality

---

## ⚙️ System Requirements

- **Memory:** Minimum 2GB RAM
- **Storage:** ~500MB for dependencies
- **Network:** Active internet connection (for API calls)
- **Browser:** Modern browser (Chrome, Firefox, Safari, Edge)

---

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [OpenRouter API Docs](https://openrouter.ai/docs)
- [OpenAI Python Library](https://github.com/openai/openai-python)

---

## 💡 Tips for Success

1. **Keep your API key safe** - Never share it or commit it to GitHub
2. **Monitor your API usage** - OpenRouter charges based on API calls
3. **Start simple** - Test basic conversation before using advanced features
4. **Experiment with styles** - Try different response styles to see the difference
5. **Export chats** - Save important conversations using the Export Chat button

---

## 🆘 Need Help?

If you encounter any issues:
1. Check the troubleshooting section above
2. Review error messages in the terminal
3. Ensure all dependencies are installed: `pip list`
4. Try restarting the app
5. Check that your API key is valid and has credits

---

**Happy chatting!** 🎉
