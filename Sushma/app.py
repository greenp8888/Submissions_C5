"""Streamlit frontend for the Multi-Agent AI Deep Researcher.

Launch with:
    streamlit run app.py
(run from the Multi_Agent_cursor directory)
"""

import asyncio
import io
import os
import re
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# Ensure the project root is importable regardless of cwd
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from multi_agent_researcher.main import SCENARIOS, run_research  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Page configuration — MUST be the very first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent AI Deep Researcher",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**Multi-Agent AI Deep Researcher** — "
            "Powered by LangGraph, OpenRouter, Tavily, ArXiv & Wikipedia."
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Layout ─────────────────────────────────────────────── */
.main .block-container { padding-top: 1rem; max-width: 1100px; }

/* ── Hero banner ─────────────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 60%, #0f3460 100%);
    border-radius: 16px;
    padding: 2.2rem 2.5rem;
    margin-bottom: 1.6rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,.4);
}
.hero h1 {
    color: #e2e8f0;
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0 0 .4rem;
    letter-spacing: -.5px;
}
.hero p { color: #94a3b8; font-size: .95rem; margin: 0 0 .8rem; }
.badge {
    display: inline-block;
    background: rgba(99,179,237,.15);
    color: #63b3ed;
    border: 1px solid rgba(99,179,237,.3);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: .72rem;
    margin: 2px 3px 0;
}

/* ── Agent step indicators ───────────────────────────────── */
.step        { display:flex; align-items:center; gap:10px; padding:8px 14px;
               border-radius:8px; margin:4px 0; font-size:.88rem;
               border-left:3px solid #334155; background:#1e293b; color:#94a3b8; }
.step.done   { border-left-color:#48bb78; background:#1a2e24; color:#9ae6b4; }
.step.active { border-left-color:#63b3ed; background:#1e3a5f; color:#90cdf4; }
.step.error  { border-left-color:#fc8181; background:#2d1b1b; color:#feb2b2; }

/* ── Status banners ──────────────────────────────────────── */
.banner-ok  { background:linear-gradient(90deg,#1a2e24,#1e3a2e);
              border:1px solid #48bb78; border-radius:10px;
              padding:.7rem 1.1rem; color:#9ae6b4; font-size:.9rem; margin:.5rem 0; }
.banner-err { background:linear-gradient(90deg,#2d1b1b,#3d1f1f);
              border:1px solid #fc8181; border-radius:10px;
              padding:.7rem 1.1rem; color:#feb2b2; font-size:.9rem; margin:.5rem 0; }
.banner-warn{ background:linear-gradient(90deg,#2d2510,#3d3010);
              border:1px solid #f6ad55; border-radius:10px;
              padding:.7rem 1.1rem; color:#fbd38d; font-size:.9rem; margin:.5rem 0; }

/* ── Report display ──────────────────────────────────────── */
.report-wrap { background:#0f172a; border:1px solid #1e3a5f;
               border-radius:12px; padding:1.5rem 2rem; }

/* ── Misc ────────────────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "query": "",
    "last_report": None,
    "last_logs": "",
    "last_elapsed": 0.0,
    "running": False,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # --- API Keys ---
    with st.expander("🔑 API Keys", expanded=True):
        openrouter_key = st.text_input(
            "OpenRouter API Key ✱",
            value=os.getenv("OPENROUTER_API_KEY", ""),
            type="password",
            help="Required for all LLM calls. Get yours at https://openrouter.ai",
        )
        tavily_key = st.text_input(
            "Tavily API Key ✱",
            value=os.getenv("TAVILY_API_KEY", ""),
            type="password",
            help="Required for web search. Free key at https://tavily.com",
        )
        serpapi_key = st.text_input(
            "SerpAPI Key (optional)",
            value=os.getenv("SERPAPI_API_KEY", ""),
            type="password",
            help="Broadens search to Google. Get at https://serpapi.com",
        )

    # --- Model selection ---
    st.markdown("### 🤖 Model")
    model_name = st.selectbox(
        "LLM via OpenRouter",
        options=[
            "openai/gpt-4.1-mini",
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "google/gemini-2.0-flash-001",
            "meta-llama/llama-3.3-70b-instruct",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # --- Architecture summary ---
    st.markdown("### 🏗️ Agent Pipeline")
    st.markdown(
        """
1. 🗺️ **Query Planner** — Decomposes question into 3–5 sub-queries
2. 📥 **Contextual Retriever** — Pulls from ArXiv, Tavily, Wikipedia, SerpAPI & PDF
3. 🔍 **Critical Analyzer** — Synthesizes evidence & identifies contradictions
4. 💡 **Insight Generator** — Chain-of-thought hypotheses & trends
5. 📝 **Report Builder** — Structured Markdown research report

Built with **LangGraph** + **OpenRouter**
"""
    )
    st.markdown("---")
    st.caption("Multi-Agent AI Deep Researcher · v1.0.0")

# Push keys + model to environment so sub-modules pick them up
if openrouter_key:
    os.environ["OPENROUTER_API_KEY"] = openrouter_key
if tavily_key:
    os.environ["TAVILY_API_KEY"] = tavily_key
if serpapi_key:
    os.environ["SERPAPI_API_KEY"] = serpapi_key
if model_name:
    os.environ["OPENROUTER_MODEL"] = model_name

# ─────────────────────────────────────────────────────────────────────────────
# Hero header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
  <h1>🔬 Multi-Agent AI Deep Researcher</h1>
  <p>Multi-hop, multi-source research — powered by five specialized AI agents</p>
  <span class="badge">LangGraph</span>
  <span class="badge">OpenRouter</span>
  <span class="badge">ArXiv</span>
  <span class="badge">Tavily</span>
  <span class="badge">Wikipedia</span>
  <span class="badge">SerpAPI</span>
  <span class="badge">PDF</span>
</div>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Predefined scenario buttons
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("#### Quick Start — Choose a Scenario")
_ICONS = ["🎓", "📰", "⚙️"]
_cols = st.columns(3)
for _i, (_key, _scenario) in enumerate(SCENARIOS.items()):
    with _cols[_i]:
        if st.button(
            f"{_ICONS[_i]} {_scenario['name']}",
            key=f"scenario_{_key}",
            use_container_width=True,
            help=_scenario["query"],
        ):
            st.session_state["query"] = _scenario["query"]
            st.rerun()

st.markdown("")

# ─────────────────────────────────────────────────────────────────────────────
# Query input
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("#### Research Query")
query = st.text_area(
    "Research query",
    value=st.session_state["query"],
    height=110,
    placeholder=(
        "e.g. What are the latest advances in large language model reasoning, "
        "specifically chain-of-thought prompting and self-reflection techniques?"
    ),
    label_visibility="collapsed",
    key="query_input",
)
st.session_state["query"] = query
char_count = len(query.strip())
col_char, col_hint = st.columns([1, 5])
col_char.caption(f"{char_count} / 2000 chars")
if 0 < char_count < 15:
    col_hint.caption("⚠️ Query must be at least 15 characters.")

# ─────────────────────────────────────────────────────────────────────────────
# PDF upload
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("📎 Attach PDF Documents (optional)", expanded=False):
    uploaded_files = st.file_uploader(
        "Upload PDFs to include as research sources",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        st.success(
            f"{len(uploaded_files)} PDF(s) ready: "
            + ", ".join(f.name for f in uploaded_files)
        )

# ─────────────────────────────────────────────────────────────────────────────
# API key warning
# ─────────────────────────────────────────────────────────────────────────────
_api_ok = bool(openrouter_key and tavily_key)
if not _api_ok:
    st.markdown(
        '<div class="banner-warn">'
        "⚠️ OpenRouter and Tavily API keys are required. Add them in the sidebar."
        "</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Run button
# ─────────────────────────────────────────────────────────────────────────────
_can_run = (
    char_count >= 15
    and _api_ok
    and not st.session_state["running"]
)
run_clicked = st.button(
    "🚀  Run Deep Research",
    type="primary",
    use_container_width=True,
    disabled=not _can_run,
)
st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# Helper — sync wrapper for the async pipeline
# ─────────────────────────────────────────────────────────────────────────────
def _run_sync(q: str, pdf_paths: list[str] | None) -> str:
    """Run the async research pipeline on a fresh event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_research(q, pdf_paths=pdf_paths))
    finally:
        loop.close()


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline execution
# ─────────────────────────────────────────────────────────────────────────────
if run_clicked:
    st.session_state["running"] = True
    st.session_state["last_report"] = None
    st.session_state["last_logs"] = ""

    # Save uploaded PDFs to temp files
    pdf_paths: list[str] = []
    if uploaded_files:
        for uf in uploaded_files:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(uf.read())
            tmp.flush()
            tmp.close()
            pdf_paths.append(tmp.name)

    # ── Agent step display ──────────────────────────────────────────────────
    _AGENT_STEPS = [
        ("🗺️", "Query Planner",        "Decomposing research question...",    "AGENT: Query Planner"),
        ("📥", "Contextual Retriever",  "Querying ArXiv, Tavily, Wikipedia...", "AGENT: Contextual Retriever"),
        ("🔍", "Critical Analyzer",     "Synthesizing evidence...",            "AGENT: Critical Analyzer"),
        ("💡", "Insight Generator",     "Generating hypotheses & trends...",   "AGENT: Insight Generator"),
        ("📝", "Report Builder",        "Compiling structured report...",      "AGENT: Report Builder"),
    ]

    st.markdown("### 🔄 Pipeline Progress")
    step_slots = []
    for icon, name, desc, _ in _AGENT_STEPS:
        slot = st.empty()
        slot.markdown(
            f'<div class="step">⏳ {icon} <strong>{name}</strong> — {desc}</div>',
            unsafe_allow_html=True,
        )
        step_slots.append(slot)

    # ── Execute ──────────────────────────────────────────────────────────────
    buf = io.StringIO()
    start_ts = datetime.now(timezone.utc)
    report: str | None = None
    error: str | None = None

    with st.spinner("Running — this typically takes 30–120 seconds…"):
        try:
            with redirect_stdout(buf):
                report = _run_sync(
                    query.strip(),
                    pdf_paths=pdf_paths or None,
                )
        except Exception as exc:
            error = str(exc)

    elapsed = (datetime.now(timezone.utc) - start_ts).total_seconds()
    captured_logs = buf.getvalue()

    # ── Update step indicators based on captured stdout ───────────────────────
    for i, (icon, name, desc, marker) in enumerate(_AGENT_STEPS):
        if marker in captured_logs:
            step_slots[i].markdown(
                f'<div class="step done">✅ {icon} <strong>{name}</strong> — Complete</div>',
                unsafe_allow_html=True,
            )
        elif error:
            step_slots[i].markdown(
                f'<div class="step error">❌ {icon} <strong>{name}</strong> — {desc}</div>',
                unsafe_allow_html=True,
            )

    # Cleanup temp PDFs
    for p in pdf_paths:
        try:
            os.unlink(p)
        except Exception:
            pass

    # Persist to session state
    st.session_state["last_report"] = report
    st.session_state["last_logs"] = captured_logs
    st.session_state["last_elapsed"] = elapsed
    st.session_state["running"] = False

    if error:
        st.markdown(
            f'<div class="banner-err">❌ Pipeline error: {error}</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# Results display (persists via session state across reruns)
# ─────────────────────────────────────────────────────────────────────────────
report = st.session_state.get("last_report")
captured_logs = st.session_state.get("last_logs", "")
elapsed = st.session_state.get("last_elapsed", 0.0)

if report:
    # ── Success banner ────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="banner-ok">✅ Research complete — {elapsed:.1f}s elapsed</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    # ── Metrics ───────────────────────────────────────────────────────────────
    _docs_m   = re.search(r"(\d+) retrieved documents", captured_logs)
    _subq_m   = re.search(r"(\d+) sub.queries", captured_logs, re.IGNORECASE)
    _ins_m    = re.search(r"Insights generated: (\d+)", captured_logs)
    _chars_m  = len(report)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("⏱️ Time", f"{elapsed:.1f}s")
    m2.metric("📄 Documents", _docs_m.group(1) if _docs_m else "—")
    m3.metric("🔍 Sub-queries", _subq_m.group(1) if _subq_m else "—")
    m4.metric("💡 Report size", f"{_chars_m:,} chars")

    st.markdown("---")

    # ── Report display ────────────────────────────────────────────────────────
    tab_rendered, tab_raw = st.tabs(["📄 Rendered Report", "📋 Raw Markdown"])

    with tab_rendered:
        st.markdown('<div class="report-wrap">', unsafe_allow_html=True)
        st.markdown(report)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_raw:
        st.code(report, language="markdown")

    # ── Download ──────────────────────────────────────────────────────────────
    _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="⬇️  Download Report (.md)",
        data=report,
        file_name=f"research_report_{_ts}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    # ── Pipeline logs ─────────────────────────────────────────────────────────
    with st.expander("🔍 Pipeline Logs", expanded=False):
        st.code(captured_logs or "(no output captured)", language="text")
