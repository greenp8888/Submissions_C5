"""Streamlit entry-point – page config and sidebar navigation."""

import streamlit as st

st.set_page_config(
    page_title="DevOps Incident Suite",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("DevOps Incident Suite")
    st.write("v1.0.0 · AI-Powered")

    st.subheader("Navigation")

    nav_items = [
        ("Upload", "Submit a log file for analysis"),
        ("Dashboard", "Browse and inspect incidents"),
        ("Report", "Remediation plan & runbook"),
    ]
    for name, desc in nav_items:
        st.write(f"**{name}**")
        st.write(desc)

    st.write("---")
    st.subheader("API Connection")
    api_url = st.text_input(
        "Base URL",
        value="http://localhost:8000",
        help="FastAPI backend URL",
    )
    st.session_state["api_base_url"] = api_url

    st.write(f"Connected to {api_url}")

# ── Home ──────────────────────────────────────────────────────────────────────
st.title("DevOps Incident Suite")
st.write("AI-powered log analysis · Automated remediation · Instant notifications")

# Feature cards row
cols = st.columns(3)
features = [
    ("Intelligent Triage", "Claude Sonnet 4.5 classifies every incident at every severity level — CRITICAL, HIGH, MEDIUM and LOW — from a single log file."),
    ("Automated Remediation", "Ordered, executable fix steps with kubectl, SQL and bash commands generated per incident. Downloadable Markdown runbook included."),
    ("Instant Notifications", "Slack Block Kit alert fires for MEDIUM+ incidents. JIRA ticket auto-created for CRITICAL."),
]
for col, (title, body) in zip(cols, features):
    with col:
        st.subheader(title)
        st.write(body)

st.write("---")

# Pipeline steps
st.subheader("Agent Pipeline")

steps = [
    ("01", "Log Classifier", "Severity, root cause, all sub-incidents"),
    ("02", "Remediation Agent", "Ordered fix steps with commands"),
    ("03", "Cookbook Synthesizer", "Markdown runbook generation"),
    ("04", "Notification Agent", "Slack alert (MEDIUM+)"),
    ("05", "JIRA Agent", "Ticket creation (CRITICAL only)"),
]
for num, name, desc in steps:
    st.write(f"**{num}** {name}: {desc}")

st.write("---")
st.write("Use the sidebar to navigate. Start on Upload to submit a log file, then monitor progress on Dashboard, and view the full remediation plan on Report.")

