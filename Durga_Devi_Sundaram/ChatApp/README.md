# 〇 Pulse AI — *Flow with me...*

A polished, ChatGPT-style chat assistant built with **Streamlit** and the **OpenRouter API**. Dark blue, turquoise, and gold themed with a clean editorial aesthetic.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

### 3. Connect your API key
- Visit [openrouter.ai](https://openrouter.ai) and sign up for a free account
- Copy your API key (starts with `sk-or-...`)
- Paste it into the **Connection** section in the sidebar

---

## ✨ Feature Overview

### 🤖 Assistant Configuration
- **Custom assistant name** — name your AI anything you like (default: Pulse)
- **Response styles** — choose between Friendly, Professional, or Creative
- **Model selection** — swap between 6 models via OpenRouter:
  - `openai/gpt-4o-mini` *(default, fast & cheap)*
  - `openai/gpt-4o`
  - `anthropic/claude-3.5-haiku`
  - `anthropic/claude-3.5-sonnet`
  - `google/gemini-flash-1.5`
  - `meta-llama/llama-3.3-70b-instruct`

### 💬 Chat Experience
- **Max history slider** — control how many messages are kept in AI context (5–50)
- **Timestamps** — toggle time/date display on every message
- **Animated message bubbles** — smooth fade-in on each new message
- **Suggestion pills** — quick-start prompts on the welcome screen

### 🗂 Chat Groups
- Create named conversation groups (e.g. Work, Research, Personal)
- Switch between groups instantly — each has its own isolated history
- Delete any group except the default General group

### 📤 Actions
- **Clear Chat** — wipe the active group's history in one click
- **Export Chat** — download the full conversation as a `.txt` file, named with the group and date

### 📊 Session Statistics
Three live-updating stats displayed as clean stacked rows in the sidebar:

| Stat | Description |
|---|---|
| ⏱ Duration | Time elapsed since the session started (HH:MM:SS) |
| 💬 Messages Sent | Number of messages you've typed this session |
| 🔢 Tokens Used | Cumulative tokens consumed across all API calls |

### 🎨 Personalization
Accessed via the **Customize your experience** expander:

| Setting | Options |
|---|---|
| Emojis in responses | Toggle on/off |
| Warmth level | Slider 1–5 (terse → very warm) |
| Base style | Conversational, Academic, Casual, Technical, Storytelling |
| Tone | Optimistic, Balanced, Analytical, Empathetic, Direct |
| Your Avatar | 5 curated emoji options (see below) |

**Avatar options:**
| Emoji | Personality |
|---|---|
| 🤖 | Robot — classic and reliable |
| 🧙 | Wizard — wise and mysterious |
| 🦊 | Fox — sly and curious |
| 👾 | Pixel Alien — playful and quirky |
| 🎩 | Top Hat — classy and refined |

---

## 🧠 Differentiating Feature: Real-time Mood Detection

Every message you send is silently analyzed and tagged with a color-coded mood badge:

| Badge | Mood | Triggered by |
|---|---|---|
| 🩵 Turquoise | **Positive** | Thanks, love, awesome, great, amazing… |
| 🔵 Blue | **Neutral** | General factual exchanges |
| 🟡 Gold | **Inquisitive** | Questions, how/why/what/where… |
| 🔴 Red | **Negative** | Errors, frustration, fail, broken… |

Mood badges render inline beneath your message bubble using fully inline styles — reliably visible across all chat groups and re-renders.

Toggle mood detection on/off via the **Show mood detection** checkbox in Chat Settings.

---

## 🎨 Design

| Element | Choice |
|---|---|
| Font | Sora (display + body), JetBrains Mono (code) |
| Background | Deep navy `#050d1a` → `#0d1e38` |
| Accent | Turquoise `#00bfbf` — interactive elements, AI avatar glow |
| Gold | `#f0b429` — token count, export button hover |
| Animations | Message fade-in, logo breathe pulse, hover transitions |

---

## 📁 File Structure

```
chat_app/
├── app.py            # Main Streamlit application
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## 📦 Dependencies

```
streamlit>=1.32.0
requests>=2.31.0
```
