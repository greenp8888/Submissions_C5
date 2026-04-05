import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Load .env from the same directory as this script
load_dotenv(Path(__file__).resolve().parent / ".env")

# Map OpenRouter credentials to OpenAI env vars before any LLM imports
_key = os.environ.get("OPENROUTER_API_KEY", "")
if not _key:
    st.error("OPENROUTER_API_KEY not found in .env file. Please add your API key.")
    st.stop()
os.environ["OPENAI_API_KEY"] = _key
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

from orchestrator.graph import build_graph
from orchestrator.state import make_initial_state
from utils.log_parser import read_uploaded_file
from ui.components import inject_theme, severity_summary, category_tags, trace_bar
from ui.tabs import (
    render_analysis_tab,
    render_remediations_tab,
    render_cookbook_tab,
    render_slack_tab,
    render_jira_tab,
    render_trace_tab,
)

st.set_page_config(
    page_title="DevOps Incident Analyzer",
    page_icon="\U0001f6e1\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

# Initialize session state
if "analysis_state" not in st.session_state:
    st.session_state.analysis_state = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False

# --- Sidebar ---
with st.sidebar:
    st.markdown("### \U0001f6e1\ufe0f Incident Analyzer")
    st.markdown('<span style="color:#8b949e; font-size:12px;">Multi-Agent DevOps Suite</span>', unsafe_allow_html=True)
    st.divider()

    # Log input section
    st.markdown("**Log Input**")
    uploaded_file = st.file_uploader(
        "Upload log file",
        type=["log", "txt", "json", "csv"],
        help="Supports .log, .txt, .json, .csv formats",
    )

    pasted_logs = st.text_area(
        "Or paste logs here",
        height=150,
        placeholder="Paste log content...",
    )

    analyze_button = st.button(
        "\u25b6\ufe0f Analyze Logs",
        use_container_width=True,
        disabled=st.session_state.is_running,
    )

    # Severity summary (after analysis)
    if st.session_state.analysis_state:
        st.divider()
        st.markdown("**Severity Breakdown**")
        severity_summary(st.session_state.analysis_state.get("classified_entries", []))

        st.divider()
        st.markdown("**Issue Categories**")
        category_tags(st.session_state.analysis_state.get("classified_entries", []))

# --- Main Content ---
st.markdown(
    '<h1 style="color:#58a6ff; margin-bottom:0;">\U0001f6e1\ufe0f DevOps Incident Analyzer</h1>'
    '<p style="color:#8b949e;">Multi-Agent Analysis Suite</p>',
    unsafe_allow_html=True,
)

# Handle analysis
if analyze_button:
    raw_logs = ""
    if uploaded_file is not None:
        raw_logs = read_uploaded_file(uploaded_file)
    elif pasted_logs.strip():
        raw_logs = pasted_logs.strip()

    if not raw_logs:
        st.error("Please upload a file or paste log content.")
    else:
        st.session_state.is_running = True
        with st.spinner("Analyzing logs with multi-agent pipeline..."):
            graph = build_graph()
            initial_state = make_initial_state(raw_logs)
            result = graph.invoke(initial_state)
            st.session_state.analysis_state = result
        st.session_state.is_running = False
        st.rerun()

# Display results
if st.session_state.analysis_state:
    # Agent trace bar at top
    st.markdown("---")
    st.markdown("**Agent Execution Trace**")
    trace_bar(st.session_state.analysis_state.get("agent_trace", []))
    st.markdown("---")

    # Tabs
    tab_analysis, tab_remediations, tab_cookbook, tab_slack, tab_jira, tab_trace = st.tabs(
        [
            "\U0001f50d Analysis",
            "\U0001f527 Remediations",
            "\U0001f4d6 Cookbook",
            "\U0001f4ac Slack Log",
            "\U0001f3ab JIRA Tickets",
            "\U0001f500 Agent Trace",
        ]
    )

    with tab_analysis:
        render_analysis_tab(st.session_state.analysis_state)
    with tab_remediations:
        render_remediations_tab(st.session_state.analysis_state)
    with tab_cookbook:
        render_cookbook_tab(st.session_state.analysis_state)
    with tab_slack:
        render_slack_tab(st.session_state.analysis_state)
    with tab_jira:
        render_jira_tab(st.session_state.analysis_state)
    with tab_trace:
        render_trace_tab(st.session_state.analysis_state)
else:
    st.markdown(
        """<div style="display:flex; align-items:center; justify-content:center; min-height:400px;">
            <div style="text-align:center;">
                <p style="font-size:48px; margin-bottom:8px;">\U0001f4cb</p>
                <h3 style="color:#c9d1d9;">Upload or paste ops logs to get started</h3>
                <p style="color:#8b949e;">The multi-agent pipeline will classify issues, generate remediations, and push notifications.</p>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
