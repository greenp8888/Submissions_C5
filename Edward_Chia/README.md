---
title: ED GPT
emoji: 💬
colorFrom: purple
colorTo: indigo
sdk: streamlit
sdk_version: "1.43.2"
app_file: app.py
pinned: false
---

# ED GPT

A public demo chatbot showcasing multiple AI models through OpenRouter.

## Features

- **Multiple AI Models** — Choose from 5 budget-friendly models
- **Conversation Management** — Create, switch, rename, and delete chats
- **Streaming Responses** — Real-time AI response display
- **Export & Summarize** — Download chats as JSON or generate summaries
- **Light/Dark Mode** — Purple pastel theme with toggle
- **Persistent Storage** — Conversations survive page refreshes

## Setup

1. Get an API key from [OpenRouter](https://openrouter.ai/)
2. Click the ⚙️ Settings button
3. Enter your API key
4. Start chatting!

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

Designed for HuggingFace Spaces with Streamlit SDK.
