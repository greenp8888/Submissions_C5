import streamlit as st
from research_engine import ResearchEngine
from utils import format_report_as_markdown

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DeepResearch · AI Investigator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:ital,wght@0,400;0,500;1,400&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

:root {
    --bg:       #0a0b0f;
    --surface:  #111318;
    --border:   #1e2130;
    --accent:   #e8ff47;
    --accent2:  #47c8ff;
    --muted:    #4a5068;
    --text:     #dde1f0;
    --danger:   #ff5e6c;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Headings */
h1, h2, h3 { font-family: 'Syne', sans-serif !important; color: #fff !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    border-radius: 6px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(232,255,71,0.15) !important;
}

/* Buttons */
.stButton > button {
    background: var(--accent) !important;
    color: #0a0b0f !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.6rem 1.4rem !important;
    letter-spacing: 0.04em !important;
    transition: opacity 0.15s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stButton > button:disabled { opacity: 0.35 !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 8px !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important;
    color: var(--text) !important;
}
.streamlit-expanderContent {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
}

/* Progress / status */
.stProgress > div > div > div { background: var(--accent) !important; }

/* Agent log boxes */
.agent-log {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin: 0.4rem 0;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
    color: var(--text);
}
.agent-log.analysis  { border-left-color: var(--accent2); }
.agent-log.insight   { border-left-color: #b47fff; }
.agent-log.report    { border-left-color: #47ffb4; }
.agent-log.error     { border-left-color: var(--danger); }

/* Metric cards */
.metric-row { display: flex; gap: 1rem; margin: 1rem 0; }
.metric-card {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
.metric-card .val {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--accent);
}
.metric-card .lbl {
    font-size: 0.75rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.25rem;
}

/* Report markdown */
.report-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 2rem;
    line-height: 1.7;
}
.report-container h2 { color: var(--accent) !important; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }
.report-container h3 { color: var(--accent2) !important; }
.report-container code { background: #1a1e2e; padding: 2px 6px; border-radius: 3px; font-family: 'DM Mono', monospace; font-size: 0.85em; }
.report-container blockquote { border-left: 3px solid var(--accent); padding-left: 1rem; color: var(--muted); }

/* Hero banner */
.hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
}
.hero h1 {
    font-size: clamp(2rem, 5vw, 3.5rem) !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
    line-height: 1.1 !important;
    background: linear-gradient(135deg, #fff 30%, var(--accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero .sub {
    color: var(--muted);
    font-size: 1rem;
    margin-top: 0.5rem;
    font-family: 'DM Mono', monospace;
}

/* Tag badge */
.badge {
    display: inline-block;
    background: rgba(232,255,71,0.1);
    color: var(--accent);
    border: 1px solid rgba(232,255,71,0.3);
    border-radius: 4px;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    padding: 2px 8px;
    margin: 2px;
    letter-spacing: 0.05em;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
for key, default in {
    "report": None,
    "logs": [],
    "running": False,
    "metrics": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Keys")
    openrouter_key = st.text_input("OpenRouter API Key", type="password", placeholder="sk-or-…")
    tavily_key     = st.text_input("Tavily API Key",     type="password", placeholder="tvly-…")

    st.markdown("---")
    st.markdown("### ⚙️ Model Settings")
    model_choice = st.selectbox(
        "LLM Model (via OpenRouter)",
        [
            "anthropic/claude-sonnet-4.5",
            "anthropic/claude-sonnet-4.6",
            "anthropic/claude-haiku-4.5",
            "anthropic/claude-opus-4.5",
            "anthropic/claude-opus-4.6",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "google/gemini-pro-1.5",
            "meta-llama/llama-3.1-70b-instruct",
        ],
    )
    max_search_results = st.slider("Max Web Search Results", 3, 15, 7)
    max_tokens         = st.slider("Max Tokens per Agent", 512, 4096, 1500, step=256)

    st.markdown("---")
    st.markdown("### 📚 Upload PDFs (RAG)")
    uploaded_pdfs = st.file_uploader(
        "Drop PDFs for local RAG context",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if uploaded_pdfs:
        for pdf in uploaded_pdfs:
            st.markdown(f'<span class="badge">📄 {pdf.name}</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        '<span style="font-family:\'DM Mono\',monospace;font-size:0.72rem;color:#4a5068;">'
        'Keys are used only in-session<br>and never stored.</span>',
        unsafe_allow_html=True,
    )


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>DeepResearch</h1>
  <p class="sub">multi-hop · multi-source · multi-agent investigation</p>
</div>
""", unsafe_allow_html=True)


# ── Main query form ───────────────────────────────────────────────────────────
col_q, col_btn = st.columns([5, 1])
with col_q:
    query = st.text_area(
        "Research Query",
        placeholder="e.g. Analyze the efficacy of GLP-1 receptor agonists for weight management in Type-2 diabetics — contradictions, emerging trends, and investment outlook.",
        height=100,
        label_visibility="collapsed",
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("▶ Investigate", disabled=st.session_state.running)

# Additional context
with st.expander("🎯 Additional Context (optional)"):
    extra_context = st.text_area(
        "Background / constraints / focus areas",
        placeholder="Limit to studies post-2020. Focus on Southeast Asian markets. Exclude preprints…",
        height=80,
        label_visibility="collapsed",
    )


# ── Run pipeline ──────────────────────────────────────────────────────────────
if run_btn and query.strip():
    if not openrouter_key:
        st.error("⚠️ Please enter your OpenRouter API key in the sidebar.")
        st.stop()
    if not tavily_key:
        st.error("⚠️ Please enter your Tavily API key in the sidebar.")
        st.stop()

    st.session_state.running = True
    st.session_state.logs    = []
    st.session_state.report  = None
    st.session_state.metrics = {}

    # ── Agent pipeline ────────────────────────────────────────────────────────
    status_box  = st.empty()
    progress_bar = st.progress(0)
    log_container = st.container()

    def add_log(msg: str, kind: str = "retriever"):
        st.session_state.logs.append({"msg": msg, "kind": kind})

    engine = ResearchEngine(
        openrouter_key=openrouter_key,
        tavily_key=tavily_key,
        model=model_choice,
        max_results=max_search_results,
        max_tokens=max_tokens,
    )

    try:
        # Step 1 — Retrieval
        status_box.info("🔍 **Contextual Retriever Agent** · Fetching sources…")
        progress_bar.progress(10)
        retrieval_result = engine.run_retriever(
            query=query,
            extra_context=extra_context,
            pdf_files=uploaded_pdfs or [],
        )
        add_log(f"Retrieved {retrieval_result['web_count']} web sources, {retrieval_result['pdf_count']} PDF chunks.", "retriever")
        progress_bar.progress(30)

        # Step 2 — Critical Analysis
        status_box.info("🧠 **Critical Analysis Agent** · Evaluating and cross-referencing…")
        analysis_result = engine.run_analysis(query, retrieval_result)
        add_log(f"Identified {analysis_result['contradiction_count']} contradictions, {analysis_result['source_count']} validated sources.", "analysis")
        progress_bar.progress(55)

        # Step 3 — Insight Generation
        status_box.info("💡 **Insight Generation Agent** · Synthesizing hypotheses…")
        insight_result = engine.run_insights(query, retrieval_result, analysis_result)
        add_log(f"Generated {insight_result['hypothesis_count']} hypotheses, {insight_result['trend_count']} emerging trends.", "insight")
        progress_bar.progress(75)

        # Step 4 — Fact Check
        status_box.info("✅ **Fact-Check Agent** · Verifying key claims…")
        factcheck_result = engine.run_factcheck(query, analysis_result, insight_result)
        add_log(f"Verified {factcheck_result['verified_count']} claims; {factcheck_result['flagged_count']} flagged for review.", "analysis")
        progress_bar.progress(88)

        # Step 5 — Report Builder
        status_box.info("📝 **Report Builder Agent** · Assembling final report…")
        report = engine.run_report_builder(query, retrieval_result, analysis_result, insight_result, factcheck_result)
        st.session_state.report  = report
        st.session_state.metrics = {
            "sources":         retrieval_result["web_count"] + retrieval_result["pdf_count"],
            "contradictions":  analysis_result["contradiction_count"],
            "hypotheses":      insight_result["hypothesis_count"],
            "verified_claims": factcheck_result["verified_count"],
        }
        add_log("Report compiled successfully.", "report")
        progress_bar.progress(100)
        status_box.success("✅ Investigation complete!")

    except Exception as exc:
        add_log(f"ERROR: {exc}", "error")
        status_box.error(f"Pipeline error: {exc}")

    finally:
        st.session_state.running = False

    # ── Render logs ───────────────────────────────────────────────────────────
    with log_container:
        st.markdown("#### Agent Activity Log")
        for entry in st.session_state.logs:
            st.markdown(
                f'<div class="agent-log {entry["kind"]}">› {entry["msg"]}</div>',
                unsafe_allow_html=True,
            )


# ── Display report ────────────────────────────────────────────────────────────
if st.session_state.report:
    st.markdown("---")

    # Metrics row
    m = st.session_state.metrics
    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card"><div class="val">{m.get('sources',0)}</div><div class="lbl">Sources Consulted</div></div>
      <div class="metric-card"><div class="val">{m.get('contradictions',0)}</div><div class="lbl">Contradictions Found</div></div>
      <div class="metric-card"><div class="val">{m.get('hypotheses',0)}</div><div class="lbl">Hypotheses Generated</div></div>
      <div class="metric-card"><div class="val">{m.get('verified_claims',0)}</div><div class="lbl">Claims Verified</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📋 Research Report")
    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(st.session_state.report, unsafe_allow_html=False)
    st.markdown('</div>', unsafe_allow_html=True)

    # Download button
    st.download_button(
        label="⬇️ Download Report (.md)",
        data=st.session_state.report,
        file_name="deep_research_report.md",
        mime="text/markdown",
    )

elif not st.session_state.running and not query.strip():
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem;color:#4a5068;">
      <div style="font-size:3rem;margin-bottom:1rem;">🔬</div>
      <div style="font-family:'DM Mono',monospace;font-size:0.9rem;">
        Enter a research query above and configure your API keys to begin.<br>
        The multi-agent pipeline will investigate, analyze, and synthesize a full report.
      </div>
    </div>
    """, unsafe_allow_html=True)
