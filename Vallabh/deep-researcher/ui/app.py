"""
=============================================================================
Streamlit UI — Deep Research Dashboard
=============================================================================
Interactive interface for multi-agent research.
Features: query input, depth selection, real-time progress,
tabbed results, report export.
=============================================================================
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import run_pipeline

logging.basicConfig(level=logging.INFO)

# ── Page Config ──
st.set_page_config(
    page_title="AI Deep Researcher",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──
st.markdown("""
<style>
.confidence-high { color: #27ae60; font-weight: bold; }
.confidence-medium { color: #f39c12; font-weight: bold; }
.confidence-low { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.title("🔬 AI Deep Researcher")
    st.markdown("Multi-Agent Research Assistant")
    st.divider()

    st.subheader("🔧 Pipeline Agents")
    agents = {
        "1. Query Planner": "Decomposes query into sub-questions",
        "2. Retriever": "ArXiv + Wikipedia + Web search",
        "3. Analyzer": "Critical analysis & gap detection",
        "4. Gap Filler": "Targeted retrieval for gaps",
        "5. Fact Checker": "Cross-validates key claims",
        "6. Insight Generator": "Trends, hypotheses, reasoning",
        "7. Report Builder": "Structured report with citations",
    }
    for name, desc in agents.items():
        st.markdown(f"**{name}**")
        st.caption(desc)

    st.divider()
    st.caption("Built with LangGraph + LangChain + Tavily")

# ── Main Content ──
st.title("🔍 Deep Research Dashboard")

# ── Input ──
col_q, col_d = st.columns([4, 1])
with col_q:
    query = st.text_area(
        "Research Question",
        height=80,
        placeholder="e.g., What are the latest advances in quantum error correction and how close are we to fault-tolerant quantum computing?",
    )
with col_d:
    depth = st.selectbox("Depth", ["quick", "standard", "deep"], index=1)
    st.caption({
        "quick": "3-4 sub-questions, fast",
        "standard": "4-6 sub-questions, balanced",
        "deep": "5-7 sub-questions, thorough",
    }[depth])

# ── Sample Queries ──
with st.expander("💡 Sample Research Queries"):
    samples = [
        "What are the latest advances in quantum error correction and how close are we to fault-tolerant quantum computing?",
        "How is CRISPR gene editing being used in agriculture, and what are the regulatory and ethical implications?",
        "What is the current state of nuclear fusion energy research? Compare tokamak, stellarator, and laser inertial approaches.",
        "How are large language models being used in drug discovery and what are the limitations?",
        "What are the economic and environmental impacts of deep-sea mining for battery minerals?",
    ]
    for s in samples:
        if st.button(s[:80] + "...", key=f"sample_{hash(s)}"):
            st.session_state["prefill_query"] = s
            st.rerun()

if "prefill_query" in st.session_state:
    query = st.session_state.pop("prefill_query")

# ── Run Pipeline ──
if query and query.strip():
    if st.button("🚀 Start Research", type="primary", use_container_width=True):
        with st.spinner("Running multi-agent research pipeline..."):
            progress = st.progress(0, "📋 Planning research...")

            try:
                progress.progress(10, "📋 Decomposing query...")
                final_state = run_pipeline(query=query, depth=depth)
                progress.progress(100, "✅ Research complete!")
                st.session_state["results"] = final_state

            except Exception as e:
                st.error(f"❌ Pipeline failed: {str(e)}")

# ── Results Dashboard ──
if "results" in st.session_state:
    state = st.session_state["results"]
    st.divider()

    # ── Metrics ──
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📚 Sources", len(state.get("sources", [])))
    with col2:
        st.metric("✅ Fact Checks", len(state.get("fact_checks", [])))
    with col3:
        reliability = state.get("overall_reliability", 0)
        st.metric("🎯 Reliability", f"{reliability:.0%}")
    with col4:
        st.metric("📈 Trends", len(state.get("trends", [])))
    with col5:
        st.metric("💡 Hypotheses", len(state.get("hypotheses", [])))

    # ── Tabs ──
    tab_report, tab_sources, tab_analysis, tab_facts, tab_insights, tab_raw = st.tabs([
        "📝 Report", "📚 Sources", "🔬 Analysis",
        "✅ Fact Checks", "💡 Insights", "📄 Raw State"
    ])

    # ── Report Tab ──
    with tab_report:
        report_md = state.get("report_markdown", "")
        if report_md:
            st.markdown(report_md)
            st.download_button(
                "📥 Download Report (Markdown)",
                data=report_md,
                file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )
        else:
            st.warning("Report not generated.")

    # ── Sources Tab ──
    with tab_sources:
        st.subheader(f"Retrieved Sources ({len(state.get('sources', []))})")
        st.info(state.get("retrieval_summary", ""))

        for s in state.get("sources", []):
            emoji = {"ARXIV": "📄", "WIKIPEDIA": "📖", "WEB": "🌐", "NEWS": "📰"}.get(s.get("source_type", ""), "📎")
            with st.expander(f"{emoji} [{s.get('id', '?')}] {s.get('title', 'Untitled')}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Type:** {s.get('source_type', 'N/A')}")
                    st.markdown(f"**Authors:** {s.get('authors', 'N/A')}")
                with c2:
                    st.markdown(f"**Published:** {s.get('published_date', 'N/A')}")
                    st.markdown(f"**Relevance:** {s.get('relevance_score', 0):.0%}")
                if s.get("url"):
                    st.markdown(f"🔗 [{s['url']}]({s['url']})")
                st.text(s.get("content", "No content")[:500])

    # ── Analysis Tab ──
    with tab_analysis:
        st.subheader("Critical Analysis")
        st.info(state.get("analysis_assessment", "No assessment"))

        if state.get("consensus_findings"):
            st.markdown("**Consensus Findings:**")
            for c in state["consensus_findings"]:
                st.markdown(f"✅ {c}")

        if state.get("contradictions"):
            st.markdown("**Contradictions:**")
            for c in state["contradictions"]:
                with st.expander(f"⚠️ {c.get('claim', 'Unknown')}"):
                    st.markdown(f"**{c.get('source_a_id', '?')}:** {c.get('source_a_position', 'N/A')}")
                    st.markdown(f"**{c.get('source_b_id', '?')}:** {c.get('source_b_position', 'N/A')}")
                    if c.get("resolution"):
                        st.markdown(f"**Resolution:** {c['resolution']}")

        if state.get("information_gaps"):
            st.markdown("**Information Gaps:**")
            for g in state["information_gaps"]:
                st.warning(f"🕳️ {g.get('description', '?')} — *{g.get('importance', '')}*")

    # ── Fact Checks Tab ──
    with tab_facts:
        st.subheader("Fact Verification")
        st.info(state.get("reliability_summary", ""))

        for fc in state.get("fact_checks", []):
            status = fc.get("status", "UNKNOWN")
            emoji = {"VERIFIED": "✅", "PARTIALLY_VERIFIED": "🟡", "UNVERIFIED": "❓", "CONTRADICTED": "❌"}.get(status, "❓")
            conf = fc.get("confidence", 0)

            with st.expander(f"{emoji} [{status}] {fc.get('claim', '?')[:80]} ({conf:.0%})"):
                st.progress(conf)
                if fc.get("supporting_sources"):
                    st.markdown(f"**Supporting:** {', '.join(fc['supporting_sources'])}")
                if fc.get("contradicting_sources"):
                    st.markdown(f"**Contradicting:** {', '.join(fc['contradicting_sources'])}")
                if fc.get("notes"):
                    st.caption(fc["notes"])

    # ── Insights Tab ──
    with tab_insights:
        st.subheader("Generated Insights")

        if state.get("key_takeaways"):
            st.markdown("**Key Takeaways:**")
            for t in state["key_takeaways"]:
                st.success(f"💡 {t}")

        if state.get("synthesis_narrative"):
            st.markdown("**Synthesis:**")
            st.markdown(state["synthesis_narrative"])

        if state.get("trends"):
            st.markdown("**Trends:**")
            for t in state["trends"]:
                with st.expander(f"📈 {t.get('title', '?')} ({t.get('confidence', '?')})"):
                    st.markdown(t.get("description", ""))
                    st.markdown(f"**Evidence:** {', '.join(t.get('evidence', []))}")

        if state.get("hypotheses"):
            st.markdown("**Hypotheses:**")
            for h in state["hypotheses"]:
                with st.expander(f"🧪 {h.get('statement', '?')[:80]}"):
                    st.markdown("**Reasoning Chain:**")
                    for i, step in enumerate(h.get("reasoning_chain", []), 1):
                        st.markdown(f"{i}. {step}")
                    st.markdown(f"**Testability:** {h.get('testability', 'N/A')}")
                    st.markdown(f"**Novelty:** {h.get('novelty', 'N/A')}")

        if state.get("future_directions"):
            st.markdown("**Future Research Directions:**")
            for d in state["future_directions"]:
                st.markdown(f"🔮 {d}")

    # ── Raw State Tab ──
    with tab_raw:
        st.subheader("Raw Pipeline State")
        st.json(state)

    # ── Errors ──
    errors = state.get("error_trace", [])
    if errors:
        st.divider()
        st.error(f"⚠️ {len(errors)} error(s):")
        for err in errors:
            st.code(err)
