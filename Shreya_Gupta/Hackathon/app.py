"""
app.py — Streamlit Frontend (root-level, required for `streamlit run app.py`)

Integrates the entire research pipeline into a clean, real-time UI.
"""

import os
import sys

# Ensure project root is on PYTHONPATH so imports work correctly
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from core.graph import build_research_graph
from core.state import ResearchState
from tools.vector_store import ingest_pdf_to_chroma
from llm.openrouter import AVAILABLE_MODELS
import time

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Autonomous Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem; font-weight: 800;
        background: linear-gradient(90deg, #6366f1, #a855f7);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .route-badge {
        display: inline-block;
        background: #1e293b; color: #818cf8;
        border: 1px solid #4f46e5; border-radius: 6px;
        padding: 2px 8px; font-size: 0.78rem;
        font-family: monospace; margin: 2px;
    }
    .report-wrap { background: #0f172a; padding: 28px; border-radius: 12px; border: 1px solid #1e293b; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
if "openrouter_key" not in st.session_state:
    st.session_state.openrouter_key = ""
if "tavily_key" not in st.session_state:
    st.session_state.tavily_key = ""
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.divider()

    st.markdown("### 🔑 API Keys")
    openrouter_key = st.text_input("OpenRouter API Key", type="password", placeholder="sk-or-v1-...", key="openrouter_key")
    tavily_key     = st.text_input("Tavily Search API Key", type="password", placeholder="tvly-...", key="tavily_key")

    st.markdown("### 🤖 Model")
    selected_label = st.selectbox("LLM via OpenRouter", list(AVAILABLE_MODELS.keys()))
    selected_model = AVAILABLE_MODELS[selected_label]

    st.divider()
    st.markdown("### 📄 Knowledge Base (ChromaDB)")
    st.caption("Upload PDFs → chunked + embedded locally → searched by `chroma_local` tool")

    uploaded_files = st.file_uploader("Upload PDF Documents", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        if st.button("📥 Ingest PDFs into ChromaDB", use_container_width=True, type="secondary"):
            prog = st.progress(0)
            for i, f in enumerate(uploaded_files):
                with st.spinner(f"Processing {f.name}..."):
                    result = ingest_pdf_to_chroma(f)
                    if result["status"] == "success":
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
                prog.progress((i + 1) / len(uploaded_files))
            prog.empty()

    st.divider()
    st.markdown("### 🗺️ Agent Pipeline")
    st.markdown("""""")

    st.divider()
    st.markdown("### 🔧 Tech Stack")
    st.markdown("""
- **Orchestration:** LangGraph
- **LLM:** OpenRouter API
- **Web Search:** Tavily
- **Academic:** ArXiv
- **Vector DB:** ChromaDB (local, free)
- **Embeddings:** FastEmbed (local, free)
- **Frontend:** Streamlit
    """)
    st.caption("ChromaDB + FastEmbed = zero cloud cost for local retrieval")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN AREA — HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">🔬 Autonomous Research Assistant</div>',
    unsafe_allow_html=True,
)
st.markdown(
    "**Agentic RAG** · LangGraph multi-agent pipeline · "
    "Dynamic Tool Routing · ArXiv + Web + Local ChromaDB"
)
st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# API KEY GATE — Prominent warning if keys are missing
# Analogy: Security guard at the door. No badge = no entry.
# ─────────────────────────────────────────────────────────────────────────────
keys_missing = not st.session_state.openrouter_key or not st.session_state.tavily_key

if keys_missing:
    st.markdown('<div class="api-warn">', unsafe_allow_html=True)
    st.warning("⚠️ **API Keys Required** — Enter them below or in the sidebar, then click **Save API Keys**.")

    main_col1, main_col2 = st.columns(2)

    with main_col1:
        main_or_key = st.text_input(
            "🔑 OpenRouter API Key",
            type="password",
            placeholder="sk-or-v1-...",
            value=st.session_state.openrouter_key,
            key="main_or_input",
            help="Sign up free at openrouter.ai",
        )

    with main_col2:
        main_tv_key = st.text_input(
            "🔑 Tavily Search API Key",
            type="password",
            placeholder="tvly-...",
            value=st.session_state.tavily_key,
            key="main_tv_input",
            help="Sign up free at tavily.com",
        )

    if st.button("💾 Save Keys & Continue", type="primary"):
        if main_or_key.strip() and main_tv_key.strip():
            st.session_state.openrouter_key = main_or_key.strip()
            st.session_state.tavily_key     = main_tv_key.strip()
            st.success("✅ Keys saved! You can now run research.")
            st.rerun()  # Refresh to hide this gate and show the full UI
        else:
            st.error("Both keys are required to proceed.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Show example queries even when keys are missing, so user knows what to expect
    st.divider()
    _show_examples = True

else:
    _show_examples = False


# ─────────────────────────────────────────────────────────────────────────────
# RESEARCH INPUT AREA
# Only fully interactive when keys are present
# ─────────────────────────────────────────────────────────────────────────────
if not keys_missing:

    st.markdown("### 🎯 Research Question")
    st.caption(
        "Ask anything! Complex, multi-part questions work best. "
        "Sports/news → web only. Academic/science → ArXiv + web. "
        "Upload PDFs for private knowledge base search."
    )

    user_query = st.text_area(
        label="Research Question",
        label_visibility="collapsed",
        placeholder=(
            "Examples:\n"
            "• 'What are Virat Kohli's IPL 2024 stats?' → routed to web search only\n"
            "• 'Explain Hawking radiation and the black hole information paradox' → ArXiv + web\n"
            "• 'Compare Mamba SSMs vs Transformer attention for long-context tasks' → ArXiv + web + local\n"
            "• 'What caused the 2024 global IT outage and what are its cybersecurity implications?'"
        ),
        height=130,
    )

    run_col1, run_col2, run_col3 = st.columns([3, 1, 3])
    with run_col2:
        run_button = st.button("🚀 Run Research", type="primary", use_container_width=True)

    st.divider()


    # ─────────────────────────────────────────────────────────────────────────
    # PIPELINE EXECUTION
    # ─────────────────────────────────────────────────────────────────────────
    if run_button:

        if not user_query.strip():
            st.warning("⚠️ Please enter a research question before running.")
            st.stop()

        # Push keys to environment for tool functions (they read os.environ)
        os.environ["TAVILY_API_KEY"] = st.session_state.tavily_key

        # ── INITIAL STATE ─────────────────────────────────────────────────────
        initial_state: ResearchState = {
            "user_query":     user_query.strip(),
            "sub_queries":    [],
            "routing_plan":   [],
            "raw_documents":  [],
            "analyzed_facts": "",
            "insights":       "",
            "final_report":   "",
            "current_agent":  "Initializing...",
            "error":          None,
        }

        # ── AGENT DISPLAY CONFIG ──────────────────────────────────────────────
        agent_display = {
            "planner":   ("🧠", "Query Planner + Router",
                          "Decomposing query & assigning tools per sub-query"),
            "retriever": ("🔍", "Dynamic Retriever",
                          "Executing parallel tool calls → Web / ArXiv / Local ChromaDB"),
            "analyst":   ("🔬", "Critical Analyst",
                          "Filtering noise, validating facts, flagging contradictions"),
            "insight":   ("💡", "Insight Generator",
                          "Chain-of-Thought reasoning → hypotheses & strategic implications"),
            "reporter":  ("📝", "Report Builder",
                          "Compiling structured Markdown report with citations"),
        }

        # ── ROUTING PLAN DISPLAY (populated mid-stream after Planner node) ───
        routing_placeholder = st.empty()
        complete_state      = None

        # ── STREAM PIPELINE ───────────────────────────────────────────────────
        with st.status("🚀 Research pipeline executing...", expanded=True) as status_box:
            try:
                # Build graph (LLM init happens here)
                st.write("⚙️ Initializing pipeline & LLM connection...")
                app = build_research_graph(
                    openrouter_api_key=st.session_state.openrouter_key,
                    model=selected_model,
                )

                for chunk in app.stream(initial_state, stream_mode="updates"):
                    for node_name, node_state in chunk.items():

                        # Display agent progress tick
                        if node_name in agent_display:
                            emoji, name, desc = agent_display[node_name]
                            st.write(f"{emoji} **{name}** — {desc} ✅")

                        # After Planner: show routing plan in real-time
                        if node_name == "planner":
                            plan = node_state.get("routing_plan", [])
                            if plan:
                                with routing_placeholder.container():
                                    st.markdown("#### 🗺️ Triage Output — Routing Plan")
                                    st.caption(
                                        "The Planner (triage nurse) decided which tools to call "
                                        "for each sub-query BEFORE retrieval begins."
                                    )
                                    for idx, item in enumerate(plan, 1):
                                        tools_badges = " ".join(
                                            f'<span class="route-badge">🔧 {t}</span>'
                                            for t in item.get("tools", [])
                                        )
                                        st.markdown(
                                            f"**{idx}. {item['sub_query']}**<br>"
                                            f"{tools_badges}<br>"
                                            f"<small style='color:#6b7280;'>"
                                            f"Rationale: {item.get('rationale', 'N/A')}"
                                            f"</small>",
                                            unsafe_allow_html=True,
                                        )
                                        st.markdown("")

                        # Track latest state across all node updates
                        complete_state = node_state

                status_box.update(
                    label="✅ Research pipeline complete!",
                    state="complete",
                    expanded=False,
                )

            except ValueError as ve:
                # Likely an API key issue
                status_box.update(label="❌ Configuration Error", state="error")
                st.error(f"Configuration error: {str(ve)}")
                st.info(
                    "💡 Check that your OpenRouter key starts with `sk-or-v1-` "
                    "and your selected model is available on your OpenRouter plan."
                )
                st.stop()

            except Exception as e:
                status_box.update(label="❌ Pipeline Error", state="error")
                st.error(f"Pipeline failed at node `{complete_state.get('current_agent', 'unknown') if complete_state else 'startup'}`: {str(e)}")
                st.info(
                    "💡 Common fixes:\n"
                    "- Verify both API keys are valid\n"
                    "- Check your internet connection (Tavily + ArXiv need network)\n"
                    "- Try a different model from the sidebar dropdown\n"
                    "- Check OpenRouter account credits"
                )
                st.exception(e)
                st.stop()

        # ── FINAL COMPLETE STATE (full invoke for complete data) ──────────────
        # Streaming gives incremental chunks per node; .invoke() gives the full
        # accumulated final state. We need both: streaming for UX, invoke for report.
        with st.spinner("📦 Assembling final report..."):
            try:
                pipeline_start = time.time()                    # ← start clock
                complete_state = app.invoke(initial_state)
                pipeline_elapsed = time.time() - pipeline_start # ← stop clock

                st.session_state.pipeline_result  = complete_state
                st.session_state.last_query       = user_query.strip()
                st.session_state.pipeline_elapsed = pipeline_elapsed  # ← persist
            except Exception as e:
                st.error(f"Final assembly failed: {str(e)}")
                st.stop()

    # ── RESULTS DISPLAY ───────────────────────────────────────────────────────
    # Shows either fresh result (just ran) or cached result (from session_state)
    result_state = st.session_state.pipeline_result

    if result_state:
        st.markdown("---")

        # ── TIMING METRICS BAR ───────────────────────────────────────────
        # Visible at the top of results — shows wall-clock time for full pipeline
        elapsed = st.session_state.get("pipeline_elapsed", 0)
        docs    = result_state.get("raw_documents", [])

        # Count docs per tool for the breakdown
        tool_counts = {}
        for d in docs:
            t = d.get("tool_used", "unknown")
            tool_counts[t] = tool_counts.get(t, 0) + 1

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("⏱️ Total Time",    f"{elapsed:.1f}s")
        m2.metric("📄 Doc Chunks",    len(docs))
        m3.metric("🌐 Web Results",   tool_counts.get("tavily_web_search", 0))
        m4.metric("📚 ArXiv Papers",  tool_counts.get("arxiv_search", 0))
        m5.metric("🗃️ Local Chunks",  tool_counts.get("chroma_local", 0))

        st.markdown(f"### 📋 Research Report")
        if st.session_state.last_query:
            st.caption(f"Query: *{st.session_state.last_query}*")

        # ── THREE TABS ────────────────────────────────────────────────────────
        tab_report, tab_docs, tab_routing = st.tabs([
            "📄 Full Report",
            f"🔍 Raw Documents ({len(result_state.get('raw_documents', []))})",
            "🗺️ Routing Details",
        ])

        # TAB 1: FINAL REPORT
        with tab_report:
            final_report = result_state.get("final_report", "")
            if final_report:
                st.markdown('<div class="report-wrap">', unsafe_allow_html=True)
                st.markdown(final_report)
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("")

                dl_col1, dl_col2 = st.columns([2, 1])
                with dl_col1:
                    st.download_button(
                        label="⬇️ Download Report as Markdown",
                        data=final_report,
                        file_name=f"research_{st.session_state.last_query[:35].replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with dl_col2:
                    # Copy-to-clipboard via Streamlit workaround
                    st.download_button(
                        label="📋 Download as .txt",
                        data=final_report,
                        file_name=f"research_{st.session_state.last_query[:35].replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
            else:
                st.error("⚠️ No report was generated. Check pipeline logs above.")

        # TAB 2: RAW RETRIEVED DOCUMENTS
        with tab_docs:
            docs = result_state.get("raw_documents", [])

            if docs:
                # Summary stats across tools
                tool_counts = {}
                for d in docs:
                    t = d.get("tool_used", "unknown")
                    tool_counts[t] = tool_counts.get(t, 0) + 1

                stat_cols = st.columns(len(tool_counts) + 1)
                stat_cols[0].metric("Total Chunks", len(docs))
                for i, (tool, count) in enumerate(tool_counts.items(), 1):
                    tool_label = {
                        "tavily_web_search": "🌐 Web",
                        "arxiv_search":      "📚 ArXiv",
                        "chroma_local":      "🗃️ Local",
                    }.get(tool, tool)
                    stat_cols[i].metric(tool_label, count)

                st.markdown("")

                # Filter by tool
                all_tools = ["All"] + list(tool_counts.keys())
                tool_filter = st.selectbox(
                    "Filter by tool",
                    options=all_tools,
                    format_func=lambda x: {
                        "All": "📦 All Sources",
                        "tavily_web_search": "🌐 Web (Tavily)",
                        "arxiv_search":      "📚 Academic (ArXiv)",
                        "chroma_local":      "🗃️ Local (ChromaDB)",
                    }.get(x, x),
                )

                filtered_docs = docs if tool_filter == "All" else [
                    d for d in docs if d.get("tool_used") == tool_filter
                ]

                for i, doc in enumerate(filtered_docs[:20], 1):  # Cap at 20 for UI perf
                    tool_used = doc.get("tool_used", "unknown")
                    tool_icon = {
                        "tavily_web_search": "🌐",
                        "arxiv_search":      "📚",
                        "chroma_local":      "🗃️",
                    }.get(tool_used, "📄")

                    with st.expander(
                        f"{tool_icon} [{i}] {doc.get('source', 'Unknown Source')[:80]}"
                    ):
                        st.markdown(f"**Tool:** `{tool_used}`")
                        st.markdown(f"**Sub-query:** {doc.get('sub_query', 'N/A')}")
                        st.divider()
                        content = doc.get("content", "")
                        st.markdown(
                            content[:800] + ("..." if len(content) > 800 else "")
                        )

                if len(filtered_docs) > 20:
                    st.caption(f"Showing first 20 of {len(filtered_docs)} chunks.")
            else:
                st.info("No documents were retrieved. Check that your API keys are valid.")

        # TAB 3: ROUTING DETAILS
        with tab_routing:
            routing_plan = result_state.get("routing_plan", [])

            if routing_plan:
                st.markdown(
                    "The **Planner** (triage nurse) made these routing decisions "
                    "BEFORE any retrieval happened. The Retriever then executed "
                    "these exact tool prescriptions, in parallel where multiple tools were assigned."
                )
                st.markdown("")

                for idx, item in enumerate(routing_plan, 1):
                    with st.expander(f"Sub-query {idx}: {item['sub_query']}", expanded=True):
                        tool_col, rationale_col = st.columns([1, 2])

                        with tool_col:
                            st.markdown("**🔧 Tools Assigned:**")
                            for t in item.get("tools", []):
                                icon = {
                                    "tavily_web_search": "🌐",
                                    "arxiv_search":      "📚",
                                    "chroma_local":      "🗃️",
                                }.get(t, "🔧")
                                st.markdown(
                                    f'<span class="route-badge">{icon} {t}</span>',
                                    unsafe_allow_html=True,
                                )

                        with rationale_col:
                            st.markdown("**🧠 Planner's Rationale:**")
                            st.info(item.get("rationale", "No rationale provided."))

                # Show which tools were NOT used (transparency)
                all_possible = {"tavily_web_search", "arxiv_search", "chroma_local"}
                tools_used   = {t for item in routing_plan for t in item.get("tools", [])}
                tools_skipped = all_possible - tools_used

                if tools_skipped:
                    st.markdown("**⏭️ Tools Skipped (not relevant to this query):**")
                    for t in tools_skipped:
                        st.markdown(
                            f'<span class="route-badge" style="opacity:0.4;">❌ {t}</span>',
                            unsafe_allow_html=True,
                        )
                    st.caption(
                        "These tools were intentionally excluded by the Planner because "
                        "they would not return useful results for this query type."
                    )
            else:
                st.info("No routing plan available. Run a research query first.")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE QUERIES — Shown when keys missing OR on fresh load
# ─────────────────────────────────────────────────────────────────────────────
if _show_examples or (not keys_missing and not st.session_state.pipeline_result):
    st.divider()
    st.markdown("### 💡 Example Queries — See Dynamic Routing in Action")
    st.caption(
        "Each query below will route differently through the tool triage system. "
        "Run them to see the Routing Details tab."
    )

    examples = [
        (
            "🏏 Sports / Real-time",
            "tavily_web_search only",
            "What are Virat Kohli's IPL 2024 batting statistics and how do they compare to his 2023 season?",
        ),
        (
            "🕳️ Physics / Academic",
            "arxiv_search + chroma_local",
            "What is the current state of research on Hawking radiation and the black hole information paradox?",
        ),
        (
            "🤖 AI / ML Research",
            "arxiv_search + tavily_web_search + chroma_local",
            "Compare Mamba state space models vs Transformer attention mechanisms for long-context sequence modeling.",
        ),
        (
            "💊 Biotech / Mixed",
            "arxiv_search + tavily_web_search",
            "What are the latest breakthroughs in mRNA vaccine technology beyond COVID-19 and what diseases are being targeted?",
        ),
        (
            "💻 Tech News / Incident",
            "tavily_web_search only",
            "What caused the CrowdStrike global IT outage in July 2024 and what are its cybersecurity implications?",
        ),
        (
            "📊 Economics / Policy",
            "tavily_web_search + arxiv_search",
            "What is the economic impact of generative AI on knowledge worker productivity based on recent studies?",
        ),
    ]

    for i in range(0, len(examples), 2):
        col_a, col_b = st.columns(2)
        for col, example in zip([col_a, col_b], examples[i:i+2]):
            label, routing_hint, query = example
            with col:
                st.markdown(f"**{label}**")
                st.caption(f"Expected routing: `{routing_hint}`")
                st.code(query, language=None)