"""
app.py  ←  Entry point
────────────────────────────────────────────────────────────────
Streamlit UI for the Agentic RAG system.

Run with:
    streamlit run app.py

Architecture (mirrors the flowchart):
  User query
    ↓
  PDF uploaded? ──Yes──→ RAG (FAISS + PDF)
    │                         ↓
    │                   Answer found? ──Yes──→ Return PDF answer
    │                         │
    │                        No
    │                         ↓
    └──No────────────→ LangChain Agent
                              ↓
                    Wikipedia / Tavily / ArXiv
                              ↓
                       Response + Source URL
"""

from __future__ import annotations

import os
import time
import streamlit as st
from dotenv import load_dotenv

from utils.rag_engine import RAGEngine
from utils.agent import build_agent, run_agent
from tools.search_tools import build_tools

# ── Load .env (for local dev) ────────────────────────────────
load_dotenv()


# ════════════════════════════════════════════════════════════
#  Page config
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Agentic RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ════════════════════════════════════════════════════════════
#  Custom CSS — dark, minimal, data-eng aesthetic
# ════════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    code, pre, .stCode {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0d1117;
        border-right: 1px solid #21262d;
    }

    /* Chat message bubbles */
    .user-bubble {
        background: #1c2333;
        border: 1px solid #30363d;
        border-radius: 12px 12px 4px 12px;
        padding: 14px 18px;
        margin: 8px 0;
        color: #e6edf3;
        font-size: 0.95rem;
    }
    .assistant-bubble {
        background: #0d1117;
        border: 1px solid #21262d;
        border-left: 3px solid #58a6ff;
        border-radius: 4px 12px 12px 12px;
        padding: 14px 18px;
        margin: 8px 0;
        color: #e6edf3;
        font-size: 0.95rem;
    }

    /* Source badge */
    .source-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        margin-right: 6px;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .badge-pdf      { background: #1a4731; color: #3fb950; border: 1px solid #3fb950; }
    .badge-wiki     { background: #1a2f4a; color: #58a6ff; border: 1px solid #58a6ff; }
    .badge-tavily   { background: #3a1f5c; color: #bc8cff; border: 1px solid #bc8cff; }
    .badge-arxiv    { background: #4a2020; color: #f85149; border: 1px solid #f85149; }
    .badge-agent    { background: #2a2a1a; color: #d29922; border: 1px solid #d29922; }

    /* Step box */
    .step-box {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 4px 0;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #8b949e;
    }

    /* Input area */
    .stTextInput > div > div > input {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
        border-radius: 8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ════════════════════════════════════════════════════════════
#  Session state initialisation
# ════════════════════════════════════════════════════════════
def _init_state():
    defaults = {
        "messages": [],          # chat history
        "rag_engine": None,      # RAGEngine instance
        "agent_executor": None,  # LangChain AgentExecutor
        "pdf_ready": False,
        "pdf_name": "",
        "pdf_chunks": 0,
        "openai_key": os.getenv("OPENAI_API_KEY", ""),
        "tavily_key": os.getenv("TAVILY_API_KEY", ""),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ════════════════════════════════════════════════════════════
#  Helpers
# ════════════════════════════════════════════════════════════
TOOL_BADGE = {
    "wikipedia-api":                 ("WIKIPEDIA", "badge-wiki"),
    "wikipedia":                     ("WIKIPEDIA", "badge-wiki"),
    "tavily_search_results_json":    ("TAVILY WEB", "badge-tavily"),
    "tavily":                        ("TAVILY WEB", "badge-tavily"),
    "arxiv":                         ("ARXIV", "badge-arxiv"),
    "pdf":                           ("PDF RAG", "badge-pdf"),
    "agent":                         ("AGENT", "badge-agent"),
}

def badge(tool_key: str) -> str:
    label, css = TOOL_BADGE.get(tool_key, ("AGENT", "badge-agent"))
    return f'<span class="source-badge {css}">{label}</span>'


def get_clients():
    """Lazily build RAGEngine + AgentExecutor when keys are available."""
    okey = st.session_state.openai_key.strip()
    tkey = st.session_state.tavily_key.strip()

    if not okey or not tkey:
        return None, None

    # Build RAG engine
    if st.session_state.rag_engine is None:
        st.session_state.rag_engine = RAGEngine(openai_api_key=okey)

    # Build agent (only once)
    if st.session_state.agent_executor is None:
        tools = build_tools(tavily_api_key=tkey)
        st.session_state.agent_executor = build_agent(
            openai_api_key=okey, tools=tools
        )

    return st.session_state.rag_engine, st.session_state.agent_executor


# ════════════════════════════════════════════════════════════
#  Sidebar
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🧠 Agentic RAG")
    st.markdown(
        "<small style='color:#8b949e'>FAISS · LangChain · GPT-4o-mini</small>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── API Keys ─────────────────────────────────────────────
    st.markdown("#### 🔑 API Keys")
    st.session_state.openai_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.openai_key,
        type="password",
        placeholder="sk-...",
    )
    st.session_state.tavily_key = st.text_input(
        "Tavily API Key",
        value=st.session_state.tavily_key,
        type="password",
        placeholder="tvly-...",
    )

    # Reset agent when keys change
    if st.button("🔄 Apply Keys", use_container_width=True):
        st.session_state.rag_engine = None
        st.session_state.agent_executor = None
        st.rerun()

    st.divider()

    # ── PDF Upload ───────────────────────────────────────────
    st.markdown("#### 📄 Upload PDF")
    uploaded_pdf = st.file_uploader(
        "Drop a PDF to enable RAG",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_pdf:
        rag, _ = get_clients()
        if rag is None:
            st.warning("⚠️ Add API keys first.")
        elif uploaded_pdf.name != st.session_state.pdf_name:
            with st.spinner("Indexing PDF into FAISS…"):
                n_chunks = rag.ingest_pdf(
                    pdf_bytes=uploaded_pdf.read(),
                    filename=uploaded_pdf.name,
                )
            st.session_state.pdf_ready = True
            st.session_state.pdf_name = uploaded_pdf.name
            st.session_state.pdf_chunks = n_chunks
            st.success(f"✅ {n_chunks} chunks indexed")

    if st.session_state.pdf_ready:
        st.markdown(
            f"""
            <div style='background:#1a4731;border:1px solid #3fb950;
                        border-radius:8px;padding:8px 12px;margin-top:8px;
                        font-size:0.8rem;color:#3fb950;'>
            📎 <b>{st.session_state.pdf_name}</b><br>
            <span style='color:#8b949e'>{st.session_state.pdf_chunks} chunks · FAISS ready</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🗑️ Remove PDF", use_container_width=True):
            st.session_state.pdf_ready = False
            st.session_state.pdf_name = ""
            st.session_state.rag_engine = None
            st.rerun()

    st.divider()

    # ── Architecture legend ──────────────────────────────────
    st.markdown("#### 🗺️ Routing Logic")
    st.markdown(
        """
        <div style='font-size:0.78rem;color:#8b949e;line-height:1.8'>
        1️⃣ PDF uploaded? → <span style='color:#3fb950'>RAG (FAISS)</span><br>
        2️⃣ Answer in PDF? → <span style='color:#3fb950'>Return it</span><br>
        3️⃣ Not found / No PDF → <span style='color:#d29922'>Agent decides</span><br>
        &nbsp;&nbsp;&nbsp;📖 Encyclopedic → <span style='color:#58a6ff'>Wikipedia</span><br>
        &nbsp;&nbsp;&nbsp;🌐 Current info → <span style='color:#bc8cff'>Tavily</span><br>
        &nbsp;&nbsp;&nbsp;🔬 Research → <span style='color:#f85149'>ArXiv</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ════════════════════════════════════════════════════════════
#  Main chat area
# ════════════════════════════════════════════════════════════
st.markdown("## 🧠 Agentic RAG Assistant")
st.markdown(
    "<p style='color:#8b949e;margin-top:-10px'>Ask anything — I'll route to the right source automatically.</p>",
    unsafe_allow_html=True,
)

# ── Render chat history ──────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-bubble">👤 {msg["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        source_html = badge(msg.get("source", "agent"))
        steps_html = ""
        if msg.get("show_steps") and msg.get("steps"):
            steps_html = "<details><summary style='color:#8b949e;font-size:0.8rem;cursor:pointer'>🔍 ReAct trace</summary>"
            for i, (action, obs) in enumerate(msg["steps"], 1):
                tool = getattr(action, "tool", "?")
                inp  = getattr(action, "tool_input", "")
                steps_html += f"""
                <div class='step-box'>
                Step {i} · Tool: <b style='color:#d29922'>{tool}</b><br>
                Input: {str(inp)[:200]}<br>
                <span style='color:#3fb950'>Output: {str(obs)[:300]}…</span>
                </div>"""
            steps_html += "</details>"

        st.markdown(
            f"""
            <div class="assistant-bubble">
            {source_html}
            <div style='margin-top:10px'>{msg["content"]}</div>
            {steps_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Input box ────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
user_input = st.chat_input("Ask a question…")

if user_input:
    rag, agent_executor = get_clients()

    if rag is None:
        st.error("⚠️ Please add your OpenAI and Tavily API keys in the sidebar.")
        st.stop()

    # Store user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # ── ROUTING LOGIC (mirrors the flowchart) ────────────────
    response_text = ""
    source_key    = "agent"
    steps         = []

    with st.spinner("Thinking…"):

        # Step 1: PDF uploaded + RAG ready?
        if st.session_state.pdf_ready and rag.is_ready:
            rag_result = rag.query(user_input)

            if rag_result["found"]:
                # ✅ Answer found in PDF
                pages = ", ".join(rag_result["sources"]) or "N/A"
                response_text = (
                    f"{rag_result['answer']}\n\n"
                    f"📎 *Source: **{rag_result['pdf_name']}** · Pages: {pages}*"
                )
                source_key = "pdf"
            else:
                # ❌ Not found in PDF → fallback to agent
                agent_result  = run_agent(agent_executor, user_input)
                response_text = agent_result["answer"]
                source_key    = agent_result["tool_used"]
                steps         = agent_result["intermediate_steps"]

        else:
            # No PDF uploaded → go straight to agent
            agent_result  = run_agent(agent_executor, user_input)
            response_text = agent_result["answer"]
            source_key    = agent_result["tool_used"]
            steps         = agent_result["intermediate_steps"]

    # Store assistant message
    st.session_state.messages.append(
        {
            "role":       "assistant",
            "content":    response_text,
            "source":     source_key,
            "steps":      steps,
            "show_steps": bool(steps),
        }
    )

    st.rerun()
